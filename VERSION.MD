# Atlas AI — Version Log

This file tracks **major changes** made to this project over time.

## Format
- **Date**: YYYY-MM-DD
- **Summary**: 1–3 bullets describing what changed and why
- **Notes** (optional): migrations, breaking changes, ports, flags

---

## 2025-12-15 (Final Update - UI Polish)
- **Dark Mode Hello Text**: Removed gold gradient, now uses white/cream gradient for better readability
- **Light Mode Upgrades**: 
  - Upgrade button now white with gradient (was black)
  - Added more gradients throughout light mode UI (send button, sidebar icons, model selector, etc.)
  - Enhanced visual consistency with gradient theme
- **Stable Mode Implementation**: Now actually disables latest features (Poseidon, Think Deeper) and applies simpler UI automatically
- **Simpler UI Mode Fix**: Now properly hides non-essential buttons (Think Deeper, History, Customize, Help, Upgrade, Model Selector) and gem action buttons

### Notes
- **Stable Mode**: Automatically switches to simpler UI and disables Poseidon and Think Deeper features
- **Simpler UI**: Hides 6+ buttons for truly minimal interface
- **Light Mode Gradients**: Send button, sidebar elements, and interactive components now use purple/pink gradients

---

## 2025-12-18 (Major Algorithm Improvements)
- **Answer Cleanup**: Removed noisy `_Sources:_ …` lines and the `_Context-aware: follow-up detected` footer from responses so they read like natural replies instead of debug output.
- **Numeric Guardrail Tuning**: Adjusted the accuracy checker so casual queries (like “bye” or “learn sometimes”) no longer get an unnecessary numeric disclaimer, and the warning now only appears when numeric sentences are actually removed.
- **Small-Talk & Lite Mode Fixes**: Added quick paths for goodbyes and short nudges (“learn sometimes”) so they don’t trigger web search, and improved the lite `/api/chat` behavior for weather-style questions to explain limitations instead of parroting raw search snippets.

---

## 2025-12-15 (Final Update)
- **Poseidon Critical Fixes**: 
  - Fixed "service-not-allowed" error with proper secure context checking and recognition instance recreation
  - Improved error handling to prevent false error messages
  - Fixed trident icon rotation (180 degrees - was upside down)
  - Enhanced recognition restart logic for seamless conversation flow
- **Poseidon Folder Structure**: Created dedicated `/poseidon` folder with modular voice handler structure
- **Command Shortcuts**: Added `/office`, `/arcade`, and `/image {description}` commands for faster access
- **UI Improvements**:
  - Fixed floating sidebar toggle button styling (gradient blue button with proper shadows)
  - Added more gradients throughout UI (buttons, welcome title, etc.)
  - Enhanced dark mode with black background, gold/white/cream accents
  - Made "How to Use Atlas" help text more formal and professional
- **Settings Enhancements**:
  - Added **Stable Mode**: Access to older, thoroughly tested version (compromises latest features for stability)
  - Added **Simpler UI Mode**: Minimalist interface hiding non-essential elements for cleaner experience
- **Dark Mode Redesign**: Complete dark mode overhaul with black (#000000) background, gold (#FFD700) primary text, cream (#FFF8DC) secondary text, and enhanced gradients

### Notes
- **Poseidon Structure**: Voice assistant code organized in `/chatbot/poseidon/` folder
- **Stable Mode**: When enabled, page reloads to apply older version settings
- **Simpler UI**: Hides Think Deeper, History, and Customize buttons for minimal interface
- **Command Shortcuts**: `/office`, `/arcade`, `/image {desc}` work alongside natural language commands

---

## 2025-12-15 (Updated)
- **Poseidon Fixes**: Fixed critical speech recognition issues:
  - Changed to continuous recognition mode with interim results for better accuracy
  - Added explicit microphone permission request before starting recognition
  - Improved error handling to prevent false "trouble understanding" messages
  - Fixed recognition restart logic to automatically continue listening after responses
  - Better handling of no-speech and aborted states
- **Poseidon UI**: Updated button design with golden trident icon in round blue button (replacing microphone icon)
- **Text Refinement**: Added `_refine_large_text()` function to process large text chunks (>500 chars) by intelligently chunking sentences, extracting key information, and maintaining context for better model understanding
- **Error Handling**: Enhanced Poseidon error messages with specific guidance for different error types (no-speech, not-allowed, network, audio-capture)

### Notes
- **Continuous Recognition**: Poseidon now uses continuous mode for seamless conversation flow
- **Permission Flow**: Microphone permission is explicitly requested via `getUserMedia()` before starting recognition
- **Large Text**: Messages over 500 characters are automatically refined to extract key information while preserving context

---

## 2025-12-15
- **Gems UI**: Fixed gem sidebar layout — edit and delete buttons now work correctly and are aligned on the same line as gem names. Removed separate tone badge display; gem names now use metallic gradient colors based on tone (friendly=green, calm=blue, formal=purple, critical=red, normal=default). "New Gem" button is now properly center-aligned.
- **Poseidon Voice Assistant**: Added comprehensive voice assistant feature named "Poseidon" (Greek spelling) with full-screen overlay interface similar to Gemini Live. Features include:
  - **Live Voice Interaction**: Real-time speech recognition and text-to-speech responses
  - **Visual Feedback**: Animated waveform visualizer, status indicators (listening/speaking/ready), and live transcript display
  - **Voice Settings**: Configurable accents (US, UK, Australian, Indian English) and gender (Male/Female) in Settings modal
  - **Controls**: Hold/Pause and End buttons for session management
  - **Auto-restart**: Continuous listening mode that automatically restarts after responses
  - **Integration**: Fully integrated with existing chat API, supports all models (Thor 1.0 and Gems), tones, and features
- **Tone Enhancement**: Significantly strengthened tone impact on responses — each tone now includes "CRITICAL INSTRUCTION" directives to ensure consistent, pervasive application throughout entire responses.
- **UI Improvements**: Enhanced gem item wrapper structure for better event handling and visual consistency.

### Notes
- **Poseidon Launch**: Accessible via prominent "Poseidon" button in the input area (left side, before attach button)
- **Voice Browser Support**: Requires Chrome, Edge, or Safari (Web Speech API)
- **Gem Actions**: Edit/delete buttons now properly isolated from gem selection click events

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
