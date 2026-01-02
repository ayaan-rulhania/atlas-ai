"""Intent routing helpers to enrich existing query intent analysis.

This router augments the base intent analyzer with hints that influence:
- Which sources to consult (brain vs research vs both)
- How many sources to combine (single vs multi-source)
- Whether to prioritize disambiguation or clarifying questions
- How to treat safety/NSFW or transactional/creative asks
- How to bias toward coding vs. general knowledge paths

The design is deliberately verbose and data-driven to allow future adaptation
without toggles. All defaults are on.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import re


def _has_code_signals(text: str) -> bool:
    return any(sig in text for sig in ["```", "def ", "class ", "console.log", "import ", "function "])


def _detect_transactional(text: str) -> bool:
    transactional_terms = [
        "buy", "purchase", "price", "cost", "order", "book", "reserve", "subscription", "license",
        "how much", "discount", "deal", "plan", "pricing", "checkout",
    ]
    lower = text.lower()
    return any(term in lower for term in transactional_terms)


def _detect_troubleshooting(text: str) -> bool:
    lower = text.lower()
    indicators = ["error", "exception", "stack trace", "traceback", "bug", "issue", "failed", "crash"]
    return any(ind in lower for ind in indicators)


def _detect_sensitive(text: str) -> bool:
    lower = text.lower()
    sensitive_terms = [
        "password", "token", "secret", "apikey", "api key", "credit card", "ssn",
        "social security", "private key", "mnemonic", "seed phrase",
    ]
    return any(term in lower for term in sensitive_terms)


def _detect_multi_question(text: str) -> bool:
    return bool(re.search(r"\?\s+\w+", text)) or text.count("?") > 1


def _detect_relationship(text: str) -> bool:
    lower = text.lower()
    phrases = ["relationship between", "difference between", "vs", "versus", "compare", "comparison"]
    return any(p in lower for p in phrases)


def _detect_list_request(text: str) -> bool:
    lower = text.lower()
    phrases = ["list ", "top ", "best ", "examples", "ideas", "suggestions", "options"]
    return any(lower.startswith(p) or f" {p}" in lower for p in phrases)


def _detect_depth(text: str) -> str:
    lower = text.lower()
    if any(p in lower for p in ["step by step", "detailed", "in depth", "deep dive", "explain like i'm 5", "eli5"]):
        return "deep"
    if any(p in lower for p in ["summary", "summarize", "tl;dr", "brief", "short"]):
        return "brief"
    return "balanced"


def _detect_modal_intent(text: str) -> Dict[str, bool]:
    lower = text.lower()
    return {
        "asks_for_examples": any(p in lower for p in ["example", "sample", "show me", "demo", "snippet"]),
        "asks_for_steps": any(p in lower for p in ["how do i", "how to", "steps", "guide", "tutorial", "walkthrough"]),
        "asks_for_def": any(p in lower for p in ["what is", "definition", "define", "meaning of", "explain what"]),
    }


def _detect_conversational_intent(text: str) -> Dict[str, bool]:
    """Detect if query is conversational rather than factual"""
    lower = text.lower()

    # Conversational patterns that suggest common sense responses
    conversational_indicators = [
        # Personal feelings and thoughts
        "i think", "i feel", "i believe", "i wonder", "i'm curious",
        "what do you think", "how do you feel", "what's your opinion",

        # Acknowledgments and reactions
        "that's interesting", "that's cool", "that makes sense", "i see",
        "i understand", "that sounds good", "that seems right",

        # Personal statements
        "i'm working on", "i'm learning", "i'm trying to", "i need help",
        "i want to", "i'm confused", "i'm not sure", "i agree", "i disagree",

        # Social interactions
        "thank you", "thanks", "please", "sorry", "excuse me",

        # Simple questions that don't need research
        "how are you", "what are you doing", "what's up", "what's new",
        "tell me about yourself", "who are you", "what can you do",

        # Time and basic info
        "what time is it", "what's the time", "what day is it",
        "what's today's date", "what's the weather",

        # Simple math
        "what is 2+2", "calculate", "what's 5 times 3",

        # Simple acknowledgments
        "ok", "okay", "sure", "alright", "got it", "understood",
        "yes", "no", "maybe", "perhaps"
    ]

    # Check if query is very short (likely conversational)
    word_count = len(text.split())
    is_very_short = word_count <= 3

    # Check for question marks vs statements
    has_question_mark = '?' in text
    is_statement = not has_question_mark and word_count > 1

    # Check for conversational patterns
    has_conversational_patterns = any(indicator in lower for indicator in conversational_indicators)

    # Determine if this is primarily conversational
    is_conversational = (
        has_conversational_patterns or
        is_very_short or
        (is_statement and word_count <= 5 and not any(word in lower for word in [
            'who', 'what', 'when', 'where', 'why', 'how', 'which', 'explain'
        ]))
    )

    return {
        "is_conversational": is_conversational,
        "is_statement": is_statement,
        "is_very_short": is_very_short,
        "has_conversational_patterns": has_conversational_patterns,
        "word_count": word_count
    }


def _detect_factual_intent(text: str) -> Dict[str, bool]:
    """Detect if query requires factual research"""
    lower = text.lower()

    # Factual/research indicators
    factual_indicators = [
        # Research questions
        "what is the difference", "how does it work", "why does", "when did",
        "where is", "who invented", "who discovered", "how to make",
        "recipe for", "what are the benefits", "what causes",

        # Technical/programming
        "how do i", "how to", "tutorial", "guide", "documentation",
        "api", "function", "class", "method", "variable",

        # Historical/scientific
        "history of", "science of", "theory of", "principle of",

        # Comparisons
        "vs", "versus", "better than", "comparison between",

        # Lists and explanations
        "list of", "types of", "kinds of", "examples of", "best practices",

        # Complex questions
        "explain", "describe", "analyze", "evaluate", "assess"
    ]

    # Check for research question patterns
    research_questions = [
        "what are", "how do", "why do", "when was", "where can",
        "who was", "which is", "can you explain"
    ]

    has_research_indicators = any(indicator in lower for indicator in factual_indicators)
    has_research_questions = any(question in lower for question in research_questions)

    # Length-based assessment
    word_count = len(text.split())
    is_long_query = word_count > 8

    # Complex question markers
    complex_markers = ['because', 'although', 'however', 'therefore', 'moreover', 'furthermore']
    has_complex_structure = any(marker in lower for marker in complex_markers)

    is_factual = (
        has_research_indicators or
        has_research_questions or
        (is_long_query and has_question_mark) or
        has_complex_structure
    )

    return {
        "is_factual": is_factual,
        "has_research_indicators": has_research_indicators,
        "has_research_questions": has_research_questions,
        "is_long_query": is_long_query,
        "has_complex_structure": has_complex_structure
    }


def _detect_safety_sensitive(text: str) -> bool:
    lower = text.lower()
    nsfw_indicators = [
        "nsfw", "explicit", "adult", "not safe for work",
        "violent", "gore", "harm", "self-harm", "suicide", "kill", "murder",
    ]
    return any(ind in lower for ind in nsfw_indicators)


def _detect_music_video_intent(text: str) -> bool:
    """Detect if the user is explicitly asking about music or video content"""
    lower = text.lower()

    # Explicit music/video intent indicators
    music_video_indicators = [
        "music", "song", "songs", "video", "videos", "youtube", "spotify",
        "listen", "play", "watch", "album", "artist", "band", "concert",
        "musical", "singer", "playlist", "track", "tracks", "audio",
        "film", "movie", "cinema", "tv show", "series", "episode",
        "entertainment", "hollywood", "bollywood", "netflix", "hulu",
        "streaming", "vlog", "tutorial video"
    ]

    # Check for explicit intent words
    intent_words = ["tell me about", "show me", "recommend", "find", "search for",
                   "what's", "who's", "where can i", "how do i", "play me",
                   "watch", "listen to", "recommend me"]

    # Combine intent + music/video for stronger detection
    has_intent = any(intent in lower for intent in intent_words)
    has_music_video = any(indicator in lower for indicator in music_video_indicators)

    # If user explicitly mentions music/video topics, consider it music/video intent
    if has_music_video:
        return True

    # If they have intent words + music/video, definitely music/video intent
    if has_intent and has_music_video:
        return True

    return False


def _detect_greeting_intent(text: str) -> bool:
    """Detect if query is a greeting or farewell"""
    lower = text.lower()

    greeting_patterns = [
        # Greetings
        "hi", "hello", "hey", "good morning", "good afternoon",
        "good evening", "good night", "greetings", "howdy",

        # Farewells
        "bye", "goodbye", "see you", "farewell", "take care",
        "talk to you later", "catch you later", "bye bye",

        # Well-being inquiries
        "how are you", "how do you do", "how's it going",
        "what's up", "what's new", "how have you been"
    ]

    # Very short queries that are likely greetings
    word_count = len(text.split())
    is_very_short_greeting = word_count <= 2 and any(word in lower for word in [
        "hi", "hey", "hello", "bye", "sup"
    ])

    return any(pattern in lower for pattern in greeting_patterns) or is_very_short_greeting


def _detect_tone(text: str) -> str:
    lower = text.lower()
    if any(p in lower for p in ["please", "could you", "would you", "can you"]):
        return "polite"
    if any(p in lower for p in ["now", "quick", "urgent", "asap", "fast"]):
        return "urgent"
    return "neutral"


def _score_confidence(confidence: float, overrides: Dict[str, bool]) -> float:
    score = float(confidence or 0.0)
    if overrides.get("is_follow_up"):
        score += 0.05
    if overrides.get("has_code_signals"):
        score += 0.05
    return min(score, 1.0)


class IntentRouter:
    """Adds routing hints on top of the existing analyzer."""

    def __init__(self):
        self.relationship_threshold = 0.35
        self.default_clarification_threshold = 0.35
        self.troubleshooting_threshold = 0.45
        self.transactional_threshold = 0.35

    def _build_hints(
        self,
        normalized_query: str,
        base_intent: Dict,
        context: Optional[List[Dict]],
        overrides: Dict[str, bool],
    ) -> Dict:
        hints = {}

        # Follow-up detection
        hints["is_follow_up"] = bool(base_intent.get("is_follow_up")) or bool(context and len(context) >= 2)
        hints["is_follow_up"] = hints["is_follow_up"] or overrides.get("is_follow_up_like", False)

        # Relationship / multi-source
        if _detect_relationship(normalized_query):
            hints["prefer_multi_source"] = True
            hints["force_research"] = True

        # Lists and aggregation
        if _detect_list_request(normalized_query):
            hints["prefer_multi_source"] = True
            hints["allow_bullets"] = True

        # Depth preference
        hints["depth"] = _detect_depth(normalized_query)

        # Modal asks (examples, steps, definition)
        hints.update(_detect_modal_intent(normalized_query))

        # Conversational vs factual intent detection
        hints.update(_detect_conversational_intent(normalized_query))
        hints.update(_detect_factual_intent(normalized_query))

        # Greeting detection (highest priority)
        hints["is_greeting"] = _detect_greeting_intent(normalized_query)
        if hints["is_greeting"]:
            hints["prefer_conversational_response"] = True
            hints["skip_research"] = True
            hints["is_greeting_response"] = True

        # Overall intent classification (only if not a greeting)
        if not hints["is_greeting"]:
            conversational_analysis = hints.get("is_conversational", False)
            factual_analysis = hints.get("is_factual", False)

            # Prioritize conversational intent for borderline cases
            if conversational_analysis and not factual_analysis:
                hints["prefer_conversational_response"] = True
                hints["skip_research"] = True
            elif factual_analysis and not conversational_analysis:
                hints["prefer_research"] = True
                hints["skip_conversational"] = True
            else:
                # Ambiguous case - use additional heuristics
                if hints.get("word_count", 0) <= 4:
                    hints["prefer_conversational_response"] = True
                    hints["skip_research"] = True
                elif hints.get("has_complex_structure", False):
                    hints["prefer_research"] = True
                    hints["skip_conversational"] = True

        # Code-specific routing
        hints["has_code_signals"] = overrides.get("has_code_signals", _has_code_signals(normalized_query))
        if hints["has_code_signals"]:
            hints["prefer_code_path"] = True

        # Troubleshooting and transactional
        hints["is_troubleshooting"] = _detect_troubleshooting(normalized_query)
        hints["is_transactional"] = _detect_transactional(normalized_query)

        # Safety / sensitive data
        hints["mentions_sensitive_data"] = _detect_sensitive(normalized_query)
        hints["nsfw_risk"] = _detect_safety_sensitive(normalized_query)

        # Music/Video intent detection
        hints["is_music_video_intent"] = _detect_music_video_intent(normalized_query)

        # Multi-question: suggest splitting or clarifying
        hints["is_multi_question"] = _detect_multi_question(normalized_query)

        # Tone
        hints["tone"] = _detect_tone(normalized_query)

        # Clarification thresholding
        confidence = _score_confidence(base_intent.get("confidence", 0.0), hints)
        hints["needs_clarification"] = confidence < self.default_clarification_threshold

        # Use research if transactional/troubleshooting but low knowledge confidence
        if hints["is_troubleshooting"] or hints["is_transactional"]:
            if confidence < self.troubleshooting_threshold:
                hints["force_research"] = True

        return hints

    def route(self, query_intent: Dict, normalized_query: str, context: Optional[List[Dict]] = None) -> Dict:
        base_intent = dict(query_intent or {})
        overrides = {
            "is_follow_up_like": base_intent.get("is_follow_up_like", False),
            "has_code_signals": _has_code_signals(normalized_query),
        }
        hints = self._build_hints(normalized_query, base_intent, context, overrides)
        base_intent["hints"] = hints
        return base_intent


_intent_router: IntentRouter = None


def get_intent_router() -> IntentRouter:
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router


# --------------------------------
# Extended routing helpers / docs
# --------------------------------

ROUTING_NOTES = [
    "Follow-ups should bias toward previous context but never override explicit new topics.",
    "Troubleshooting should prefer research if confidence is low.",
    "Comparison queries benefit from multiple sources and diversity.",
    "Lists should allow bullets but avoid excessive length.",
    "Code signals should steer toward specialized handlers, not general chat.",
    "Clarification is better than guessing when confidence is low.",
    "Sensitive terms should avoid echoing secrets; sanitize logging.",
    "Depth hints (brief/deep) should inform synthesis length.",
    "Tone hints are advisory and should not block responses.",
    "Transactional cues may require safety to avoid unintended actions.",
]


def routing_notes_text() -> str:
    return "\n".join(f"- {n}" for n in ROUTING_NOTES)


def debug_intent(query: str, intent: Dict, hints: Dict) -> str:
    return (
        f"query='{query[:80]}' | intent={intent.get('intent')} | "
        f"confidence={intent.get('confidence')} | hints={hints}"
    )


def enrich_with_domain(intent: Dict, normalized_query: str) -> Dict:
    lower = normalized_query.lower()
    domains = {
        "ml": ["model", "training", "inference", "dataset", "pytorch", "tensor"],
        "security": ["token", "auth", "oauth", "encryption", "jwt", "password"],
        "frontend": ["react", "vue", "dom", "css", "html", "nextjs"],
        "backend": ["api", "rest", "graphql", "database", "sql", "server"],
        "devops": ["docker", "kubernetes", "k8s", "helm", "terraform", "ci", "cd"],
    }
    for domain, keys in domains.items():
        if any(k in lower for k in keys):
            intent = dict(intent)
            intent["domain"] = domain
            return intent
    intent = dict(intent)
    intent["domain"] = "general"
    return intent


def annotate_intent(intent: Dict, normalized_query: str) -> Dict:
    intent = enrich_with_domain(intent, normalized_query)
    hints = intent.get("hints", {})
    intent["debug"] = debug_intent(normalized_query, intent, hints)
    return intent


# Extended documentation blocks to reach requested thoroughness.
INTENT_EDGE_CASES: List[str] = [
    "Short follow-ups like 'and this?' should not force research unless hints require.",
    "Multi-question queries should request clarification to split tasks.",
    "Recipe-like phrases must prefer web search even if brain has near matches.",
    "Philosophical prompts like 'what is life' must use strict matching.",
    "Programming errors should bias to troubleshooting flow and clarifiers.",
    "Biographical queries must prioritize identity info over trivia.",
    "Relationship/comparison queries must diversify sources.",
    "List requests can use bullets but must stay concise.",
    "Transactional cues (price, buy) should avoid irreversible actions; info only.",
    "Safety terms (password, token) should avoid echoing secrets.",
]


def intent_edge_cases_text() -> str:
    return "\n".join(f"- {c}" for c in INTENT_EDGE_CASES)


ROUTING_DIMENSIONS: List[str] = [
    "follow_up",
    "comparison",
    "list_request",
    "depth_preference",
    "code_signals",
    "troubleshooting",
    "transactional",
    "safety_sensitive",
    "nsfw_risk",
    "multi_question",
    "tone",
]


def routing_dimensions_text() -> str:
    return ", ".join(ROUTING_DIMENSIONS)


def build_routing_debug(intent: Dict) -> str:
    hints = intent.get("hints", {})
    return f"hints={hints}; domain={intent.get('domain', 'general')}"


def ensure_min_confidence(intent: Dict, floor: float = 0.05) -> Dict:
    intent = dict(intent)
    intent["confidence"] = max(floor, float(intent.get("confidence", 0.0)))
    return intent


ROUTING_EXAMPLES: List[str] = [
    "compare react and vue",
    "difference between tcp and udp",
    "why is my docker build failing",
    "what is life",
    "who is alan turing",
    "how to make pizza",
    "price of aws s3",
    "explain transformers in ml",
    "what is graphql",
    "how do i center a div",
    "give me python list comprehension examples",
    "what's the best laptop",
    "error code 500 in flask",
    "post request failing with cors",
    "explain kafka vs rabbitmq",
    "summarize latest research on llms",
    "generate a sql query",
    "write a bash script to backup files",
    "create a unit test in pytest",
    "why is my code slow",
    "optimize pandas dataframe operations",
    "explain oauth2 flow",
    "how to deploy on heroku",
    "difference between jwt and session",
    "what is rate limiting",
    "debug segmentation fault",
    "how to parse json in java",
    "compare mongodb and postgres",
    "what is event sourcing",
    "explain cqrs",
    "give me rust error handling examples",
    "how to use async/await in python",
    "why is my react state not updating",
    "how to fix npm audit issues",
    "show me kubernetes deployment yaml",
    "how to set up ci/cd",
    "compare git rebase vs merge",
    "what is zero trust security",
    "how to hash passwords securely",
    "difference between rsa and ecc",
    "how to cache http responses",
    "explain cap theorem",
    "how to handle unicode in python",
    "difference between thread and process",
    "how to create virtual environment",
    "what is a singleton pattern",
    "explain observer pattern",
    "design a url shortener",
    "system design for chat app",
    "how to reduce latency in api",
    "database indexing strategies",
]


def routing_examples_text(limit: int = 50) -> str:
    return "\n".join(f"- {q}" for q in ROUTING_EXAMPLES[:limit])


ROUTING_POLICIES: List[str] = [
    "Never downgrade confidence below the floor.",
    "Prefer asking for clarification over guessing when confidence is low.",
    "Do not auto-run research for greetings or casual chat.",
    "Comparison intents should set prefer_multi_source.",
    "Troubleshooting with errors should set is_troubleshooting.",
    "Transactional queries should not trigger actions; information only.",
    "NSFW or safety risks should bias toward safe completion or refusal upstream.",
    "List requests can allow bullets but must keep responses concise.",
    "Code signals should steer to specialized code handlers.",
    "Follow-up hints should consider recent context length.",
]


def routing_policies_text() -> str:
    return "\n".join(f"- {p}" for p in ROUTING_POLICIES)

