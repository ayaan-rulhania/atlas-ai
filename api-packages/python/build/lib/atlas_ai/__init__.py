"""
Atlas AI Python SDK

A simple Python package for generating API keys and making calls to Atlas AI models.
"""

from .api_key import api, generate_key, register_key
from .client import call, AtlasClient
from .config import get_config, set_config

__version__ = "1.0.0"
__all__ = [
    "api",
    "call",
    "generate_key",
    "register_key",
    "AtlasClient",
    "get_config",
    "set_config"
]
