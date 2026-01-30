```
╔══════════════════════════════════════════════════════════════╗
║ Incoming request (message + flags: model / think_deeper)     |
╚══════════════════════════════════════════════════════════════╝
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 1) Result Setter (per model)                                  │
│    - Exact match                                              │
│    - Fuzzy (tight for “who is …” / “do you know …”)           │
│    - If hit → return curated answer (no refiner/model)        │
└───────────────────────────────────────────────────────────────┘
                             │ (if no hit)
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 2) Math evaluator (quick calc)                                │
│    - If hit → return result                                   │
└───────────────────────────────────────────────────────────────┘
                             │ (if no hit)
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 3) Identity / greetings / common-sense small talk             │
│    - Identity prompts → Thor intro                            │
│    - Greetings → greeting handler                             │
│    - Compliments/casual → common_sense handler                │
│    - If hit → return                                          │
└───────────────────────────────────────────────────────────────┘
                             │ (if no hit)
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 4) Image handling (if image_data)                             │
│    - Process/describe image; augment message                  │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 5) Context & intent                                           │
│    - Build contextual_message (follow-ups/pronouns)           │
│    - Intent analyzer → query_intent                           │
│    - Intent router adds hints (follow-up, multi-source, etc.) │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 6) Knowledge fetch                                            │
│    - Brain lookup (contextual_message)                        │
│    - Recipe/relationship/low-knowledge → force web research   │
│    - Think Deeper → always research + brain + synthesis       │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 7) Knowledge filtering & rerank                               │
│    - Semantic relevance scorer                                │
│    - Reranker (recency + diversity)                           │
│    - Clarifier if no knowledge/confidence is low              │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 8) Model inference (Thor)                                     │
│    - Tasks: text_generation / QA / classification / NER, etc. │
│    - If model unavailable → fallback to knowledge             │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 9) Synthesis                                                  │
│    - Synthesize_knowledge (multi-source)                      │
│    - Relationship questions → merged perspectives             │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│ 10) Answer refinement (skipped if Result Setter hit)          │
│     - Clean/structure text                                    │
│     - Model tag, follow-up marker                             │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
╔══════════════════════════════════════════════════════════════╗
║ Final response to the user                                    ║
╚══════════════════════════════════════════════════════════════╝
```
