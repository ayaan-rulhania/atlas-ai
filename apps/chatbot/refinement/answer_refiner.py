"""Final answer refinement utilities.

This module focuses on polishing responses to make them more readable,
grounded, and transparent. It provides:
- Cleaning via the shared response cleaner
- Light structuring (sections, bullets)
- Optional source mentions (titles only)
- Minimal transparency notes (model + follow-up awareness)
- Guardrails for redundant whitespace, accidental code fences, and
  overly long lines

Everything is enabled by default; there are no toggles.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import re

from services.response_cleaner import ResponseCleaner

# Local wrapper to reuse the ResponseCleaner instance
_response_cleaner = ResponseCleaner()


def _clean_response_text(text: str) -> str:
    return _response_cleaner.clean_response(text)


def _squash_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text or "").strip()


def _trim_bullets(text: str) -> str:
    # Avoid stray hyphens without text
    return re.sub(r"(?m)^\s*-\s*$", "", text)


def _ensure_sentence_spacing(text: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1. \2", text)


def _truncate(text: str, limit: int = 2400) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_sources(knowledge_used: List[Dict], limit: int = 3) -> Optional[str]:
    """
    Previously, this rendered a visible `_Sources:_` line with titles for the
    top knowledge items. In practice this was noisy and felt like debug output
    to users, so we now hide it by default.

    The function is kept for backwards compatibility and future UI hooks, but
    returns ``None`` so no explicit sources footer is added to answers.
    """
    return None


def _shorten_code_blocks(text: str, max_lines: int = 40) -> str:
    blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    for block in blocks:
        lines = block.splitlines()
        if len(lines) > max_lines:
            trimmed = "\n".join(lines[:max_lines] + ["..."])
            text = text.replace(block, trimmed)
    return text


def _prepend_follow_up_note(hints: Dict) -> Optional[str]:
    """
    Enhanced follow-up handling that provides contextual awareness without
    visible debug text. Instead, we ensure the response feels natural and
    connected to the conversation context.
    """
    if not hints.get('is_follow_up'):
        return None

    # Instead of visible notes, we can modify response starters or tone
    # This is handled in the main refinement process now
    return None


def _enhance_follow_up_context(answer: str, hints: Dict) -> str:
    """
    Enhance responses for follow-up questions to feel more contextual and natural.
    """
    if not hints.get('is_follow_up'):
        return answer

    # Add natural conversational connectors for follow-ups
    follow_up_starters = [
        "Based on what you asked earlier,",
        "Following up on that,",
        "To elaborate,",
        "Additionally,",
        "Regarding your question,",
        "To continue from where we left off,"
    ]

    # Only add if the answer doesn't already start with a connector
    existing_starters = ['based on', 'following up', 'to elaborate', 'additionally', 'regarding', 'to continue']
    if not any(starter in answer.lower()[:50] for starter in existing_starters):
        # Choose a starter that fits the context
        if len(answer.split()) > 15:  # Longer answers benefit from context setting
            starter = "To elaborate on that:"
        else:
            starter = "Sure, here's more detail:"

        return f"{starter} {answer}"

    return answer


def _render_sections(sections: List[str]) -> str:
    return "\n\n".join([s for s in sections if s]).strip()


def _short_title_from_text(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9']+", text)
    if not words:
        return "Summary"
    short = words[:3]
    return " ".join(short).title()


def _apply_rich_formatting(answer: str, hints: Dict) -> str:
    """
    Enhanced rich formatting with better structure detection and section headers.
    More intelligent about when to add formatting and what type to use.
    """
    text = answer.strip()
    if not text:
        return text

    if text.startswith("#"):
        return text  # already formatted

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return text

    # Enhanced structure detection
    wants_structure = bool(
        hints.get("asks_for_steps") or
        hints.get("wants_structure") or
        len(sentences) > 8 or  # Long answers benefit from structure
        len(text) > 600 or     # Long text needs organization
        any(keyword in text.lower() for keyword in [
            'steps', 'process', 'guide', 'tutorial', 'how to',
            'comparison', 'versus', 'vs', 'differences', 'alternatives'
        ])
    )

    if not wants_structure:
        return text

    # Better title detection
    title = (
        hints.get("detected_subject") or
        hints.get("primary_topic") or
        hints.get("topic") or
        _short_title_from_text(sentences[0])
    )
    title = _short_title_from_text(title)

    # Enhanced content analysis for better structuring
    has_steps = any(word in text.lower() for word in ['first', 'then', 'next', 'after', 'finally', 'step'])
    has_comparison = any(word in text.lower() for word in ['versus', 'vs', 'compared to', 'unlike', 'whereas', 'better than', 'worse than'])
    has_list = '\n-' in text or '\n*' in text or '•' in text
    has_examples = any(word in text.lower() for word in ['example', 'for instance', 'such as', 'like'])

    intro = sentences[0]
    remaining_sentences = sentences[1:]

    # Structured formatting based on content type
    if has_steps and len(remaining_sentences) >= 3:
        # Format as step-by-step guide
        return f"## {title}\n\n{intro}\n\n**Steps:**\n" + "\n".join(f"{i+1}. {sent}" for i, sent in enumerate(remaining_sentences[:8]))

    elif has_comparison and len(remaining_sentences) >= 4:
        # Format as comparison
        mid_point = len(remaining_sentences) // 2
        option1_sentences = remaining_sentences[:mid_point]
        option2_sentences = remaining_sentences[mid_point:]

        formatted = f"## {title}\n\n{intro}\n\n"
        if option1_sentences:
            formatted += "**Option 1:**\n" + "\n".join(f"- {sent}" for sent in option1_sentences[:4]) + "\n\n"
        if option2_sentences:
            formatted += "**Option 2:**\n" + "\n".join(f"- {sent}" for sent in option2_sentences[:4])
        return formatted

    elif has_list or hints.get("allow_bullets"):
        # Format with bullets for clarity
        if len(remaining_sentences) >= 2:
            bullets = "\n".join(f"- {sent}" for sent in remaining_sentences[:6])
            return f"## {title}\n\n{intro}\n\n{bullets}"

    else:
        # Default structured paragraph format
        if len(remaining_sentences) < 2:
            return f"## {title}\n\n{intro}"
        elif len(remaining_sentences) <= 4:
            body = "\n\n".join(remaining_sentences)
            return f"## {title}\n\n{intro}\n\n{body}"
        else:
            # Split into sections for very long content
            summary_sentences = remaining_sentences[:3]
            details_sentences = remaining_sentences[3:6]

            formatted = f"## {title}\n\n{intro}\n\n"
            if summary_sentences:
                formatted += "**Summary:**\n" + "\n\n".join(summary_sentences) + "\n\n"
            if details_sentences:
                formatted += "**Details:**\n" + "\n\n".join(details_sentences)
            return formatted


def _add_structuring(answer: str, hints: Dict) -> str:
    """Light formatting when the user likely wants lists/steps."""
    lower = answer.lower()
    if hints.get("asks_for_steps") and " - " not in answer and "1." not in answer:
        parts = [p.strip() for p in re.split(r"(?<=[.;])\s+", answer) if len(p.strip()) > 0]
        if len(parts) >= 3:
            bullets = "\n".join(f"- {p}" for p in parts)
            return bullets
    if hints.get("allow_bullets") and " - " not in answer and "\n-" not in answer:
        # Only convert to bullets when the text is long enough and has multiple sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
        if len(sentences) >= 3 and len(answer) > 220:
            return "\n".join(f"- {s}" for s in sentences)
    return answer


def _detect_contradictions(text: str) -> List[Dict]:
    """Detect potential contradictory statements in the text."""
    contradictions = []
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # Common contradiction patterns
    contradiction_pairs = [
        (r'\bis\b', r'\bis not\b'),
        (r'\bcan\b', r'\bcannot\b'),
        (r'\bdoes\b', r'\bdoes not\b'),
        (r'\bhas\b', r'\bdoes not have\b'),
        (r'\bworks\b', r'\bdoes not work\b'),
        (r'\bsupports\b', r'\bdoes not support\b'),
    ]

    for i, sentence1 in enumerate(sentences):
        for j, sentence2 in enumerate(sentences[i+1:], i+1):
            s1_lower = sentence1.lower()
            s2_lower = sentence2.lower()

            # Check for direct contradictions
            for pos_pattern, neg_pattern in contradiction_pairs:
                if (re.search(pos_pattern, s1_lower) and re.search(neg_pattern, s2_lower)) or \
                   (re.search(neg_pattern, s1_lower) and re.search(pos_pattern, s2_lower)):
                    contradictions.append({
                        'sentence1': sentence1.strip(),
                        'sentence2': sentence2.strip(),
                        'type': 'direct_contradiction'
                    })

            # Check for conflicting numbers/dates
            s1_nums = re.findall(r'\b\d+\b', s1_lower)
            s2_nums = re.findall(r'\b\d+\b', s2_lower)
            if s1_nums and s2_nums and s1_nums != s2_nums:
                # Check if they're talking about the same topic
                s1_words = set(s1_lower.split())
                s2_words = set(s2_lower.split())
                if len(s1_words & s2_words) >= 2:  # Significant word overlap
                    contradictions.append({
                        'sentence1': sentence1.strip(),
                        'sentence2': sentence2.strip(),
                        'type': 'numeric_conflict'
                    })

    return contradictions


def _fix_contradictions(text: str, contradictions: List[Dict]) -> str:
    """Attempt to resolve detected contradictions."""
    if not contradictions:
        return text

    # For now, add a caution note about potential inconsistencies
    # More sophisticated resolution could be added later
    caution_note = "\n\n*Note: Some details in this response may vary by context or source. For precise information, please specify the exact scenario or timeframe.*"

    return text + caution_note


def _improve_answer_flow(text: str, hints: Dict) -> str:
    """Improve the logical flow and structure of complex answers."""
    # Detect if this is a complex multi-part answer
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) < 4:
        return text  # Keep simple answers as-is

    # Check for different answer types that benefit from better structure
    has_steps = any(word in text.lower() for word in ['first', 'then', 'next', 'after', 'finally', 'step'])
    has_comparison = any(word in text.lower() for word in ['versus', 'vs', 'compared to', 'unlike', 'whereas'])
    has_list = '\n-' in text or '\n*' in text

    if has_steps and not has_list:
        # Convert step-based content to numbered list
        parts = re.split(r'(first|then|next|after|finally|step \d+)', text, flags=re.IGNORECASE)
        if len(parts) > 3:
            structured = []
            current_step = []
            for part in parts:
                part_lower = part.lower()
                if any(indicator in part_lower for indicator in ['first', 'then', 'next', 'after', 'finally']) or 'step' in part_lower:
                    if current_step:
                        structured.append(' '.join(current_step).strip())
                        current_step = []
                    structured.append(part.strip())
                else:
                    current_step.append(part)
            if current_step:
                structured.append(' '.join(current_step).strip())

            return '\n'.join(structured)

    elif has_comparison and not has_list:
        # Add section headers for comparison content
        if ' vs ' in text.lower() or ' versus ' in text.lower():
            return text  # Already has comparison structure
        elif len(sentences) > 5:
            # Split into pros/cons or alternative sections if applicable
            return text

    return text


def _enhance_tone_consistency(text: str, hints: Dict) -> str:
    """Ensure consistent tone throughout the response."""
    # Detect requested tone from hints
    requested_tone = hints.get('tone', 'normal').lower()

    # Simple tone adjustments (more sophisticated tone control could be added)
    if requested_tone == 'formal':
        # Ensure more formal language
        text = re.sub(r'\bI think\b', 'It appears', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprobably\b', 'likely', text, flags=re.IGNORECASE)
    elif requested_tone == 'friendly':
        # Add warmth where appropriate
        if not text.startswith(('Hi', 'Hello', 'Hey')) and len(text.split()) > 10:
            text = "Here's what I found: " + text

    return text


def _clean_and_structure(answer: str, hints: Dict) -> str:
    cleaned = _clean_response_text(answer)

    # Enhanced coherence checking
    contradictions = _detect_contradictions(cleaned)
    cleaned = _fix_contradictions(cleaned, contradictions)

    # Improved structure and flow
    cleaned = _improve_answer_flow(cleaned, hints)
    cleaned = _add_structuring(cleaned, hints)

    # Tone consistency
    cleaned = _enhance_tone_consistency(cleaned, hints)

    # Existing cleaning steps
    cleaned = _shorten_code_blocks(cleaned)
    cleaned = _trim_bullets(cleaned)
    cleaned = _ensure_sentence_spacing(cleaned)
    cleaned = _squash_blank_lines(cleaned)
    cleaned = _truncate(cleaned)
    return cleaned


class AnswerRefiner:
    """Cleans, structures, and annotates answers."""

    def __init__(self):
        self.max_output_chars = 2400

    def refine(
        self,
        answer: str,
        knowledge_used: List[Dict],
        query_intent: Dict,
        model_name: str,
    ) -> str:
        if not answer:
            return answer

        hints = query_intent.get("hints", {}) if query_intent else {}
        sections = []

        core = _clean_and_structure(answer, hints)
        core = _enhance_follow_up_context(core, hints)  # Enhanced follow-up handling
        core = _apply_rich_formatting(core, hints)
        sections.append(core.strip())

        # Optional transparency: follow-up marker + source titles + model label
        follow_up_note = _prepend_follow_up_note({"is_follow_up": bool(query_intent.get("is_follow_up")) or bool(hints.get("is_follow_up"))})
        if follow_up_note:
            sections.append(follow_up_note)

        sources_line = _format_sources(knowledge_used or [], limit=4)
        if sources_line:
            sections.append(sources_line)

        if model_name:
            sections.append(f"_Model:_ {model_name}")

        final = _render_sections(sections)
        return _truncate(final, self.max_output_chars)


_answer_refiner: AnswerRefiner = None


def get_answer_refiner() -> AnswerRefiner:
    global _answer_refiner
    if _answer_refiner is None:
        _answer_refiner = AnswerRefiner()
    return _answer_refiner


# --------------------------------
# Extended helpers for transparency
# --------------------------------

def summarize_answer(answer: str) -> str:
    """Provide a short diagnostic summary of the answer length and line count."""
    lines = answer.splitlines()
    return f"{len(answer)} chars; {len(lines)} lines"


def highlight_clarifications(answer: str) -> str:
    """Emphasize clarifying questions if present."""
    if "clarify" in answer.lower():
        return f"**Clarification:** {answer}"
    return answer


def add_heading(answer: str, heading: str) -> str:
    """Prepend a heading if not already present."""
    if heading and not answer.startswith(heading):
        return f"{heading}\n\n{answer}"
    return answer


def emphasize_sources(answer: str, knowledge_used: List[Dict]) -> str:
    """No-op placeholder: source listing disabled."""
    return answer


def strip_trailing_hashes(answer: str) -> str:
    return answer.rstrip("#").strip()


def ensure_periods(answer: str) -> str:
    return re.sub(r"(?m)([a-zA-Z0-9])$", r"\1.", answer)


def normalize_headings(answer: str) -> str:
    return re.sub(r"(?m)^#+\s*", "", answer)


def cap_list_length(answer: str, max_items: int = 8) -> str:
    """Limit bullet list length to keep responses concise."""
    lines = answer.splitlines()
    bullets = [i for i, line in enumerate(lines) if line.strip().startswith("- ")]
    if len(bullets) <= max_items:
        return answer
    cut_index = bullets[max_items] if len(bullets) > max_items else len(lines)
    trimmed = lines[:cut_index] + ["- ..."]
    return "\n".join(trimmed)


def guard_empty_sections(answer: str) -> str:
    """Remove empty sections often introduced by cleaning."""
    return re.sub(r"(?m)^\s*(_Sources:_)?\s*$", "", answer).strip()


def ensure_markdown_safe(answer: str) -> str:
    """Minimal markdown safety for untrusted text."""
    return answer.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")


def annotate_model(answer: str, model_name: str) -> str:
    if "_Model:" in answer:
        return answer
    return f"{answer}\n\n_Model:_ {model_name}"


def add_follow_up_marker(answer: str, is_follow_up: bool) -> str:
    # Follow-up awareness should be handled naturally in the response content,
    # not as a visible label. This function is kept for backwards compatibility
    # but no longer adds visible markers.
    return answer


def sanitize(answer: str) -> str:
    answer = strip_trailing_hashes(answer)
    answer = guard_empty_sections(answer)
    answer = ensure_markdown_safe(answer)
    return answer


def postprocess_final(answer: str, knowledge_used: List[Dict], hints: Dict, model_name: str) -> str:
    answer = cap_list_length(answer)
    answer = sanitize(answer)
    return answer


# -----------------------------
# Extended style guidance
# -----------------------------

STYLE_RULES: List[str] = [
    "Prefer short paragraphs over long walls of text.",
    "Use bullets only when summarizing steps or options.",
    "Avoid unnecessary code fences unless code is present.",
    "Be explicit about models to maintain transparency.",
    "Keep sources concise; titles only, no URLs.",
    "Trim trailing whitespace and excessive blank lines.",
    "Avoid shouting; keep casing natural.",
    "Guard against hallucinated citations.",
    "When uncertain, ask for a single clarifying detail.",
    "Keep markdown simple for broad client compatibility.",
]


def style_rules_text() -> str:
    return "\n".join(f"- {r}" for r in STYLE_RULES)


def ensure_lower_title(answer: str) -> str:
    return re.sub(r"(?m)^TITLE: ", "Title: ", answer)


def compact_answer(answer: str, max_lines: int = 60) -> str:
    lines = answer.splitlines()
    if len(lines) <= max_lines:
        return answer
    return "\n".join(lines[:max_lines] + ["..."])


def ensure_section_spacing(answer: str) -> str:
    return re.sub(r"(?m)([A-Za-z0-9])\n(_Sources:_)", r"\\1\n\n\\2", answer)


def strip_duplicate_sections(answer: str) -> str:
    seen = set()
    lines = []
    for line in answer.splitlines():
        key = line.strip().lower()
        if key in seen and key.startswith("_sources:_"):
            continue
        seen.add(key)
        lines.append(line)
    return "\n".join(lines)


REFINER_CHECKLIST: List[str] = [
    "Ensure answer always includes model transparency line.",
    "Do not invent citations; only use existing titles.",
    "Keep responses within 2400 characters unless future changes require otherwise.",
    "Normalize headings to avoid markdown level issues.",
    "Strip redundant blank lines created during cleaning.",
    "Preserve code fences unless they exceed length caps.",
    "Avoid duplicate source blocks if refine runs multiple times.",
    "Ensure follow-up marker appears only once.",
    "Guard against accidental HTML/script injection.",
    "Favor concise bullets when user intent signals steps.",
]


def refiner_checklist_text() -> str:
    return "\n".join(f"- {item}" for item in REFINER_CHECKLIST)


ANSWER_TEMPLATES: List[str] = [
    "Here is a concise explanation: ...",
    "Steps you can follow:\n- Step 1\n- Step 2\n- Step 3",
    "Key points:\n- Point A\n- Point B\n- Point C",
    "Example code:\n```python\n# code here\n```",
    "Summary:\n- What it is\n- Why it matters\n- How to use it",
    "Troubleshooting checklist:\n- Check logs\n- Verify inputs\n- Reproduce minimal case",
    "Comparison summary:\n- Option 1: pros/cons\n- Option 2: pros/cons\n- Recommendation",
    "Data guidance:\n- Input format\n- Validation\n- Output expectations",
    "Performance tips:\n- Baseline\n- Optimize hot path\n- Measure again",
    "Security tips:\n- Avoid secrets in logs\n- Use env vars\n- Rotate keys",
]


def answer_templates_text() -> str:
    return "\n".join(f"- {t}" for t in ANSWER_TEMPLATES)


REFINER_LONG_NOTES = """
Answer refinement notes:
- Always append model transparency tag.
- Include sources only when titles are available.
- Keep responses concise; truncate when needed.
- Preserve code fences unless excessively long.
- Keep markdown simple for wide client compatibility.
- Avoid nested bullets; prefer single-level lists.
- Use clarifier markers only when follow-up detected.
- Avoid hallucinating citations or links.
- Ensure sentences are separated for readability.
- Respect user intent; do not over-format if not needed.
- Avoid inserting unsolicited opinions.
- Keep examples minimal unless explicitly requested.
- Do not change numeric values during cleaning.
- Avoid aggressive paraphrasing; preserve meaning.
- Keep whitespace tidy and consistent.
- Avoid leaking internal debug info to the user.
- Keep response cleaner usage centralized.
- Prefer deterministic outputs for the same inputs.
- Keep output encoding safe for markdown.
- Avoid altering capitalization in code.
- Keep headings optional and minimal.
- Avoid redundant source blocks.
- Keep line count reasonable for chat windows.
- Avoid overly casual tone unless prompted.
- Avoid heavy sarcasm; stay professional.
- Keep safety considerations in mind when refining.
- Ensure follow-up marker appears only once.
- Keep bullet count capped to reduce clutter.
- Maintain ASCII where possible.
- Remember this layer is lightweight; avoid heavy logic.
"""


def refiner_long_notes_text() -> str:
    return REFINER_LONG_NOTES.strip()


