# Atlas AI API Packages

This repository contains installable Python and JavaScript packages that allow developers worldwide to easily integrate Atlas AI into their applications.

## Overview

The Atlas AI API packages provide:
- **API Key Generation**: Generate and register API keys for Atlas AI models
- **Simple API Calls**: Make chat requests to Thor 1.0 and Thor 1.1 models
- **Easy Installation**: Install via pip/npm from anywhere in the world
- **Developer Friendly**: Simple interfaces with comprehensive error handling

## Packages

### Python Package (`python/`)
- **Installation**: `pip install atlas-ai-thor-20251231`
- **Features**: Full Python SDK with type hints and async support
- **Requirements**: Python 3.8+, requests library

### JavaScript Package (`js/`)
- **Installation**: `npm install atlas-ai-sdk`
- **Features**: Works in Node.js and browsers (with fetch support)
- **Requirements**: Node.js 14+ or modern browser

## Quick Start Examples

### Python

```python
from atlas_ai import api, call

# Generate API key
key_suffix = api("thor-1.1")  # Prints: thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz
API_KEY = f"thor-1.1-{key_suffix}"

# Make API call
response = call("Hello, how are you?", api_key=API_KEY)
print(response["response"])
```

### JavaScript (Node.js)

```javascript
const { api, call } = require('atlas-ai');

// Generate API key
async function init() {
  const keySuffix = await api('thor-1.1'); // Prints: thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz
  const API_KEY = `thor-1.1-${keySuffix}`;

  // Make API call
  const response = await call('Hello, how are you?', API_KEY);
  console.log(response.response);
}

init();
```

### JavaScript (ES Modules/Browser)

```javascript
import { api, call } from 'atlas-ai';

// Generate API key
const keySuffix = await api('thor-1.1');
const API_KEY = `thor-1.1-${keySuffix}`;

// Make API call
const response = await call('Hello, how are you?', API_KEY);
console.log(response.response);
```

## Supported Models

- **Thor 1.0**: Stable, production-ready model
- **Thor 1.1**: Latest model with enhanced capabilities

## API Key Management

API keys are generated in the format `{model}-{random_string}`:
- `thor-1.0-AbCdEfGhIjKlMnOpQrStUvWxYz`
- `thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz`

Keys are automatically registered with the Atlas AI backend when generated.

## Configuration

### Environment Variables

**Python:**
```bash
export ATLAS_BASE_URL="https://your-atlas-server.com"
export ATLAS_TIMEOUT=120
```

**JavaScript (Node.js):**
```bash
export ATLAS_BASE_URL="https://your-atlas-server.com"
export ATLAS_TIMEOUT=120000
```

### Programmatic Configuration

**Python:**
```python
from atlas_ai import set_config
set_config('base_url', 'https://your-atlas-server.com')
```

**JavaScript:**
```javascript
const { setConfig } = require('atlas-ai');
setConfig('baseUrl', 'https://your-atlas-server.com');
```

## Error Handling

Both packages provide clear error messages:

- `Invalid API key`: Key not registered or malformed
- `Rate limit exceeded`: Too many requests
- `Network error`: Connection issues

## Development

### Building Python Package

```bash
cd python
python setup.py sdist bdist_wheel
pip install -e .
```

### Building JavaScript Package

```bash
cd js
npm install
npm test  # (when tests are added)
npm publish  # (when ready)
```

## Backend Requirements

These packages require an Atlas AI server running with:

- `/api/keys/register` endpoint (POST)
- `/api/keys/validate` endpoint (GET)
- `/api/chat` endpoint (POST) with optional `api_key` parameter

## Package Names & Versions

- **Python**: `atlas-ai-thor-20251231` v1.0.0
- **JavaScript**: `atlas-ai-sdk` v1.0.0

## License

MIT License - See individual package READMEs for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- **Issues**: Create GitHub issues for bugs/features
- **Documentation**: Check individual package READMEs
- **Examples**: See usage examples in package READMEs
