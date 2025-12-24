# Atlas AI - Comprehensive Documentation

## 🚀 Overview

Atlas AI is a sophisticated AI assistant platform powered by **Thor 1.1** (latest) with **Thor 1.0** available in stable mode. The platform provides a unified chat interface, continuous learning capabilities, and advanced features for knowledge management and conversation handling.

**Latest Updates (Version 1.3.3 - 2025-12-26):**
- ✅ Cross-chat memory system - Atlas remembers your preferences and information across all chats
- ✅ Enhanced command system - Added /help, /clear, /remember, /forget, /info, /think, /tone commands
- ✅ Improved "How to use Atlas" pop-up - Beautifully redesigned with comprehensive sections
- ✅ Fixed gems localStorage saving - Gems now properly cached for faster loading
- ✅ Major Hindi language enhancements - Advanced text processing, better voice selection, optimized speech
- ✅ Enhanced common sense prioritization - Better reasoning before web searches for natural conversation
- ✅ Thor 1.1 released with enhanced model architecture and improved inference
- ✅ Poseidon voice assistant with comprehensive multi-language support

## 📁 Project Structure

```
atlas-ai/
├── chatbot/                # Main Flask app (UI + API)
│   ├── app.py              # Main server (serves UI + /api/chat)
│   ├── ui/                 # Frontend (templates + static)
│   ├── refinement/         # Refinement + accuracy checks
│   ├── handlers/           # Image + markdown helpers
│   ├── gems/               # Gems store (custom sub-models)
│   └── thor_result_setter_server.py  # Optional result-setter tool (port 5004)
├── thor-1.0/               # Thor 1.0 model (stable mode)
├── thor-1.1/               # Thor 1.1 model (latest, default)
├── trainx/                 # TrainX tooling (Q/A and image pairs)
├── brain/                  # Knowledge store
├── training_data/          # Training datasets
├── VERSION.MD              # Major change log (keep updated)
└── requirements.txt
```

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.8+** (Python 3.14 recommended)
- **pip** (Python package manager)
- **Virtual environment** support (venv)

### Step-by-Step Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/arulhania/Coding/atlas-ai
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. **Upgrade pip and install dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python3 -c "import torch; import flask; print('Dependencies installed successfully')"
   ```

## 🚀 Running the Servers

### Starting All Servers

The platform consists of three main servers:

#### 1. Main Chatbot Server (Port 5000)
```bash
cd /Users/arulhania/Coding/atlas-ai/chatbot
../.venv/bin/python3 app.py
```

**Access:** http://localhost:5000

**Features:**
- Unified chat interface for Thor 1.0
- Conversation history management
- Project management
- Image processing
- Continuous learning integration

#### 2. Thor Result Setter Server (Port 5004)
```bash
cd /Users/arulhania/Coding/atlas-ai/chatbot
../.venv/bin/python3 thor_result_setter_server.py
```

**Access:** http://localhost:5004

**Features:**
- Manual Q&A pair entry
- TrainX compilation support
- Edit, delete, and search curated responses
- Data stored in: `chatbot/thor_result_setter.json`

### Starting All Servers at Once

Create a startup script (`start_all_servers.sh`):

```bash
#!/bin/bash
cd /Users/arulhania/Coding/atlas-ai

# Activate virtual environment
source .venv/bin/activate

# Start Chatbot Server
cd chatbot
python3 app.py > ../logs/chatbot.log 2>&1 &
CHATBOT_PID=$!
echo "Chatbot started (PID: $CHATBOT_PID)"

# Start Thor Result Setter
python3 thor_result_setter_server.py > ../logs/thor_result_setter.log 2>&1 &
THOR_PID=$!
echo "Thor Result Setter started (PID: $THOR_PID)"

