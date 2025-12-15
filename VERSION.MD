# Atlas AI — Version Log

This file tracks **major changes** made to this project over time.

## Format
- **Date**: YYYY-MM-DD
- **Summary**: 1–3 bullets describing what changed and why
- **Notes** (optional): migrations, breaking changes, ports, flags

---

## 2025-12-14
- **Research**: Hardened web research to pull from **Google + Bing + DuckDuckGo + Wikipedia** (always-on, with SerpAPI/Brave optional) and improved deduplication/metadata.
- **Accuracy**: Added a conservative final "accuracy check" pass to reduce ungrounded numeric claims when sources are present.
- **Images**: Improved "another angle/style/background" flow so it reliably fetches a *new* image variant (variant-aware image selection + better follow-up phrasing). Enhanced image tweak parsing to support specific angles ("top-down angle"), styles ("watercolor style"), and colors ("make it red").
- **Gems**: Added **Gems** (custom sub-models) end-to-end: try-before-create, create/edit/delete, add sources (links/files), select Gems in the model dropdown, and manage Gems from the sidebar.
- **Gems UI**: Improved gem sidebar layout — name, tone badge, edit/delete buttons all on one line with title case formatting. Enhanced tone badges with color coding (Friendly/Calm/Formal/Critical/Normal). Fixed "New Gem" button to remove duplicate plus sign.
- **Gems Sources**: Significantly improved gem source reading — better HTML content extraction (prioritizes article/main content), increased content limits (2500 chars), improved link parsing (up to 5 links), and gem sources are always prioritized in knowledge arrays even after reranking.
- **UI**: Sidebar spacing/padding tweaks and new header buttons (Customize + Help) with inline SVG icons. Fixed games/office suite loaders to reliably open correct URLs with better phrase matching.
- **Typography**: Chat messages (user + assistant) now use Roboto font for better readability while UI keeps Aboreto.

### Notes
- **Gem model IDs**: saved gems are selected as `gem:<id>`; previews use `gem:preview` with a `gem_draft` payload.
- **Gem sources**: Links are fetched with improved content extraction, files support up to 10 items with 2500 char content limit each.
- **Gem priority**: Gem sources have `priority: 1` flag and are always placed first in knowledge arrays, ensuring they're used over web search results.

---

## 2025-12-08
- **UI**: Major redesign iterations for the main chat experience (layout, spacing, markdown rendering, theming), moving toward a more minimal, compact chat surface while preserving existing features.
- **Images**: Added an image-request flow ("create an image of …") and hardened frontend rendering so markdown images reliably display as images (not raw markdown).
- **Dev tooling**: Added **Dev Atlas** (`/dev-atlas`) — a minimal, no-history chat page for fast testing (single prompt box + plus button), backed by the same `/api/chat` Thor 1.0 endpoint.

### Notes
- **Dev Atlas URL**: `/dev-atlas` (served by the same Flask app)
- **Port override**: server can be started with `PORT=5001 ...` (defaults to 5000)

---

## 2025-12-07
- **Cleanup**: Removed all Odin 0.5 references and the `/odin-0.5` directory; simplified to a single-model (Thor 1.0) architecture.
- **Frontend**: Updated UI templates/components to remove Odin selection and align copy, docs, and routing to Thor-only.
