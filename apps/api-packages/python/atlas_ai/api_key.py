"""
API Key management for Atlas AI SDK
"""

import requests
import secrets
import string
from typing import Optional
from .config import get_config


def generate_key(model: str, length: int = 24) -> str:
    """
    Generate a new API key for the specified model.

    Args:
        model: The model type ('thor-1.0', 'thor-1.1', 'thor-1.2', or 'antelope-1.1')
        length: Length of the random part of the key

    Returns:
        API key in format '{model}-{random_string}'

    Raises:
        ValueError: If model is not supported
    """
    allowed_models = ['thor-1.0', 'thor-1.1', 'thor-1.2', 'antelope-1.1']
    if model not in allowed_models:
        raise ValueError("Model must be 'thor-1.0', 'thor-1.1', 'thor-1.2', or 'antelope-1.1'")

    # Generate random alphanumeric string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))

    return f"{model}-{random_part}"


def register_key(key: str, base_url: Optional[str] = None) -> bool:
    """
    Register an API key with the Atlas AI backend.

    Args:
        key: The API key to register
        base_url: Base URL of the Atlas AI server (optional, uses config default)

    Returns:
        True if registration successful, False otherwise
    """
    if not base_url:
        base_url = get_config().get('base_url', 'http://localhost:5000')

    # Extract model from key (e.g. "thor-1.2-<random>")
    parts = key.split('-') if isinstance(key, str) else []
    if len(parts) < 3:
        return False

    model = '-'.join(parts[:2])
    allowed_models = ['thor-1.0', 'thor-1.1', 'thor-1.2', 'antelope-1.1']
    if model not in allowed_models:
        return False

    try:
        response = requests.post(
            f"{base_url}/api/keys/register",
            json={"key": key, "model": model},
            timeout=10
        )
        return response.status_code == 200 and response.json().get('success', False)
    except Exception:
        return False


def api(model: str, base_url: Optional[str] = None) -> str:
    """
    Generate and register a new API key, then log it to console.

    This is the main function for getting a new API key. It generates a key,
    registers it with the backend, and prints the key to console for copying.

    Args:
        model: The model type ('thor-1.0', 'thor-1.1', 'thor-1.2', or 'antelope-1.1')
        base_url: Base URL of the Atlas AI server (optional, uses config default)

    Returns:
        The generated API key

    Example:
        >>> key = api("thor-1.1")
        thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz
        >>> API_KEY = f"thor-1.1-{key.split('-')[-1]}"
    """
    key = generate_key(model)

    if register_key(key, base_url):
        print(key)  # Print to console as requested
        return key.split('-')[-1]  # Return just the random part
    else:
        raise RuntimeError("Failed to register API key with backend")
