"""Generate clarifying prompts when confidence is low.

The clarifier aims to keep interaction smooth by:
- Asking for the minimum additional detail needed
- Suggesting useful dimensions (framework, domain, depth, constraints)
- Staying concise to avoid user friction
- Handling programming vs. general knowledge vs. factual asks differently

Everything is on by default.
"""

from __future__ import annotations

from typing import Dict, List


GENERIC_PROMPTS = [
    "Can you share a bit more detail so I can answer precisely?",
    "What context or constraints should I keep in mind?",
    "Which part should I focus on first?",
]

PROGRAMMING_PROMPTS = [
    "Which language, framework, or version are you using?",
    "Can you share the exact error message or a short snippet?",
    "Are you targeting backend, frontend, or CLI?",
]

DEFINITION_PROMPTS = [
    "Are you looking for a concise definition or a deep-dive?",
    "Should I include examples or just the core definition?",
]

RELATIONSHIP_PROMPTS = [
    "Do you want pros/cons, performance, or conceptual differences?",
    "Which two options should I compare most closely?",
]


def _pick_prompt(intent: str, hints: Dict) -> str:
    if intent == "programming":
        return PROGRAMMING_PROMPTS[0]
    if intent in ("definition", "biographical"):
        return DEFINITION_PROMPTS[0]
    if hints.get("prefer_multi_source"):
        return RELATIONSHIP_PROMPTS[0]
    return GENERIC_PROMPTS[0]


def _build_suffix(intent: str, normalized_query: str) -> str:
    if intent == "programming":
        return "Share the language, framework, error text, or expected output."
    if intent in ("definition", "biographical"):
        return "Tell me if you want a short definition, timeline, or examples."
    return f"Add any keywords for '{normalized_query}' to help me aim correctly."


class Clarifier:
    def __init__(self):
        self.max_len = 280

    def build_clarification(self, normalized_query: str, query_intent: Dict, knowledge_available: bool) -> str:
        intent = (query_intent or {}).get("intent", "general")
        hints = (query_intent or {}).get("hints", {})
        if knowledge_available:
            return ""

        if hints.get("needs_clarification", False) or intent in ["general", "programming", "definition"]:
            prompt = _pick_prompt(intent, hints)
            suffix = _build_suffix(intent, normalized_query)
            msg = f"{prompt} {suffix}"
            return msg[: self.max_len]
        return ""


_clarifier: Clarifier = None


def get_clarifier() -> Clarifier:
    global _clarifier
    if _clarifier is None:
        _clarifier = Clarifier()
    return _clarifier


# --------------------------------
# Extended templates and utilities
# --------------------------------

CLARIFICATION_DIMENSIONS = [
    "language/framework",
    "version/platform",
    "input/output format",
    "constraints (time/memory/performance)",
    "audience (beginner/intermediate/advanced)",
    "depth (brief/deep dive)",
    "examples vs. conceptual overview",
    "security/privacy expectations",
    "domain (web/mobile/cloud/data/ml)",
    "tooling (IDE/CLI/CI)",
]


def dimension_hints() -> str:
    return ", ".join(CLARIFICATION_DIMENSIONS)


def build_multi_prompt(intent: str) -> str:
    base = _pick_prompt(intent, {})
    dims = dimension_hints()
    return f"{base} Useful details: {dims}."


def clarify_for_error(error_text: str) -> str:
    if not error_text:
        return ""
    return (
        f"I saw an error mentioned. Please share the exact error text and what you tried. "
        f"This helps me give a precise fix for: {error_text[:120]}"
    )


def clarify_for_data(task: str) -> str:
    return (
        f"To help with '{task}', tell me the data shape, size, and source (CSV/DB/API). "
        f"Do you need SQL, Python, or a conceptual explanation?"
    )


def clarify_for_design(task: str) -> str:
    return (
        f"For design questions like '{task}', mention target users, constraints, and whether you prefer "
        f"wireframes, architecture, or step-by-step guidance."
    )


def choose_clarifier(intent: str, hints: Dict, normalized_query: str) -> str:
    if hints.get("is_troubleshooting"):
        return clarify_for_error(normalized_query)
    if hints.get("prefer_multi_source"):
        return RELATIONSHIP_PROMPTS[0]
    if intent == "programming":
        return PROGRAMMING_PROMPTS[1]
    if intent == "definition":
        return DEFINITION_PROMPTS[1]
    return build_multi_prompt(intent)


def clarifier_catalog() -> Dict[str, List[str]]:
    return {
        "generic": GENERIC_PROMPTS,
        "programming": PROGRAMMING_PROMPTS,
        "definition": DEFINITION_PROMPTS,
        "relationship": RELATIONSHIP_PROMPTS,
    }


def render_catalog() -> str:
    catalog = clarifier_catalog()
    lines = []
    for k, prompts in catalog.items():
        lines.append(f"{k}:")
        for p in prompts:
            lines.append(f"  - {p}")
    return "\n".join(lines)


CLARIFIER_SCENARIOS = [
    {"intent": "programming", "hint": "error", "ask": "Share error text, stack trace, and environment."},
    {"intent": "programming", "hint": "performance", "ask": "State current performance, expected target, and constraints."},
    {"intent": "definition", "hint": "depth", "ask": "Do you want a one-liner or detailed explanation with examples?"},
    {"intent": "biographical", "hint": "focus", "ask": "Should I cover career highlights, timeline, or major works?"},
    {"intent": "comparison", "hint": "criteria", "ask": "List the criteria to compare (performance, cost, ease of use)."},
    {"intent": "data", "hint": "format", "ask": "Describe your data source (CSV/DB/API) and target schema."},
    {"intent": "design", "hint": "audience", "ask": "Who is the target user and what are their goals?"},
]


