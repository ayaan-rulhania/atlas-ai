# Atlas CLI

A simple, elegant command-line interface for Atlas AI. Query multiple models directly from your terminal with a beautiful ASCII art interface.

## Features

- 🎨 Beautiful ASCII art banner (green ATLAS text)
- 🤖 Multiple model support with intelligent selection
- 🔌 Connects to local Atlas AI server (port 5000)
- 🎯 Support for 6 models: thor-1.0, thor-1.1, thor-lite-1.1, thor-calc-1.0, antelope-1.0, and auto mode
- 🔄 Easy model switching during sessions
- ✨ Clean, minimal user experience

## Installation

### Via Homebrew (Recommended)

```bash
brew install atlas-cli
```

### Manual Installation

1. **Prerequisites:**
   - Python 3.8 or higher
   - Atlas AI server running on `localhost:5000`

2. **Install dependencies:**
   ```bash
   pip install -r cli/requirements.txt
   ```

3. **Install the CLI:**
   ```bash
   pip install -e .
   ```

   Or from the project root:
   ```bash
   python setup.py install
   ```

## Usage

### Starting the CLI

Simply run:

```bash
atlas-cli
```

This will:
1. Display the ASCII art banner (ATLAS)
2. Check if the server is running
3. Load available models from the API
4. Start an interactive query session (default: thor-1.1)

### Available Models

The CLI supports the following models:

- **thor-1.0**: Stable model - reliable and proven
- **thor-1.1**: Latest model - enhanced features and performance (default)
- **thor-lite-1.1**: API/Code specialist - optimized for API calls and code generation (400M parameters)
- **thor-calc-1.0**: Calculator specialist - optimized for mathematical calculations
- **antelope-1.0**: Python specialist - optimized for Python programming
- **auto**: Auto mode - intelligently selects best model based on query type

### Commands

#### List Available Models

```
/models
```

This displays all available models with descriptions and shows which one is currently active.

#### Switch Models

```
/use <model-name>
```

Switch to a specific model. Examples:
```
/use thor-1.0
/use antelope-1.0
/use thor-calc-1.0
```

#### Enable Auto Mode

```
/auto
```

Enable auto mode for intelligent model selection. The CLI will automatically select the best model based on your query:
- Math/calculator queries → `thor-calc-1.0`
- API/code/HTTP queries → `thor-lite-1.1`
- Python-specific queries → `antelope-1.0`
- General queries → `thor-1.1`

#### Querying

Once the CLI is running, simply type your questions:

```
> What is Python?
> Calculate 25 * 47
> How do I make an API call?
> import numpy as np
```

In auto mode, the CLI will automatically select the appropriate model for each query.

#### Getting Help

```
/help
```

Or use the command-line flag:
```bash
atlas-cli --help
```

#### Exiting

- Type `exit` or `quit` to exit gracefully
- Press `Ctrl+C` to interrupt and exit

## Requirements

### Server

The CLI requires the Atlas AI server to be running on `localhost:5000`. 

To start the server:

```bash
cd apps/chatbot
python3 app.py
```

The server should be accessible at `http://localhost:5000`.

### Python Dependencies

- `requests` - HTTP client for API calls
- `pyfiglet` - ASCII text generation (fallback available)
- `colorama` - Cross-platform colored terminal output

These are automatically installed when installing via Homebrew or pip.

## Configuration

The CLI connects to `http://localhost:5000` by default. This cannot be changed from the command line in the current version.

### Model Selection

The CLI starts with `thor-1.1` as the default model. You can:

1. **Switch models manually**: Use `/use <model-name>` to switch to a specific model
2. **Use auto mode**: Use `/auto` to enable intelligent model selection
3. **View available models**: Use `/models` to see all models and their descriptions

### Auto Mode Behavior

When auto mode is enabled, the CLI analyzes your query and selects the best model:

- **Math/Calculator queries**: Detects keywords like "calculate", "math", "equation", "+", "-", etc. → uses `thor-calc-1.0`
- **Python queries**: Detects keywords like "python", "pip", "import", ".py", etc. → uses `antelope-1.0`
- **API/Code queries**: Detects keywords like "API", "HTTP", "endpoint", "REST", "code", etc. → uses `thor-lite-1.1`
- **General queries**: Everything else → uses `thor-1.1`

## Troubleshooting

### Server Not Running

If you see an error about the server not being accessible:

```
❌ Error: Atlas AI server is not running or not accessible.
```

Make sure:
1. The Atlas AI server is running: `cd apps/chatbot && python3 app.py`
2. The server is accessible at `http://localhost:5000`
3. No firewall is blocking the connection

### Connection Errors

If you encounter connection errors:
- Check that port 5000 is not in use by another application
- Verify the server is running: `curl http://localhost:5000`
- Check server logs for errors

### ASCII Art Not Displaying

If ASCII art doesn't display correctly:
- Ensure your terminal supports ANSI color codes
- Try a different terminal (Terminal.app, iTerm2, etc.)
- On Windows, ensure `colorama` is installed

## Development

### Running from Source

```bash
# From project root
python -m apps.cli.atlas_cli
```

Or:
```bash
cd apps/cli
python -m atlas_cli
```

### Building for Homebrew

1. Create a release tarball:
   ```bash
   tar -czf atlas-cli-0.1.0.tar.gz --exclude='.git' --exclude='__pycache__' .
   ```

2. Upload to GitHub releases

3. Update the `url` and `sha256` in `Formula/atlas-cli.rb`

4. Test the formula:
   ```bash
   brew install --build-from-source ./Formula/atlas-cli.rb
   ```

## License

MIT License - see LICENSE file in project root.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md in the project root.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