echo ""
echo "All servers started!"
echo "Chatbot: http://localhost:5000"
echo "Thor Result Setter: http://localhost:5004"
echo ""
echo "To stop all servers: kill $CHATBOT_PID $THOR_PID"
```

Make it executable:
```bash
chmod +x start_all_servers.sh
```

## 🎯 Key Features

### 1. Model Support

- **Thor 1.1**: Latest model with enhanced features (default)
- **Thor 1.0**: Stable model with proven reliability (used in stable mode)
- **Gems**: Custom sub-models that you can create, customize, and use for specialized tasks
  - **Try Before Create**: Test gem configurations without saving
  - **Custom Instructions**: Define how each gem should behave
  - **Tone Control**: Set tone (Normal, Friendly, Calm, Formal, Critical) for consistent style with enhanced impact on responses
  - **Source Integration**: Add links and files as knowledge sources that are prioritized over web search
  - **One-Line Management**: View and manage gems in the sidebar with metallic-colored gem names (based on tone) and edit/delete actions on the same line

### 2. Continuous Learning

- **Auto-Trainer**: Automatically trains on conversations every 30 minutes
- **Brain System**: Organized knowledge storage by letter/keyword
- **Research Engine**: Web search integration for unknown topics
- **Learning Tracker**: Monitors and records learning progress

### 3. TrainX Language

A domain-specific language for defining Q&A pairs with advanced features:

#### Basic Syntax:
```trainx
Q: What is Python?
A: Python is a high-level programming language known for its simplicity and readability.
```

#### Alias Syntax (Alternative Question Phrasing):
```trainx
Q: {"What is Python?" / "Tell me about Python" / "Python info"}?
A: Python is a high-level programming language known for its simplicity and readability.
```

This generates three Q&A pairs:
- Q: "What is Python?" → A: [answer]
- Q: "Tell me about Python" → A: [answer]
- Q: "Python info" → A: [answer]

The first alias is treated as canonical for internal reference.

#### Image Syntax (Q (Image)):
```trainx
Q (Image): Thor
A: https://upload.wikimedia.org/wikipedia/en/3/3c/Chris_Hemsworth_as_Thor.jpg
```

- The question is stored as `Create an image of Thor` for clarity.
- The pair is tagged as `type: image` and the Result Setter renders an
  iframe + still preview from the URL.
- Aliases work too: `Q (Image): {"puppy" / "dog"}` will generate image
  pairs for each alias.

### 4. Result Setter System

- **Authoritative Answers**: Pre-set responses for specific questions
- **Fuzzy Matching**: Handles variations in question phrasing
- **TrainX Integration**: Bulk import via TrainX compilation
- **Manual Management**: Web interface for editing Q&A pairs

### 5. Conversation Management

- **Chat History**: All conversations saved in `chatbot/chats/`
- **Conversation Archive**: Backup copies in `chatbot/conversations/`
- **Project Organization**: Group related chats into projects
- **History Tracking**: Comprehensive history system

### 6. Gems (Custom Sub-Models)

Gems allow you to create specialized AI assistants tailored to specific tasks or domains:

- **Create Gems**: Define custom instructions, tone, and knowledge sources
- **Try Before Save**: Test gem configurations without committing
- **Source Integration**: 
  - Add **links** (up to 5 URLs) — automatically fetched and parsed for content
  - Add **files** (up to 10 text files) — uploaded content used as context
  - Gem sources are **always prioritized** over web search results
- **Tone Control**: Choose from Normal, Friendly, Calm, Formal, or Critical tones
- **Model Dropdown**: Select gems from the model selector alongside Thor 1.0
- **Sidebar Management**: View all gems with name, tone badge, and quick edit/delete actions

**Example Use Cases:**
- **Study Buddy**: Explains concepts step-by-step, then quizzes you
- **Product Manager**: Turns ideas into PRDs, risks, and roadmaps
- **Design Critic**: Provides direct UI/UX critique with actionable fixes
- **Custom Domain Expert**: Add specialized knowledge via sources for domain-specific assistance

### 7. Command Shortcuts

For faster access to common features, use these command shortcuts:
- `/office` - Opens the Office Suite interface
- `/arcade` - Opens the Game Suite interface
- `/image {description}` - Generates an image based on description (e.g., `/image beautiful sunset`)

These commands work alongside natural language requests (e.g., "Load Office Suite" still works).

### 8. Poseidon Voice Assistant

Poseidon is a comprehensive voice assistant feature that provides live, conversational interactions similar to Gemini Live:

- **Live Voice Interaction**: Real-time speech recognition and text-to-speech responses
- **Full-Screen Interface**: Immersive overlay with visual feedback
  - Animated waveform visualizer that responds to listening/speaking states
  - Status indicators (Ready/Listening/Speaking/Processing)
  - Live transcript display for both user input and assistant responses
- **Voice Customization**: Configure in Settings modal
  - **Accents**: US English, UK English, Australian English, Indian English
  - **Gender**: Male or Female voices
  - Settings persist across sessions
- **Session Controls**:
  - **Hold/Pause**: Temporarily pause listening and speaking
  - **End**: Close Poseidon and return to text chat
- **Auto-Continuation**: Automatically restarts listening after each response for seamless conversation flow
- **Full Integration**: Works with all models (Thor 1.0 and Gems), tones, Think Deeper mode, and all existing features

**Access**: Click the golden trident icon button (round blue button) in the input area (left side, before the attach button)

**Browser Support**: Requires Chrome, or Edge

**Features**:
- **Continuous Recognition**: Automatically continues listening after each response
- **Permission Handling**: Explicitly requests microphone permission before starting
- **Error Recovery**: Intelligent error handling with automatic retry for common issues
- **Large Text Support**: Backend automatically refines large text chunks for better understanding
- **Secure Context**: Automatically checks for HTTPS/localhost and provides helpful error messages
- **Fast Response**: Optimized for speed with reduced delays (300ms restart, 50ms auto-restart)
- **Backend Validation**: Comprehensive checks for browser support, secure context, and DOM elements

**Command Shortcuts**:
- `/office` - Quickly open Office Suite
- `/arcade` - Quickly open Game Suite  
- `/image {description}` - Generate an image (e.g., `/image sunset over mountains`)

**Settings Options**:
- **Stable Mode**: Disables latest features (Poseidon, Think Deeper) and automatically applies simpler UI for maximum stability. Uses Thor 1.0 model.
- **Simpler UI Mode**: Minimalist interface hiding non-essential buttons (Think Deeper, History, Customize, Help, Upgrade, Model Selector) for a cleaner experience

**Troubleshooting Poseidon**:
- If you see "Service Unavailable", check browser microphone permissions
- Circuit breaker automatically stops infinite error loops
- Browser-specific guidance is provided in error messages
- Requires HTTPS or localhost for security
- Supported browsers: Chrome, Edge

### 9. Advanced Features

- **Think Deeper Mode**: Enhanced reasoning for complex queries
- **Image Processing**: Upload and analyze images with support for style/angle/color tweaks
- **Code Mode**: Specialized code assistance
- **Semantic Relevance**: Intelligent knowledge filtering
- **Response Cleaning**: Automatic response validation and cleaning
- **Enhanced Tone Impact**: Tones now have significantly stronger, more consistent impact on response style and content

### 10. Easter Egg

Type exactly `"I am in C5."` in the chat interface to trigger a celebratory animation! 🎉

## 📚 API Endpoints

### Chatbot Server (Port 5000)

- `GET /` - Main chat interface
- `POST /api/chat` - Send chat message
- `GET /api/chats` - List all chats
- `GET /api/chats/<chat_id>` - Get specific chat
- `DELETE /api/chats/<chat_id>` - Delete chat
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/history` - Get history
- `GET /api/model/status` - Check model status
- `GET /api/gems` - List all gems
- `POST /api/gems` - Create a new gem
- `GET /api/gems/<gem_id>` - Get specific gem
- `PUT /api/gems/<gem_id>` - Update gem
- `DELETE /api/gems/<gem_id>` - Delete gem

