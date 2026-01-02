/**
 * API Key management for Atlas AI SDK
 */

const { getConfig } = require('./config');

/**
 * Generate a new API key for the specified model.
 *
 * @param {string} model - The model type ('thor-1.0' or 'thor-1.1')
 * @param {number} length - Length of the random part of the key
 * @returns {string} API key in format '{model}-{random_string}'
 * @throws {Error} If model is not supported
 */
function generateKey(model, length = 24) {
  if (!['thor-1.0', 'thor-1.1'].includes(model)) {
    throw new Error("Model must be 'thor-1.0' or 'thor-1.1'");
  }

  // Generate random alphanumeric string
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let randomPart = '';
  for (let i = 0; i < length; i++) {
    randomPart += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
  }

  return `${model}-${randomPart}`;
}

/**
 * Register an API key with the Atlas AI backend.
 *
 * @param {string} key - The API key to register
 * @param {string} baseUrl - Base URL of the Atlas AI server (optional)
 * @returns {Promise<boolean>} True if registration successful, false otherwise
 */
async function registerKey(key, baseUrl = null) {
  if (!baseUrl) {
    baseUrl = getConfig().baseUrl;
  }

  // Extract model from key
  if (!key || !key.includes('-')) {
    return false;
  }

  const model = key.split('-', 1)[0];
  if (!['thor-1.0', 'thor-1.1'].includes(model)) {
    return false;
  }

  try {
    const response = await fetch(`${baseUrl}/api/keys/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ key, model }),
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.success === true;
  } catch (error) {
    console.error('Error registering API key:', error);
    return false;
  }
}

/**
 * Generate and register a new API key, then log it to console.
 *
 * This is the main function for getting a new API key. It generates a key,
 * registers it with the backend, and prints the key to console for copying.
 *
 * @param {string} model - The model type ('thor-1.0' or 'thor-1.1')
 * @param {string} baseUrl - Base URL of the Atlas AI server (optional)
 * @returns {Promise<string>} The random part of the generated API key
 * @throws {Error} If registration fails
 *
 * @example
 * const keySuffix = await api('thor-1.1');
 * // Logs: thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz
 * const API_KEY = `thor-1.1-${keySuffix}`;
 */
async function api(model, baseUrl = null) {
  const key = generateKey(model);

  if (await registerKey(key, baseUrl)) {
    console.log(key); // Print to console as requested
    return key.split('-').pop(); // Return just the random part
  } else {
    throw new Error('Failed to register API key with backend');
  }
}

module.exports = {
  generateKey,
  registerKey,
  api,
};
