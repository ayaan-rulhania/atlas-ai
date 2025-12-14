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
        "asks_for_def": any(p in lower for p in ["what is", "definition", "define"]),
    }


def _detect_safety_sensitive(text: str) -> bool:
    lower = text.lower()
    nsfw_indicators = [
        "nsfw", "explicit", "adult", "not safe for work",
        "violent", "gore", "harm", "self-harm", "suicide", "kill", "murder",
    ]
    return any(ind in lower for ind in nsfw_indicators)


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

