"""
Model management for Atlas CLI - handles model selection, listing, and auto-mode logic
"""

import re
from typing import Dict, List, Optional, Tuple


class ModelManager:
    """
    Manages model selection, auto-mode, and model availability for the CLI.
    """
    
    # Available models with descriptions
    MODEL_DESCRIPTIONS = {
        "thor-1.0": "Stable model - reliable and proven",
        "thor-1.1": "Latest model - enhanced features and performance",
        "thor-lite-1.1": "API/Code specialist - optimized for API calls and code generation",
        "thor-calc-1.0": "Calculator specialist - optimized for mathematical calculations",
        "antelope-1.0": "Python specialist - optimized for Python programming",
        "auto": "Auto mode - intelligently selects best model based on query",
    }
    
    # Models that are confirmed supported by the API
    CONFIRMED_MODELS = ["thor-1.0", "thor-1.1", "antelope-1.0"]
    
    # All available models (including potentially unsupported ones)
    ALL_MODELS = ["thor-1.0", "thor-1.1", "thor-lite-1.1", "thor-calc-1.0", "antelope-1.0", "auto"]
    
    def __init__(self, default_model: str = "thor-1.1"):
        """
        Initialize the model manager.
        
        Args:
            default_model: Default model to use (default: thor-1.1)
        """
        self.current_model = default_model
        self.auto_mode_enabled = False
        self.available_models: List[str] = []
    
    def set_available_models(self, models: List[str]):
        """
        Set the list of available models from the API.
        
        Args:
            models: List of model names that are available from the API
        """
        self.available_models = models
        # Always include "auto" as it's a CLI feature
        if "auto" not in self.available_models:
            self.available_models.append("auto")
    
    def get_current_model(self) -> str:
        """
        Get the current selected model.
        
        Returns:
            Current model name
        """
        return self.current_model
    
    def is_auto_mode(self) -> bool:
        """
        Check if auto mode is enabled.
        
        Returns:
            True if auto mode is enabled, False otherwise
        """
        return self.auto_mode_enabled or self.current_model == "auto"
    
    def set_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Set the current model.
        
        Args:
            model_name: Name of the model to set
        
        Returns:
            Tuple of (success, message)
        """
        model_name_lower = model_name.lower().strip()
        
        # Handle auto mode
        if model_name_lower == "auto":
            self.auto_mode_enabled = True
            self.current_model = "auto"
            return True, "Auto mode enabled. Model will be selected based on query type."
        
        # Validate model name
        if model_name_lower not in self.ALL_MODELS:
            available = ", ".join(self.ALL_MODELS)
            return False, f"Unknown model: {model_name}. Available models: {available}"
        
        # Check if model is available (warn if not confirmed)
        if model_name_lower not in self.CONFIRMED_MODELS and model_name_lower != "auto":
            warning = f"Warning: {model_name} may not be fully supported by the API yet."
        else:
            warning = None
        
        # Set the model
        self.current_model = model_name_lower
        self.auto_mode_enabled = False
        
        msg = f"Switched to model: {model_name_lower}"
        if warning:
            msg += f"\n   {warning}"
        
        return True, msg
    
    def get_model_for_query(self, query: str) -> str:
        """
        Get the appropriate model for a given query.
        If auto mode is enabled, selects model based on query content.
        Otherwise, returns the current model.
        
        Args:
            query: The user's query string
        
        Returns:
            Model name to use for the query
        """
        if not self.is_auto_mode():
            return self.current_model
        
        # Auto mode: analyze query and select appropriate model
        return self._select_model_auto(query)
    
    def _select_model_auto(self, query: str) -> str:
        """
        Automatically select the best model based on query content.
        
        Args:
            query: The user's query string
        
        Returns:
            Selected model name
        """
        query_lower = query.lower()
        
        # Math/Calculator detection
        math_keywords = [
            "calculate", "math", "equation", "solve", "formula", "derivative",
            "integral", "sum", "multiply", "divide", "square root", "logarithm",
            "trigonometry", "algebra", "calculus", "geometry", "percentage",
            "fraction", "decimal", "number", "numeric", "computation"
        ]
        math_operators = ["+", "-", "*", "/", "=", "^", "√", "∫", "∑"]
        
        if any(keyword in query_lower for keyword in math_keywords):
            return "thor-calc-1.0"
        if any(op in query for op in math_operators):
            return "thor-calc-1.0"
        
        # Python-specific detection
        python_keywords = [
            "python", "pip", "import", ".py", "pypi", "pythonic", "django",
            "flask", "numpy", "pandas", "python code", "python script",
            "python function", "python class", "python module", "python package"
        ]
        
        if any(keyword in query_lower for keyword in python_keywords):
            return "antelope-1.0"
        
        # API/Code detection
        api_keywords = [
            "api", "http", "rest", "endpoint", "request", "response", "fetch",
            "curl", "postman", "webhook", "graphql", "json", "xml", "soap",
            "authentication", "authorization", "oauth", "jwt", "token",
            "endpoint", "route", "controller", "service", "microservice"
        ]
        code_keywords = [
            "code", "function", "method", "class", "variable", "script",
            "programming", "developer", "software", "application"
        ]
        
        if any(keyword in query_lower for keyword in api_keywords):
            return "thor-lite-1.1"
        if any(keyword in query_lower for keyword in code_keywords):
            return "thor-lite-1.1"
        
        # Default: use thor-1.1 for general queries
        return "thor-1.1"
    
    def list_models(self) -> List[Dict[str, str]]:
        """
        Get a list of all available models with descriptions.
        
        Returns:
            List of dictionaries with model info (name, description, status)
        """
        models = []
        for model_name in self.ALL_MODELS:
            description = self.MODEL_DESCRIPTIONS.get(model_name, "No description available")
            
            # Determine status
            if model_name == self.current_model:
                if self.is_auto_mode():
                    status = "active (auto mode)"
                else:
                    status = "active"
            elif model_name in self.CONFIRMED_MODELS:
                status = "available"
            elif model_name == "auto":
                status = "available"
            else:
                status = "may require backend support"
            
            models.append({
                "name": model_name,
                "description": description,
                "status": status
            })
        
        return models
    
    def format_models_list(self) -> str:
        """
        Format the models list as a string for display.
        
        Returns:
            Formatted string listing all models
        """
        models = self.list_models()
        lines = ["\nAvailable Models:"]
        lines.append("=" * 60)
        
        for model in models:
            name = model["name"]
            desc = model["description"]
            status = model["status"]
            
            # Highlight current model
            if "active" in status:
                name_display = f"→ {name}"
                color = '\033[32m'  # Green
                reset = '\033[0m'
            else:
                name_display = f"  {name}"
                color = ''
                reset = ''
            
            line = f"{color}{name_display:<20} {desc}{reset}"
            if status != "available":
                line += f" ({status})"
            lines.append(line)
        
        lines.append("=" * 60)
        lines.append("\nUse '/use <model-name>' to switch models, or '/auto' for auto mode.\n")
        
        return "\n".join(lines)
