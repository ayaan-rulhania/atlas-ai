# Atlas AI — Version Log

This file tracks **major changes** made to this project over time.

## Format
- **Date**: YYYY-MM-DD
- **Summary**: 1–3 bullets describing what changed and why
- **Notes** (optional): migrations, breaking changes, ports, flags

---

## 2025-12-26 (Version 1.3.3 - Major Enhancements Update)
- **Cross-Chat Memory System**: Implemented comprehensive user memory system that stores preferences, facts, and conversation topics across all chats
  - Automatically extracts user preferences from conversations (likes, dislikes, interests, profession, location)
  - Injects relevant user context into queries for personalized responses
  - Commands: `/remember <info>` to save information, `/forget` to clear memory, `/info` to see what Atlas knows about you
- **Enhanced Command System**: Added comprehensive command shortcuts for better user experience
  - `/help` - Show detailed help with all available commands
  - `/clear` - Clear current chat
  - `/remember <information>` - Save information for future reference
  - `/forget` - Clear saved preferences and memory
  - `/info` - Display what Atlas knows about the user
  - `/think` - Toggle Think Deeper mode
  - `/tone <style>` - Set response tone (friendly, calm, formal, critical, normal)
- **Improved Help Modal**: Complete redesign of "How to use Atlas" pop-up with beautiful formatting
  - Comprehensive sections: Getting Started, Quick Commands, Features & Tips, Best Practices
  - Better visual design with icons, code blocks, and improved readability
  - More detailed explanations and actionable tips
- **Gems localStorage Fix**: Fixed gems not being saved in localStorage
  - Gems now cached in localStorage for instant display on page load
  - Automatic cache updates after create, update, or delete operations
  - Fallback to cached gems if API fails for better offline experience
- **Major Hindi Language Enhancements**: Comprehensive improvements to Hindi support in Poseidon
  - Advanced Hindi text processing with Devanagari script handling
  - Enhanced voice selection with prioritization of Neural/Wavenet Hindi voices
  - Optimized speech synthesis with proper pitch, rate, and punctuation handling
  - Explicit Hindi language settings for recognition (hi-IN)
  - Better Hindi transcript processing and normalization
  - Detailed Hindi-specific logging and debugging
- **Enhanced Common Sense Prioritization**: Improved reasoning before web searches
  - Expanded common sense patterns to skip unnecessary searches
  - Better handling of math questions, time/date queries, and conversational statements
  - Prioritizes common sense responses before triggering web research
  - Enhanced common sense handler with more intelligent detection

### Notes
- **User Memory**: Stored in `user_memory.json`, automatically extracts and saves user information from conversations
- **Commands**: All new commands work alongside existing `/office`, `/arcade`, `/image` commands
- **Hindi Support**: Optimized for Devanagari script, includes proper punctuation handling and voice selection
- **Common Sense**: Reduces unnecessary web searches for questions that can be answered with common knowledge

---

## 2025-12-19 (Thor 1.1 Release & Poseidon Circuit Breaker - Major Update)
- **Thor 1.1 Release**: Created Thor 1.1 as the latest model with enhanced features, defaulting to Thor 1.1 for all new conversations
  - Enhanced model architecture: 1024 hidden size, 16 layers, 16 attention heads, 1024 max position embeddings
  - Improved inference with temperature sampling and top-k filtering for better text generation
  - Enhanced training configuration with better hyperparameters
- **Stable Mode Support**: Thor 1.0 is automatically used when stable mode is enabled via main Atlas page settings
- **Base Knowledge Import**: Thor 1.1 imports base knowledge from Thor 1.0, ensuring backward compatibility and knowledge continuity
- **Result Setter & Image Mapping**: Updated all references from Thor 1.0 to Thor 1.1, with separate files for each version
- **Poseidon Critical Fixes**:
  - **Circuit Breaker**: Added intelligent circuit breaker to prevent infinite error loops (stops after 5 rapid errors in 3 seconds)
  - **Improved Error Handling**: Enhanced service-not-allowed error handling with browser-specific guidance
  - **Better State Management**: Fixed overlay visibility detection using multiple methods to ensure poseidonActive is set correctly
  - **Enhanced Debugging**: Added comprehensive console logging for what Poseidon hears (🎤 [Poseidon HEARD] logs)
  - **User-Friendly Error Messages**: Browser-specific troubleshooting guidance for Chrome, Edge, and Safari

### Notes
- **Model Selection**: System automatically uses Thor 1.1 by default, switches to Thor 1.0 in stable mode
- **File Structure**: Created `thor-1.1/` directory with all services, `thor_1_1_result_setter.json`, and `thor_1_1_image_setter.json`
- **Backward Compatibility**: Thor 1.0 remains fully functional and is used in stable mode
- **Knowledge Base**: Thor 1.1 result setter automatically imports Q&A pairs from Thor 1.0 for base knowledge
- **Poseidon Circuit Breaker**: Prevents infinite error loops by automatically stopping retry attempts after detecting rapid failures
- **Git Repository**: Local git repository exists but no remote URL configured
- **Vercel Deployment**: Configuration file exists at `chatbot/vercel.json` for serverless deployment

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

## 2025-12-18 (Major Conversational Context Algorithm - Complete Overhaul)
- **Conversational Context Analyzer**: Implemented comprehensive conversational context understanding system that distinguishes between literal queries and conversational statements. Detects semantic relationships between user messages and previous assistant responses (e.g., "I came back" responding to "come back any time").
- **Context-Aware Response Generation**: Added intelligent response generation for conversational statements that maintains natural dialogue flow without hardcoding specific phrases. Handles acknowledgments, return statements, agreements, thanks, and casual remarks conversationally.
- **Semantic Relationship Detection**: Enhanced system to detect semantic relationships between messages using pattern matching and word overlap analysis, preventing conversational statements from being treated as literal search queries.
- **Early Context Analysis**: Conversational context is analyzed before search/knowledge retrieval, preventing unnecessary web searches for conversational statements and maintaining natural conversation flow.

---

## 2025-12-18 (Comprehensive Reasoning Improvements - Major Update)
- **Enhanced Goodbye Detection**: Implemented comprehensive pattern matching for farewells (bye, goodbye, see you, later, etc.) with context-aware detection that prevents false positives in questions. Handles variations like "goodnight", "ttyl", "take care", etc.
- **Improved Non-Question Detection**: Added intelligent detection for statements, commands, and casual remarks (like "learn sometimes!") that shouldn't trigger web search, with pattern-based matching for exclamations and short statements.
- **Answer Synthesis Improvements**: Enhanced knowledge synthesis to remove source attribution lines (Sources:, Model:, Context-aware:, etc.) that made responses look like raw debug output. Improved sentence extraction and content processing for gem sources and research results.
- **Gem Source Processing**: Ensured gem sources are always intelligently synthesized rather than read verbatim, with better extraction of key sentences and removal of promotional content and source metadata.
- **Research Result Processing**: Improved synthesis function to better handle factual queries (like weather) by removing source metadata and extracting meaningful content instead of returning raw search snippets.
- **Context-Aware Message Cleanup**: Removed all instances of "Context-aware: follow-up detected" and similar debug messages from responses.

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

### Notes
- **Port override**: server can be started with `PORT=5001 ...` (defaults to 5000)

---

## 2025-12-07
- **Cleanup**: Removed all Odin 0.5 references and the `/odin-0.5` directory; simplified to a single-model (Thor 1.0) architecture.
- **Frontend**: Updated UI templates/components to remove Odin selection and align copy, docs, and routing to Thor-only.
