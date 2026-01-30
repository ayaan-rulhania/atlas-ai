# Atlas CLI - Quick Start Guide

## Installation

### Method 1: Homebrew (Once Published)

```bash
brew tap YOUR_USERNAME/tap
brew install atlas-cli
```

### Method 2: Local Development

```bash
cd /Users/arulhania/Coding/atlas-ai
python3 -m venv .venv-cli
source .venv-cli/bin/activate
pip install -r apps/cli/requirements.txt
pip install -e .
```

## Starting the Server

**IMPORTANT**: The CLI requires the Atlas AI server to be running first!

In one terminal:

```bash
cd /Users/arulhania/Coding/atlas-ai/apps/chatbot
python3 app.py
```

Wait until you see the server start message.

## Running the CLI

### With Virtual Environment

```bash
cd /Users/arulhania/Coding/atlas-ai
source .venv-cli/bin/activate
atlas-cli
```

### As Python Module

```bash
cd /Users/arulhania/Coding/atlas-ai
source .venv-cli/bin/activate
python -m apps.cli.atlas_cli
```

### After Homebrew Install

```bash
atlas-cli
```

## Basic Usage

### 1. Start the CLI

```bash
atlas-cli
```

You'll see:
- ASCII art banner (green ATLAS text)
- Connection status
- Current model (default: thor-1.1)
- Command prompt: `> `

### 2. Available Commands

#### List Models
```
/models
```
Shows all available models with descriptions and current selection.

#### Switch Model
```
/use thor-1.0
/use antelope-1.0
/use thor-calc-1.0
```
Switch to a specific model.

#### Enable Auto Mode
```
/auto
```
Enable intelligent model selection based on query type.

#### Show Status
```
/status
```
Display current server connection, model, and mode.

#### Clear Screen
```
/clear
```
Clear the terminal and re-display banner.

#### Help
```
/help
```
Show help message with all commands.

#### Exit
```
exit
quit
```
Or press `Ctrl+C` to exit.

### 3. Ask Questions

Just type your question:

```
> What is Python?
> Calculate 25 * 47
> How do I make an HTTP API call?
> import numpy as np
```

In auto mode, the CLI automatically selects:
- Math queries → `thor-calc-1.0`
- Python queries → `antelope-1.0`
- API/Code queries → `thor-lite-1.1`
- General queries → `thor-1.1`

## Example Session

```
$ atlas-cli

                                                    
  _|_|    _|_|_|_|_|  _|          _|_|      _|_|_|  
_|    _|      _|      _|        _|    _|  _|        
_|_|_|_|      _|      _|        _|_|_|_|    _|_|    
_|    _|      _|      _|        _|    _|        _|  
_|    _|      _|      _|_|_|_|  _|    _|  _|_|_|    

📡 Connected to http://localhost:5000
🤖 Model: thor-1.1

Enter your queries below. Type '/help' for commands, 'exit' or 'quit' to exit.

> /models
Available Models:
============================================================
→ thor-1.0               Stable model - reliable and proven (active)
  thor-1.1               Latest model - enhanced features and performance
  thor-lite-1.1           API/Code specialist - optimized for API calls and code generation
  thor-calc-1.0          Calculator specialist - optimized for mathematical calculations
  antelope-1.0           Python specialist - optimized for Python programming
  auto                   Auto mode - intelligently selects best model based on query
============================================================

Use '/use <model-name>' to switch models, or '/auto' for auto mode.

> /auto
✅ Auto mode enabled. Model will be selected based on query type.

> Calculate 123 + 456
🤔 Thinking (auto: thor-calc-1.0)...
[Response from thor-calc-1.0]

> What is machine learning?
🤔 Thinking (auto: thor-1.1)...
[Response from thor-1.1]

> /status
📊 CLI Status
============================================================
📡 Server: http://localhost:5000
   Status: ✅ Connected
🤖 Current Model: auto
   Mode: Auto (intelligent selection)
============================================================

> exit
Goodbye!
```

## Troubleshooting

### Server Not Running

If you see:
```
❌ Error: Atlas AI server is not running or not accessible.
```

**Solution**: Start the server first:
```bash
cd apps/chatbot && python3 app.py
```

### Connection Errors

**Check server is running**:
```bash
curl http://localhost:5000
```

**Check port 5000 is available**:
```bash
lsof -i :5000
```

### Model Not Found

If a model isn't available, you'll see a warning when switching. Use `/models` to see confirmed available models.

### Command Not Found (atlas-cli)

If installed via pip, make sure virtual environment is activated:
```bash
source .venv-cli/bin/activate
```

Or verify installation:
```bash
which atlas-cli
```

## Quick Reference Card

| Command | Description |
|---------|-------------|
| `/models` | List all available models |
| `/use <model>` | Switch to specific model |
| `/auto` | Enable auto mode |
| `/status` | Show current status |
| `/clear` | Clear screen |
| `/help` | Show help |
| `exit` or `quit` | Exit CLI |
| `Ctrl+C` | Force exit |

## Tips

1. **Use auto mode** for best results - it selects the right model automatically
2. **Check status** with `/status` if something seems wrong
3. **Clear screen** with `/clear` if output gets messy
4. **Model persists** across queries until you change it
5. **Server must run** - keep the server terminal open while using CLI
