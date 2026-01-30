# Atlas AI Python SDK

The simplest way to use Atlas AI in Python.

This SDK talks to a running Atlas AI server and requires an API key registered with that server.

## Installation

```bash
pip install atlas-ai
```

## Quick Start

### Generate an API key + make a call
```python
from atlas_ai import api, call

# Generate and register a key for Thor 1.2 (recommended default)
key_suffix = api("thor-1.2")  # prints full key to console
API_KEY = f"thor-1.2-{key_suffix}"

response = call("Hello, how are you?", API_KEY)
print(response["response"])
```

### Using the client class
```python
from atlas_ai import AtlasClient

client = AtlasClient(API_KEY)
response = client.call("What is the capital of France?")
print(response["response"])
```

## Core API

### `atlas_ai.api(model, base_url=None)`
Generate and register a new API key (prints full key; returns the random suffix).

### `atlas_ai.call(message, api_key, base_url=None, **options)`
Send a message to the AI and return the response as a dictionary.

**Returns:** A JSON-like dict (typically includes `response`)

### Selecting a model

Pass `model="thor-1.2"` (or `"thor-1.0"`, `"thor-1.1"`, `"antelope-1.1"`) as an option:

```python
response = call("Hello", API_KEY, model="thor-1.2")
print(response["response"])
```

## Available Models

- **thor-1.2**: Latest model (default server-side)
- **thor-1.1**: Legacy model (still supported)
- **thor-1.0**: Stable model
- **antelope-1.1**: Optional alternate model (if enabled on your server)

## API Summary

- `atlas_ai.api(model)` - Generate + register a key (prints full key; returns suffix)
- `atlas_ai.call(message, api_key, base_url?, **options)` - Make a chat request
- `atlas_ai.AtlasClient(api_key, base_url?)` - Reusable client

Tip: set `ATLAS_BASE_URL` via `atlas_ai.set_config('base_url', 'http://localhost:5000')` if your server runs on a different URL.

## Examples

### Basic Usage
```python
from atlas_ai import api, call

key_suffix = api("thor-1.2")
API_KEY = f"thor-1.2-{key_suffix}"

response = call("How are you?", API_KEY)
print(f"AI said: {response['response']}")
```

### Multiple Messages
```python
from atlas_ai import call

messages = ["Hello", "How are you?", "Tell me about AI"]
for msg in messages:
    print(f"You: {msg}")
    resp = call(msg, API_KEY)
    print(f"Atlas: {resp['response']}\n")
```

## Requirements

- Python 3.8+
- Running Atlas AI server

## License

MIT License