def format_scenarios() -> str:
    lines = []
    for sc in CLARIFIER_SCENARIOS:
        lines.append(f"- intent={sc['intent']} hint={sc['hint']}: {sc['ask']}")
    return "\n".join(lines)


def pick_scenario(intent: str, hint: str) -> str:
    for sc in CLARIFIER_SCENARIOS:
        if sc["intent"] == intent and sc["hint"] == hint:
            return sc["ask"]
    return ""


def build_targeted_clarifier(intent: str, hints: Dict, normalized_query: str) -> str:
    if hints.get("is_troubleshooting"):
        ask = pick_scenario("programming", "error")
        return ask or choose_clarifier(intent, hints, normalized_query)
    if hints.get("prefer_multi_source"):
        ask = pick_scenario("comparison", "criteria")
        return ask or choose_clarifier(intent, hints, normalized_query)
    return choose_clarifier(intent, hints, normalized_query)


CLARIFIER_EXAMPLES: List[str] = [
    "Can you specify the programming language and version?",
    "Which framework or library are you using?",
    "What is the exact error message or stack trace?",
    "What output did you expect versus what you got?",
    "Is this for backend, frontend, CLI, or mobile?",
    "Do you want a quick summary or a detailed walkthrough?",
    "Should I include code examples?",
    "What performance or latency targets do you have?",
    "What is the size and format of your data?",
    "Are there any security or privacy constraints?",
    "Who is the target audience or user persona?",
    "Do you want alternatives or just the best-practice approach?",
    "Should I focus on conceptual explanation or practical steps?",
    "Is this for production or a prototype?",
    "What tools or environment are you using (IDE/CLI/CI)?",
    "Do you need compatibility with specific OS or hardware?",
    "Should I compare trade-offs between two options?",
    "Do you prefer bullet points or prose?",
    "Should I include references to external standards or docs?",
    "Is there a deadline or urgency for this task?",
    "Do you want me to check for common pitfalls first?",
    "Is there an existing code snippet I should adapt?",
    "Do you need output in JSON, text, or code?",
    "Should I optimize for readability or performance?",
    "Is there a specific version constraint (e.g., Python 3.8)?",
    "Should I assume internet access or offline constraints?",
    "Is this academic, production, or hobby work?",
    "Any industry/domain context (finance, health, education)?",
    "Should I avoid third-party dependencies?",
    "Do you want testing strategies included?",
    "Any particular style guide to follow?",
    "Do you want example inputs/outputs?",
    "How familiar are you with this topic (beginner/advanced)?",
    "Should I include edge cases and error handling?",
    "Do you want a checklist of steps?",
    "Is this for a specific device or browser?",
    "Do you want me to highlight risks or limitations?",
    "Do you need deployment guidance too?",
    "Should I focus on conceptual differences or practical usage?",
    "Do you want a recommendation or neutral overview?",
    "Are there budget or licensing limits?",
    "Do you need integration guidance with other tools?",
    "Is this for teaching someone else or for your own work?",
    "Do you prefer metric or imperial units (if relevant)?",
    "Should I use plain language or technical jargon?",
    "Any constraints on response length?",
    "Should I propose multiple options or just one?",
    "Do you need citations or references?",
    "Should I avoid AI-specific terminology?",
    "Do you want visual layout suggestions or just text?",
    "Is accessibility a priority?",
    "Any localization/language considerations?",
]


def list_examples(limit: int = 20) -> List[str]:
    return CLARIFIER_EXAMPLES[:limit]


def examples_text(limit: int = 50) -> str:
    return "\n".join(f"- {c}" for c in CLARIFIER_EXAMPLES[:limit])


CLARIFIER_RULES: List[str] = [
    "Ask only one concise question at a time.",
    "Stay neutral; do not bias user toward an answer.",
    "Limit length to remain chat-friendly.",
    "Favor actionable dimensions (language, framework, version, error).",
    "Do not repeat the user's entire message back to them.",
    "Avoid sensitive data; never request secrets.",
    "Keep tone polite but efficient.",
    "Prefer clarifying when confidence is low instead of guessing.",
    "Skip clarification if knowledge is already available.",
    "Keep formatting simple; no nested bullets.",
]


def clarifier_rules_text() -> str:
    return "\n".join(f"- {r}" for r in CLARIFIER_RULES)


CLARIFIER_QA_PAIRS: List[Dict[str, str]] = [
    {"q": "My app crashes", "a": "Share the stack trace, environment, and recent change."},
    {"q": "Need best database", "a": "State use-case, scale, budget, and managed vs self-hosted."},
    {"q": "Explain AI", "a": "Clarify domain: ML basics, transformers, or deployment?"},
    {"q": "Website slow", "a": "Front-end or backend? Provide metrics, pages affected."},
    {"q": "Code not working", "a": "Share snippet, error, expected behavior, and runtime."},
    {"q": "How to learn python", "a": "Beginner or intermediate? Prefer projects or theory?"},
    {"q": "Need system design", "a": "State scale, constraints, and main features to design."},
    {"q": "Fix CORS issue", "a": "What request, headers, and server setup? Include browser error."},
    {"q": "Better laptop", "a": "Budget, workload (coding/design/gaming), and OS preference?"},
    {"q": "Help with resume", "a": "Target role, years of experience, and notable projects."},
]


def clarifier_qa_text(limit: int = 20) -> str:
    lines = []
    for pair in CLARIFIER_QA_PAIRS[:limit]:
        lines.append(f"- Q: {pair['q']} | Ask: {pair['a']}")
    return "\n".join(lines)

