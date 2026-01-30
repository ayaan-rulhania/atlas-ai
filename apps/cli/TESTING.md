# Testing Atlas CLI Locally

This guide shows you how to test the Atlas CLI before releasing to Homebrew.

## Quick Test (Virtual Environment)

### 1. Create and activate virtual environment

```bash
cd /Users/arulhania/Coding/atlas-ai
python3 -m venv .venv-cli
source .venv-cli/bin/activate
```

### 2. Install dependencies and CLI

```bash
pip install --upgrade pip
pip install -r cli/requirements.txt
pip install -e .
```

### 3. Test the CLI

**Test help:**
```bash
atlas-cli --help
```

**Test banner display:**
```bash
python cli/test_banner.py
```

**Test with server (if running):**
```bash
# In one terminal, start the server:
cd chatbot && python3 app.py

# In another terminal, test the CLI:
source .venv-cli/bin/activate
atlas-cli
```

**Test without server (error handling):**
```bash
# Make sure server is NOT running, then:
atlas-cli
# Should show connection error message
```

## Alternative: Using pipx (Recommended for Testing)

If you have `pipx` installed (install with `brew install pipx`):

```bash
cd /Users/arulhania/Coding/atlas-ai
pipx install -e .
```

Then test:
```bash
atlas-cli --help
atlas-cli
```

## Testing Checklist

- [ ] Help command works (`atlas-cli --help`)
- [ ] Banner displays correctly with colors (blue globe, green ATLAS)
- [ ] Error message shows when server is not running
- [ ] CLI connects successfully when server is running
- [ ] Queries work and return responses
- [ ] Exit commands work (`exit`, `quit`, `Ctrl+C`)

## Testing the Full Flow

1. **Start the Atlas AI server:**
   ```bash
   cd chatbot
   python3 app.py
   ```

2. **In another terminal, test the CLI:**
   ```bash
   cd /Users/arulhania/Coding/atlas-ai
   source .venv-cli/bin/activate
   atlas-cli
   ```

3. **Try some queries:**
   ```
   > Hello, Atlas!
   > What is Python?
   > Explain quantum computing in simple terms
   ```

4. **Test exit:**
   ```
   > exit
   ```

## Troubleshooting

### "Command not found: atlas-cli"

Make sure you:
- Activated the virtual environment: `source .venv-cli/bin/activate`
- Installed the package: `pip install -e .`

### Banner colors not showing

- Make sure your terminal supports ANSI colors
- Try a different terminal (Terminal.app, iTerm2, etc.)
- Colors should work automatically with `colorama` installed

### Connection errors

- Verify server is running: `curl http://localhost:5000`
- Check server logs for errors
- Make sure no firewall is blocking port 5000

## Clean Up

To remove the test virtual environment:

```bash
rm -rf .venv-cli
```
