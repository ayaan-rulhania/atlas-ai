# Atlas AI JavaScript SDK

A simple JavaScript package for generating API keys and making calls to Atlas AI models.

## Installation

```bash
npm install atlas-ai-sdk
```

## Quick Start

### Generate an API Key

```javascript
const { api } = require('atlas-ai');

// Generate and register a key for Thor 1.1
const keySuffix = await api('thor-1.1');
// This will print: thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz

// Use the key in your code
const API_KEY = `thor-1.1-${keySuffix}`;
```

### Make API Calls

```javascript
const { call } = require('atlas-ai');

// Simple API call
const response = await call('Hello, how are you?', API_KEY);
console.log(response.response);

// Advanced API call with options
const response = await call('Explain quantum computing', API_KEY, null, {
  tone: 'formal',
  think_deeper: true
});
console.log(response.response);
```

### Using the Client Class

```javascript
const { AtlasClient } = require('atlas-ai');

// Create a client
const client = new AtlasClient(API_KEY);

// Make calls
const response = await client.call('What is the capital of France?');
console.log(response.response);

const response = await client.call('Write a poem about AI', { tone: 'creative' });
console.log(response.response);
```

## ES Modules

```javascript
import { api, call, AtlasClient } from 'atlas-ai';

// Generate key
const keySuffix = await api('thor-1.1');
const API_KEY = `thor-1.1-${keySuffix}`;

// Make calls
const response = await call('Hello!', API_KEY);
console.log(response.response);
```

## Browser Usage

```html
<!DOCTYPE html>
<html>
<head>
  <title>Atlas AI Demo</title>
</head>
<body>
  <script type="module">
    import { api, call } from './node_modules/atlas-ai/src/index.js';

    // Note: For browser usage, you may need to set up CORS on your Atlas AI server
    // and use HTTPS in production

    async function init() {
      try {
        const keySuffix = await api('thor-1.1');
        const API_KEY = `thor-1.1-${keySuffix}`;

        const response = await call('Hello from browser!', API_KEY);
        console.log(response.response);
      } catch (error) {
        console.error('Error:', error);
      }
    }

    init();
  </script>
</body>
</html>
```

## API Reference

### Functions

#### `api(model, baseUrl?)`
Generate and register a new API key.

- `model`: `"thor-1.0"` or `"thor-1.1"`
- `baseUrl`: Optional base URL (defaults to `http://localhost:5000`)
- Returns: Promise<string> - The random part of the API key

#### `call(message, apiKey, baseUrl?, options?)`
Make a chat API call.

- `message`: The message to send (string)
- `apiKey`: Your API key (string)
- `baseUrl`: Optional base URL
- `options`: Additional parameters like `tone`, `model`, `think_deeper`, etc.
- Returns: Promise<Object> - Response object

### Classes

#### `AtlasClient(apiKey, baseUrl?)`
Client class for making multiple API calls.

- `apiKey`: Your API key
- `baseUrl`: Optional base URL

##### Methods

###### `call(message, options?)`
Make a chat API call.

- Same parameters as the `call()` function

## Configuration

You can configure the SDK using environment variables (Node.js):

```bash
export ATLAS_BASE_URL="https://your-atlas-server.com"
export ATLAS_TIMEOUT=120000
```

Or programmatically:

```javascript
const { setConfig } = require('atlas-ai');

setConfig('baseUrl', 'https://your-atlas-server.com');
setConfig('timeout', 120000);
```

## Error Handling

```javascript
try {
  const response = await call('Hello!', API_KEY);
} catch (error) {
  console.error('API call failed:', error.message);
}
```

Common errors:
- `"Invalid API key"`: The API key is not registered or invalid
- `"Rate limit exceeded"`: Too many requests
- `"Network error"`: Connection issues

## Requirements

- Node.js 14+ or modern browser with fetch support
- No external dependencies (uses built-in fetch)

## License

MIT License
