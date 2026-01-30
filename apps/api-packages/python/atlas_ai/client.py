"""
Atlas AI API client for making chat requests
"""

import requests
from typing import Dict, Any, Optional, Union
from .config import get_config


class AtlasClient:
    """
    Client for making API calls to Atlas AI.

    Example:
        >>> client = AtlasClient("thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz")
        >>> response = client.call("Hello, how are you?")
        >>> print(response["response"])
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize the Atlas AI client.

        Args:
            api_key: Your API key (format: "thor-1.1-{random_string}")
            base_url: Base URL of the Atlas AI server (optional)
        """
        self.api_key = api_key
        self.base_url = base_url or get_config().get('base_url', 'http://localhost:5000')

    def call(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Make a chat request to Atlas AI.

        Args:
            message: The message to send
            **kwargs: Additional parameters (tone, model, think_deeper, etc.)

        Returns:
            Response dictionary containing the AI response

        Raises:
            RuntimeError: If the API call fails
        """
        return call(message, self.api_key, self.base_url, **kwargs)


def call(
    message: str,
    api_key: str,
    base_url: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Make a chat request to Atlas AI.

    This is a convenience function for making API calls without creating a client instance.

    Args:
        message: The message to send
        api_key: Your API key
        base_url: Base URL of the Atlas AI server (optional)
        **kwargs: Additional parameters (tone, model, think_deeper, etc.)

    Returns:
        Response dictionary containing the AI response

    Raises:
        RuntimeError: If the API call fails

    Example:
        >>> response = call("Hello!", "thor-1.1-AbCdEfGhIjKlMnOpQrStUvWxYz")
        >>> print(response["response"])
    """
    if not base_url:
        base_url = get_config().get('base_url', 'http://localhost:5000')

    # Prepare request data
    data = {
        "message": message,
        "api_key": api_key,
        **kwargs
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=data,
            timeout=60  # Longer timeout for AI responses
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise RuntimeError("Invalid API key")
        elif response.status_code == 429:
            raise RuntimeError("Rate limit exceeded")
        else:
            error_data = response.json()
            error_msg = error_data.get('error', f'HTTP {response.status_code}')
            raise RuntimeError(f"API call failed: {error_msg}")

    except requests.RequestException as e:
        raise RuntimeError(f"Network error: {e}")
