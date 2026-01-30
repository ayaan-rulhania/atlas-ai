/**
 * Configuration management for Atlas AI SDK
 */

const DEFAULT_CONFIG = {
  baseUrl: 'http://localhost:5000',
  timeout: 60000, // 60 seconds
  maxRetries: 3,
};

let config = { ...DEFAULT_CONFIG };

/**
 * Get the current configuration.
 *
 * @returns {Object} Configuration object
 */
function getConfig() {
  return { ...config };
}

/**
 * Set a configuration value.
 *
 * @param {string} key - Configuration key
 * @param {*} value - Configuration value
 */
function setConfig(key, value) {
  config[key] = value;
}

/**
 * Reset configuration to defaults.
 */
function resetConfig() {
  config = { ...DEFAULT_CONFIG };
}

/**
 * Load configuration from environment variables (Node.js only).
 */
function loadEnvConfig() {
  // Only works in Node.js environment
  if (typeof process !== 'undefined' && process.env) {
    const envMappings = {
      ATLAS_BASE_URL: 'baseUrl',
      ATLAS_TIMEOUT: 'timeout',
      ATLAS_MAX_RETRIES: 'maxRetries',
    };

    for (const [envVar, configKey] of Object.entries(envMappings)) {
      const value = process.env[envVar];
      if (value !== undefined) {
        // Convert string values to appropriate types
        if (['timeout', 'maxRetries'].includes(configKey)) {
          const numValue = parseInt(value, 10);
          if (!isNaN(numValue)) {
            setConfig(configKey, numValue);
          }
        } else {
          setConfig(configKey, value);
        }
      }
    }
  }
}

// Load environment configuration on initialization
loadEnvConfig();

module.exports = {
  getConfig,
  setConfig,
  resetConfig,
  loadEnvConfig,
};
