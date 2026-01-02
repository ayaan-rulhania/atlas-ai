"""
Configuration management for Atlas AI SDK
"""

import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    'base_url': 'http://localhost:5000',
    'timeout': 60,
    'max_retries': 3
}

_config = DEFAULT_CONFIG.copy()


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        Dictionary containing configuration values
    """
    return _config.copy()


def set_config(key: str, value: Any) -> None:
    """
    Set a configuration value.

    Args:
        key: Configuration key
        value: Configuration value
    """
    _config[key] = value


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = DEFAULT_CONFIG.copy()


# Load configuration from environment variables
def _load_env_config():
    """Load configuration from environment variables."""
    env_mappings = {
        'ATLAS_BASE_URL': 'base_url',
        'ATLAS_TIMEOUT': 'timeout',
        'ATLAS_MAX_RETRIES': 'max_retries'
    }

    for env_var, config_key in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if config_key in ['timeout', 'max_retries']:
                try:
                    value = int(value)
                except ValueError:
                    continue
            set_config(config_key, value)


# Load environment configuration on import
_load_env_config()
