"""Query normalization utilities for the Thor chat pipeline.

This module is intentionally thorough and verbose to capture a wide range of
user input patterns. The goal is to give downstream intent routing and
knowledge retrieval a consistent, low-noise query representation without
changing the user's meaning. The normalizer is conservative: it avoids
aggressive rewriting that could remove intent, but it provides hooks for:

- Alias expansion (common chat shorthands → canonical phrases)
- Unicode and punctuation cleanup
- URL, handle, and code fence stripping for cleaner semantic matching
- Keyword extraction for fast filters
- Entity extraction (simple capitalized phrases + heuristic fallbacks)
- Pronoun and follow-up detection signals
- Language and slang detection flags
- Lightweight sentence segmentation for multi-question handling

The code favors readability and debuggability over brevity. Each stage is
broken out so it can be inspected or adapted independently.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import re
import unicodedata


def _squash_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_surrounding(text: str, chars: str = " ?!.;,") -> str:
    return text.strip(chars)


def _strip_urls(text: str) -> Tuple[str, List[str]]:
    urls = re.findall(r"https?://\S+|www\.\S+", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text, flags=re.IGNORECASE)
    return cleaned, urls


def _strip_handles(text: str) -> Tuple[str, List[str]]:
    handles = re.findall(r"@[A-Za-z0-9_]+", text)
    cleaned = re.sub(r"@[A-Za-z0-9_]+", "", text)
    return cleaned, handles


def _strip_code_fences(text: str) -> Tuple[str, List[str]]:
    fences = re.findall(r"```.*?```", text, flags=re.DOTALL)
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return cleaned, fences


def _normalize_unicode(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\u2019", "'").replace("\u2018", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
    normalized = normalized.replace("\u00a0", " ")
    return normalized


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    # Simple splitter that respects question marks and exclamation points.
    parts = re.split(r"(?<=[\.\?!])\s+", text)
    return [p.strip() for p in parts if p and len(p.strip()) > 0]


def _extract_entities(original: str) -> List[str]:
    """Extract capitalized entities; favor multi-word sequences."""
    entities = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", original)
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for ent in entities:
        if ent not in seen:
            ordered.append(ent)
            seen.add(ent)
    return ordered


def _extract_keywords(normalized: str, stopwords: set, limit: int = 12) -> List[str]:
    words = normalized.split()
    keywords = []
    for w in words:
        if w in stopwords:
            continue
        if len(w) <= 2:
            continue
        keywords.append(w)
        if len(keywords) >= limit:
            break
    return keywords


def _detect_language_flags(text: str) -> Dict[str, bool]:
    """Very lightweight heuristic language/slang flags."""
    lower = text.lower()
    flags = {
        "possible_hinglish": any(word in lower for word in ["hai", "nahi", "kya", "acha", "accha"]),
        "possible_spanish": any(word in lower for word in ["que", "como", "porque", "gracias", "hola"]),
        "possible_french": any(word in lower for word in ["bonjour", "merci", "pourquoi", "comment"]),
        "possible_code_snippet": "def " in lower or "function " in lower or "class " in lower or "console.log" in lower,
    }
    return flags


def _detect_follow_up_signals(text: str) -> Dict[str, bool]:
    lower = text.lower().strip()
    short = len(lower.split()) <= 8
    contains_pronouns = any(p in lower.split() for p in ["it", "that", "this", "they", "them", "those"])
    continues = any(lower.startswith(prefix) for prefix in ["and ", "also ", "then ", "so ", "but "])
    ellipsis = "..." in lower
    return {
        "is_short": short,
        "has_pronoun_reference": contains_pronouns,
        "starts_like_continuation": continues,
        "has_ellipsis": ellipsis,
    }


def _punctuation_cleanup(text: str) -> str:
    cleaned = re.sub(r"[“”]", '"', text)
    cleaned = re.sub(r"[‘’]", "'", cleaned)
    cleaned = re.sub(r"[‐‑‒–—―]", "-", cleaned)
    cleaned = re.sub(r"\s*[,;:]\s*", lambda m: m.group(0).strip() + " ", cleaned)
    cleaned = re.sub(r"\s+[!?]", lambda m: m.group(0).strip(), cleaned)
    return cleaned


def _alias_expand(text: str, alias_map: Dict[str, str]) -> str:
    lowered = text
    for alias, full in alias_map.items():
        lowered = re.sub(rf"\b{alias}\b", full, lowered, flags=re.IGNORECASE)
    return lowered


def _strip_fillers(text: str, fillers: List[str]) -> str:
    cleaned = text
    for filler in fillers:
        cleaned = re.sub(rf"\b{filler}\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = _squash_whitespace(cleaned)
    return cleaned


def _extract_time_and_numbers(text: str) -> Dict[str, List[str]]:
    times = re.findall(r"\b\d{1,2}:\d{2}(?:\s*[ap]m)?\b", text, flags=re.IGNORECASE)
    years = re.findall(r"\b(19|20)\d{2}\b", text)
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    return {"times": times, "years": years, "numbers": numbers}


def _normalize_quotes(text: str) -> str:
    return text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")


def _remove_repeated_punctuation(text: str) -> str:
    return re.sub(r"([!?\.])\1{1,}", r"\1", text)


class QuestionNormalizer:
    """Extensive normalizer to make queries easier to route and match."""

    def __init__(self):
        # Common expansions for shorthand
        self.alias_map = {
            "whats": "what is",
            "what's": "what is",
            "who's": "who is",
            "wanna": "want to",
            "gonna": "going to",
            "lemme": "let me",
            "gimme": "give me",
            "kinda": "kind of",
            "sorta": "sort of",
            "dont": "do not",
            "can't": "cannot",
            "cant": "cannot",
            "wont": "will not",
            "won't": "will not",
        }

        # Stopwords that frequently add noise when matching
        self.stopwords = {
            "please",
            "kindly",
            "hey",
            "hi",
            "hello",
            "can",
            "could",
            "would",
            "you",
            "me",
            "tell",
            "about",
            "the",
            "a",
            "an",
            "of",
            "for",
            "to",
            "in",
            "on",
            "with",
            "and",
            "or",
            "is",
            "are",
            "was",
            "were",
        }

        self.filler_words = [
            "please",
            "kindly",
            "just",
            "actually",
            "literally",
            "basically",
            "like",
            "uh",
            "um",
            "hmm",
        ]

    def _base_cleanup(self, text: str) -> Dict:
        normalized = _normalize_unicode(text)
        normalized = _normalize_quotes(normalized)
        normalized = _punctuation_cleanup(normalized)
        normalized = _remove_repeated_punctuation(normalized)
        normalized, urls = _strip_urls(normalized)
        normalized, handles = _strip_handles(normalized)
        normalized, fences = _strip_code_fences(normalized)
        normalized = _alias_expand(normalized, self.alias_map)
        normalized = _strip_fillers(normalized, self.filler_words)
        normalized = _squash_whitespace(normalized)
        normalized = _strip_surrounding(normalized)
        return {
            "text": normalized,
            "urls": urls,
            "handles": handles,
            "code_fences": fences,
        }

    def _analyze_sentences(self, text: str) -> List[Dict]:
        sentences = _split_sentences(text)
        analyzed = []
        for sent in sentences:
            flags = _detect_follow_up_signals(sent)
            analyzed.append({"text": sent, "signals": flags})
        return analyzed

    def _aggregate_follow_up(self, sentence_info: List[Dict]) -> bool:
        for entry in sentence_info:
            signals = entry.get("signals", {})
            if signals.get("starts_like_continuation") or signals.get("has_pronoun_reference"):
                return True
        return False

    def normalize(self, text: str, conversation_context: Optional[List[Dict]] = None) -> Dict:
        """Return a normalized query plus lightweight entity extraction."""
        original = text or ""
        base = self._base_cleanup(original)
        lowered = base["text"].lower().strip()

        # Trim extra punctuation and spaces
        lowered = _squash_whitespace(lowered)
        lowered = _strip_surrounding(lowered)

        # Pull simple entities (capitalized tokens in original text)
        entities = _extract_entities(original)

        # Derive lightweight keywords (non-stopwords, >2 chars)
        keywords = _extract_keywords(lowered, self.stopwords, limit=12)

        # Sentence-level follow-up hints
        sentence_info = self._analyze_sentences(original)
        follow_up_from_sentences = self._aggregate_follow_up(sentence_info)

        # Context-based follow-up hint
        context_follow_up = bool(conversation_context and len(conversation_context) >= 2)
        follow_up = follow_up_from_sentences or context_follow_up

        # Additional metadata
        language_flags = _detect_language_flags(original)
        numbers = _extract_time_and_numbers(original)

        return {
            "original": original,
            "normalized_query": lowered or original,
            "entities": entities,
            "keywords": keywords,
            "urls_removed": base["urls"],
            "handles_removed": base["handles"],
            "code_blocks_removed": base["code_fences"],
            "sentences": sentence_info,
            "is_follow_up_like": follow_up,
            "language_flags": language_flags,
            "numbers": numbers,
        }


_question_normalizer: QuestionNormalizer = None


def get_question_normalizer() -> QuestionNormalizer:
    """Singleton accessor."""
    global _question_normalizer
    if _question_normalizer is None:
        _question_normalizer = QuestionNormalizer()
    return _question_normalizer


# -----------------------------
# Extended helper utilities
# -----------------------------

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    return EMOJI_PATTERN.sub("", text)


def detect_questions(text: str) -> List[str]:
    """Return individual questions detected in text."""
    parts = re.split(r"\?\s*", text)
    questions = []
    for p in parts:
        cleaned = p.strip()
        if cleaned:
            questions.append(cleaned)
    return questions


def tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"\W+", text) if t]


def guess_domain(keywords: List[str]) -> str:
    domains = {
        "cloud": {"aws", "gcp", "azure", "cloud", "bucket", "lambda"},
        "data": {"sql", "database", "query", "spark", "pandas"},
        "web": {"http", "browser", "react", "vue", "next", "dom"},
        "mobile": {"android", "ios", "swift", "kotlin"},
        "ml": {"model", "training", "inference", "torch", "tensorflow"},
    }
    lower = {k.lower() for k in keywords}
    for domain, keys in domains.items():
        if lower & keys:
            return domain
    return "general"


def score_noise(text: str) -> float:
    """Heuristic noise score; higher is noisier."""
    if not text:
        return 1.0
    tokens = tokenize(text)
    if not tokens:
        return 0.8
    uppercase_ratio = sum(1 for t in tokens if t.isupper()) / len(tokens)
    digit_ratio = sum(1 for t in tokens if t.isdigit()) / len(tokens)
    emoji_count = len(EMOJI_PATTERN.findall(text))
    return min(1.0, 0.3 * uppercase_ratio + 0.3 * digit_ratio + 0.1 * emoji_count)


def summarize_normalization(result: Dict) -> str:
    parts = [
        f"normalized='{result.get('normalized_query')}'",
        f"keywords={result.get('keywords')}",
        f"entities={result.get('entities')}",
        f"follow_up_like={result.get('is_follow_up_like')}",
    ]
    return " | ".join(parts)


def merge_with_context(normalized: Dict, context: List[Dict]) -> Dict:
    """Attach last user message for downstream context-aware steps."""
    if context:
        last_user = next((m for m in reversed(context) if m.get("role") == "user"), None)
    else:
        last_user = None
    normalized = dict(normalized)
    normalized["last_user_message"] = last_user.get("content") if last_user else None
    return normalized


def build_debug_record(text: str, context: Optional[List[Dict]] = None) -> Dict:
    normalizer = get_question_normalizer()
    result = normalizer.normalize(text, context)
    result["noise_score"] = score_noise(text)
    result["debug_summary"] = summarize_normalization(result)
    return result


def lower_only(text: str) -> str:
    return (text or "").lower()


def contains_url(text: str) -> bool:
    return bool(re.search(r"https?://\S+|www\.\S+", text or "", flags=re.IGNORECASE))


def ensure_ascii(text: str) -> str:
    return text.encode("ascii", errors="ignore").decode("ascii")


def clean_for_matching(text: str) -> str:
    text = strip_emojis(text)
    text = ensure_ascii(text)
    text = _normalize_unicode(text)
    text = _alias_expand(text, {})
    text = _squash_whitespace(text)
    return text


# Extended reference patterns for maintainers (not actively used, kept for future heuristics).
REFERENCE_PATTERNS = [
    r"\bwho\s+is\s+[A-Z][a-z]+",
    r"\bwhat\s+is\s+[a-z]{3,}",
    r"\bhow\s+to\s+\w+",
    r"\bdifference\s+between\s+\w+\s+and\s+\w+",
    r"\berror\s+code\s+\d+",
    r"\bwhy\s+does\s+\w+",
    r"\bwhere\s+is\s+\w+",
    r"\bwhen\s+does\s+\w+",
]


def list_reference_patterns() -> List[str]:
    return list(REFERENCE_PATTERNS)


def contains_reference_pattern(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in REFERENCE_PATTERNS)


def debug_patterns(text: str) -> List[str]:
    matched = []
    for pat in REFERENCE_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            matched.append(pat)
    return matched


NORMALIZER_RULES = [
    "Never drop intent words even if they look like stopwords in context.",
    "Preserve user casing for entity extraction; use lower for matching.",
    "Do not rewrite slang unless alias map explicitly covers it.",
    "Avoid stripping numbers; they may be important (versions, quantities).",
    "Trim excessive punctuation but keep single question marks.",
    "Handle emojis by stripping for matching but keep original safe copy if needed.",
    "Stopword list should stay small to avoid removing meaning.",
    "Sentence splitting must not break URLs or code fences.",
    "Normalization must be idempotent for repeat calls.",
    "ASCII cleaning should not discard meaningful content; prefer replacement.",
]


def normalizer_rules_text() -> str:
    return "\n".join(f"- {r}" for r in NORMALIZER_RULES)

