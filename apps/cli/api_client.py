"""
API client for communicating with Atlas AI server
"""

import requests
from typing import Dict, Any, Optional, List


class AtlasAPIClient:
    """
    Client for making API calls to the local Atlas AI server.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the Atlas AI server (default: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/chat"
        self.model_status_endpoint = f"{self.base_url}/api/model/status"
        self.model = "thor-1.1"  # Default model
    
    def check_connection(self) -> bool:
        """
        Check if the server is running and accessible.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            # Try to connect to the server (any endpoint will do)
            response = requests.get(f"{self.base_url}/", timeout=2)
            
            # Check if it's the simple mock server
            if response.status_code < 500:
                # Check /api/health endpoint to see server type
                try:
                    health = requests.get(f"{self.base_url}/api/health", timeout=2)
                    if health.status_code == 200:
                        health_data = health.json()
                        if health_data.get('server') == 'simple':
                            return False  # Signal that it's the wrong server
                except Exception:
                    pass
            
            return response.status_code < 500  # Any response means server is up
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False
        except Exception:
            return False
    
    def set_model(self, model_name: str):
        """
        Set the model to use for queries.
        
        Args:
            model_name: Name of the model to use
        """
        self.model = model_name
    
    def get_current_model(self) -> str:
        """
        Get the current model being used.
        
        Returns:
            Current model name
        """
        return self.model
    
    def get_available_models(self) -> List[str]:
        """
        Fetch available models from the API.
        
        Returns:
            List of available model names
        
        Raises:
            ConnectionError: If server is not reachable
            RuntimeError: If API call fails
        """
        if not self.check_connection():
            raise ConnectionError(
                f"Could not connect to Atlas AI server at {self.base_url}.\n"
                f"Please make sure the server is running on port 5000."
            )
        
        try:
            response = requests.get(self.model_status_endpoint, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Extract available models from API response
                available = data.get("available_models", [])
                # Always ensure we have at least the confirmed models
                if not available:
                    available = ["thor-1.0", "thor-1.1", "antelope-1.0"]
                return available
            else:
                # Fallback to default models if endpoint fails
                return ["thor-1.0", "thor-1.1", "antelope-1.0"]
                
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            # Fallback to default models on any error
            return ["thor-1.0", "thor-1.1", "antelope-1.0"]
    
    def query(self, message: str, model: Optional[str] = None, timeout: int = 60) -> Dict[str, Any]:
        """
        Send a query to the Atlas AI server.
        
        Args:
            message: The user's query message
            model: Model to use (overrides current model if provided)
            timeout: Request timeout in seconds (default: 60)
        
        Returns:
            Response dictionary containing the AI response
        
        Raises:
            ConnectionError: If server is not reachable
            RuntimeError: If API call fails or returns an error
        """
        # Check connection first
        if not self.check_connection():
            raise ConnectionError(
                f"Could not connect to Atlas AI server at {self.base_url}.\n"
                f"Please make sure the server is running on port 5000.\n"
                f"Start it with: cd apps/chatbot && python3 app.py"
            )
        
        # Use provided model or current model
        model_to_use = model if model else self.model
        
        # Prepare request data
        data = {
            "message": message,
            "model": model_to_use,
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=data,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if we're hitting the simple mock server
                response_text = result.get('response', '')
                if 'simple server without ML models' in response_text.lower():
                    raise RuntimeError(
                        "❌ Error: Connected to simple mock server instead of full Atlas AI server.\n"
                        "   The server running is 'simple_server.py' which doesn't have ML models.\n\n"
                        "   Please stop the current server and start the full server:\n"
                        "   cd apps/chatbot && python3 app.py\n\n"
                        "   The full server will load and use the actual ML models."
                    )
                
                return result
            elif response.status_code == 401:
                raise RuntimeError("Invalid API key (if using API key authentication)")
            elif response.status_code == 429:
                raise RuntimeError("Rate limit exceeded. Please wait a moment before trying again.")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', f'HTTP {response.status_code}')
                raise RuntimeError(f"API call failed: {error_msg}")
                
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out after {timeout} seconds. The server may be processing a complex query.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Atlas AI server at {self.base_url}.\n"
                f"Please make sure the server is running on port 5000."
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")