### Result Setter Servers (Ports 5004 & 5005)

- `GET /` - Result setter interface
- `GET /api/qa/list` - List all Q&A pairs
- `POST /api/qa/add` - Add new Q&A pair
- `POST /api/qa/update` - Update existing Q&A pair
- `POST /api/qa/delete` - Delete Q&A pair
- `POST /api/qa/search` - Search Q&A pairs
- `POST /api/trainx/compile` - Compile TrainX code

## 🔧 Configuration

### Model Configuration

**Thor 1.0:** `thor-1.0/config/config.yaml`

### Chatbot Configuration

Configuration is managed in `chatbot/app.py`:
- Model directories
- Chat storage paths
- Result setter file paths
- Port settings

### Environment Variables

Create a `.env` file in the root directory (optional):
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
MODEL_PATH=path/to/models
```

## 🧠 Brain System

The Brain System organizes knowledge by letters and keywords:

```
brain/
├── A/
│   └── keywords.json
├── B/
│   └── keywords.json
...
└── Z/
    └── keywords.json
```

Each `keywords.json` contains:
- Letter identifier
- Keywords list
- Knowledge entries with content, source, and timestamps
- Last updated timestamp

## 📝 TrainX Language Reference

### Basic Q&A Block
```trainx
Q: Your question here?
A: Your answer here.
```

### List Declaration
```trainx
List myList = [
    "key1": "value1",
    "key2": "value2"
]
```

### Alias Syntax
```trainx
Q: {"Canonical Question" / "Alias 1" / "Alias 2"}?
A: Single answer for all variations.
```

### Comments
```trainx
# This is a comment
Q: Question?
A: Answer.
```

## 📄 License

This project is released under the **Atlas AI Internal Use License**
(`LICENSE` in the repo root). In short: internal evaluation and research
use are allowed; redistribution, commercial hosting, or model-training
derivatives outside this project are prohibited without written
permission. See the full LICENSE text for all terms, conditions,
limitations, and warranty disclaimers.

## 🐛 Troubleshooting

### Server Won't Start

1. **Check if port is in use:**
   ```bash
   lsof -i :5000  # For chatbot
   lsof -i :5004  # For Thor result setter
   ```

2. **Kill existing processes:**
   ```bash
   pkill -f "app.py"
   pkill -f "result_setter_server"
   ```

3. **Check virtual environment:**
   ```bash
   source .venv/bin/activate
   which python3  # Should point to .venv/bin/python3
   ```

### Import Errors

1. **Verify sys.path setup:**
   - Check that `thor-1.0` is added before `odin-0.5` in sys.path
   - Verify all required modules exist

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Model Loading Issues

1. **Check model files exist:**
   ```bash
   ls -la thor-1.0/models/final_model.pt
   ls -la thor-1.0/models/tokenizer.json
   ```

2. **Verify config paths:**
   - Check `config/config.yaml` exists
   - Verify paths in `app.py` are correct

### Conversation Not Saving

1. **Check directory permissions:**
   ```bash
   ls -la chatbot/chats/
   ls -la chatbot/conversations/
   ```

2. **Verify directory creation:**
   - Directories should be created automatically
   - Check logs for permission errors

## 📊 Monitoring & Logs

### Log Locations

- **Chatbot:** `/tmp/chatbot.log` or `logs/chatbot.log`
- **Thor Result Setter:** `/tmp/thor_result_setter.log` or `logs/thor_result_setter.log`

### Viewing Logs

```bash
# Real-time log viewing
tail -f /tmp/chatbot.log

