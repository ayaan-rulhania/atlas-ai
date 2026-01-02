---
title: "Announcing Atlas-AI 1.0 – The Open-Source Multimodal Assistant"
date: 2026-01-01
author: Atlas AI Team
description: Atlas-AI 1.0 is now open-source under Apache 2.0. Discover how to integrate a powerful text-and-image assistant in minutes.
---

![Atlas AI Banner](../assets/social-banner.svg)

> **TL;DR:** Atlas-AI 1.0 is live on GitHub under Apache 2.0. Get started with the Python or JS SDK, join our Discord, and help us shape the future of open multimodal AI.

## Why Atlas-AI?

Teams need an assistant that understands text, images, and code – and can be self-hosted, audited, and extended. Atlas-AI delivers:

1. 🤖 **Two transformer models** – Thor 1.0 (stable) & Thor 1.1 (latest research).
2. 🖼 **Image understanding & generation** via TrainX language.
3. 🧠 **Continuous learning** from conversations and curated knowledge.
4. 🔌 **SDKs & REST APIs** for Python, JS, and any language over HTTP.
5. 👐 **Full transparency** – inspect, fork, and improve every layer.

## Quick-Start

```bash
pip install atlas-ai
atlas-chat  # CLI chat with Thor 1.1
```

or

```js
import { Chatbot } from '@atlas-ai/sdk';
const bot = new Chatbot();
console.log(await bot.ask('Hello Atlas!'));
```

## What’s Inside 1.0

| Component | Highlights |
|-----------|------------|
| **Chatbot UI** | React front-end served by Flask back-end |
| **Thor 1.1** | 20-layer, 1.2 B parameters, 2 k token context |
| **TrainX DSL** | Define Q&A and image prompts in plain text |
| **Brain System** | JSON knowledge shards A-Z |
| **Result-Setter** | Authoritative answers & fuzzy matching |

## Roadmap (Public)

- 🎨 Brand-new web UI
- 🔄 Hugging Face model card
- 📊 Grafana community dashboard
- 🔥 Plugins: VS Code, Figma, Discord bot

## Get Involved

1. ⭐ Star the repo – signals community interest.
2. 🍴 Fork & contribute – good first issues are labelled.
3. 💬 Join **discord.gg/atlas-ai** for support & discussion.

_Open minds build better models. We can’t wait to see what you create!_

