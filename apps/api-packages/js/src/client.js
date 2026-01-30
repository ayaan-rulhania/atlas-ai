/**
 * Atlas AI API client for making chat requests
 */

const { getConfig } = require('./config');

/**
 * Client for making API calls to Atlas AI.
 *
 * @example
 * const client = new AtlasClient("thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz");
 * const response = await client.call("Hello, how are you?");
 * console.log(response.response);
 */
class AtlasClient {
  /**
   * Initialize the Atlas AI client.
   *
   * @param {string} apiKey - Your API key (format: "thor-1.1-{random_string}")
   * @param {string} baseUrl - Base URL of the Atlas AI server (optional)
   */
  constructor(apiKey, baseUrl = null) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl || getConfig().baseUrl;
  }

  /**
   * Make a chat request to Atlas AI.
   *
   * @param {string} message - The message to send
   * @param {Object} options - Additional parameters (tone, model, think_deeper, etc.)
   * @returns {Promise<Object>} Response object containing the AI response
   * @throws {Error} If the API call fails
   */
  async call(message, options = {}) {
    return await call(message, this.apiKey, this.baseUrl, options);
  }
}

/**
 * Make a chat request to Atlas AI.
 *
 * This is a convenience function for making API calls without creating a client instance.
 *
 * @param {string} message - The message to send
 * @param {string} apiKey - Your API key
 * @param {string} baseUrl - Base URL of the Atlas AI server (optional)
 * @param {Object} options - Additional parameters (tone, model, think_deeper, etc.)
 * @returns {Promise<Object>} Response object containing the AI response
 * @throws {Error} If the API call fails
 *
 * @example
 * const response = await call("Hello!", "thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz");
 * console.log(response.response);
 */
async function call(message, apiKey, baseUrl = null, options = {}) {
  if (!baseUrl) {
    baseUrl = getConfig().baseUrl;
  }

  // Prepare request data
  const data = {
    message,
    api_key: apiKey,
    ...options
  };

  try {
    const response = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      return await response.json();
    } else if (response.status === 401) {
      throw new Error('Invalid API key');
    } else if (response.status === 429) {
      throw new Error('Rate limit exceeded');
    } else {
      const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      const errorMsg = errorData.error || `HTTP ${response.status}`;
      throw new Error(`API call failed: ${errorMsg}`);
    }
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Atlas AI server');
    }
    throw error;
  }
}

module.exports = {
  AtlasClient,
  call,
};