# Last 50 lines
tail -50 /tmp/chatbot.log

# Search for errors
grep -i error /tmp/chatbot.log
```

## 🔒 Security Considerations

1. **Development Server Warning:**
   - Flask's development server is NOT suitable for production
   - Use a production WSGI server (Gunicorn, uWSGI) for deployment

2. **Secret Key:**
   - Change `app.secret_key` in production
   - Use environment variables for sensitive data

3. **CORS:**
   - Currently allows all origins (`CORS(app)`)
   - Restrict in production: `CORS(app, origins=["https://yourdomain.com"])`

## 🚀 Deployment

### Production Setup

1. **Use Production WSGI Server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set Environment Variables:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-production-secret-key
   ```

3. **Use Process Manager:**
   - **systemd** (Linux)
   - **supervisor**
   - **PM2** (Node.js process manager)

### Docker Deployment (Future)

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "chatbot.app:app"]
```

## 🤝 Contributing

1. Follow the existing code structure
2. Add comments for complex logic
3. Update documentation for new features
4. Test changes thoroughly before committing

## 📄 License
This software is Proprietary and Confidential (P&C). The Licensor grants the 
Licensee a limited, non-exclusive, and non-transferable right to Use the compiled, 
object-code version of this software solely for its intended purpose. The Licensee
is strictly prohibited from accessing, viewing, copying, distributing, or 
modifying the Source Code. Furthermore, the Licensee shall not reverse engineer, 
decompile, or disassemble the software, nor shall they distribute, sublicense, or 
publicly display the software or any derivative works. All rights, title, and 
intellectual property ownership remain solely with the Licensor.

## 📞 Support

For issues, questions, or contributions:
- Check the troubleshooting section
- Review logs for error messages
- Verify all dependencies are installed
- Ensure virtual environment is activated

## 🔄 Version History

- **v1.0.2** – Major algorithm improvements: Gems now intelligently synthesize sources instead of reading verbatim, Thor search results are properly synthesized from multiple sources, improved intent detection to avoid treating commands as search queries, and removed hardcoded context labels.
- **v1.0.1** – Refinement pass for responses (removed debug-style footers like `_Sources:_ …` and `_Context-aware: follow-up detected`, and made small-talk/goodbye handling less likely to trigger web search).
- **v1.0.0** – Initial release with Thor 1.0
  - TrainX alias syntax support
  - Continuous learning system
  - Result setter integration

---

**Last Updated:** December 18, 2025
**Maintained by:** Atlas AI Development Team