/**
 * Atlas AI JavaScript SDK
 *
 * A simple JavaScript package for generating API keys and making calls to Atlas AI models.
 */

const { api, generateKey, registerKey } = require('./api-key');
const { call, AtlasClient } = require('./client');
const { getConfig, setConfig } = require('./config');

module.exports = {
  api,
  call,
  generateKey,
  registerKey,
  AtlasClient,
  getConfig,
  setConfig
};

// ES module exports for modern environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports.default = module.exports;
}

// For browsers and ES modules
if (typeof window !== 'undefined') {
  window.AtlasAI = module.exports;
}
