"""
Calculator Service for Atlas AI Chatbot

This service provides integration between the Thor Calculator 1.0 model
and the Atlas AI chatbot application.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

# Setup paths for calculator integration
current_dir = Path(__file__).parent
atlas_root = current_dir.parent.parent

# Add calculator model to path
calc_model_path = atlas_root / "models" / "thor-calc-1.0"
if str(calc_model_path) not in sys.path:
    sys.path.insert(0, str(calc_model_path))

try:
    from thor_integration import ThorCalcIntegration, load_thor_calc_model
    CALCULATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Calculator model not available: {e}")
    CALCULATOR_AVAILABLE = False
    ThorCalcIntegration = None


class CalculatorService:
    """
    Calculator service for Atlas AI chatbot integration.

    This service provides mathematical calculation capabilities
    that can be used by the chatbot to handle math queries.
    """

    def __init__(self):
        """Initialize the calculator service."""
        self.calculator = None
        self.initialized = False

        if CALCULATOR_AVAILABLE:
            try:
                self.calculator = load_thor_calc_model()
                self.initialized = True
                print("✓ Calculator service initialized successfully")
            except Exception as e:
                print(f"✗ Failed to initialize calculator service: {e}")
                self.initialized = False
        else:
            print("✗ Calculator model not available")

    def is_available(self) -> bool:
        """Check if calculator service is available."""
        return self.initialized and CALCULATOR_AVAILABLE

    def process_math_query(self, query: str) -> Dict[str, Any]:
        """
        Process a mathematical query.

        Args:
            query: Mathematical query string

        Returns:
            Dictionary containing processing results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Calculator service is not available",
                "response": "Calculator functionality is currently unavailable."
            }

        try:
            return self.calculator.process_query(query)
        except Exception as e:
            print(f"Calculator service error: {e}")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": f"Calculator processing failed: {str(e)}",
                "response": "I encountered an error while processing your mathematical query."
            }

    def is_math_query(self, query: str) -> bool:
        """
        Determine if a query is mathematical.

        Args:
            query: Query string to check

        Returns:
            True if query appears to be mathematical
        """
        if not self.is_available():
            return False

        try:
            return self.calculator.is_math_query(query)
        except Exception:
            return False

    def get_calculator_info(self) -> Dict[str, Any]:
        """
        Get calculator service information.

        Returns:
            Dictionary with calculator capabilities and status
        """
        if not self.is_available():
            return {
                "available": False,
                "status": "unavailable",
                "error": "Calculator service not initialized"
            }

        try:
            return {
                "available": True,
                "status": "ready",
                "model_info": self.calculator.get_model_info(),
                "supported_operations": self.calculator.get_supported_operations()
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "error": str(e)
            }


# Global calculator service instance
_calculator_service = None

def get_calculator_service() -> CalculatorService:
    """
    Get the global calculator service instance.

    Returns:
        CalculatorService instance
    """
    global _calculator_service
    if _calculator_service is None:
        _calculator_service = CalculatorService()
    return _calculator_service


def process_calculator_query(query: str) -> Dict[str, Any]:
    """
    Process a calculator query using the service.

    Args:
        query: Mathematical query string

    Returns:
        Processing results
    """
    service = get_calculator_service()
    return service.process_math_query(query)


def is_calculator_query(query: str) -> bool:
    """
    Check if query should be handled by calculator.

    Args:
        query: Query string

    Returns:
        True if mathematical query
    """
    service = get_calculator_service()
    return service.is_math_query(query)


# Integration functions for Atlas chatbot
def handle_math_request(query: str) -> Optional[Dict[str, Any]]:
    """
    Handle mathematical requests in the Atlas chatbot.

    Args:
        query: User query

    Returns:
        Calculator response if mathematical, None otherwise
    """
    if is_calculator_query(query):
        return process_calculator_query(query)
    return None


if __name__ == "__main__":
    # Test calculator service
    print("Testing Calculator Service")
    print("=" * 30)

    service = get_calculator_service()

    if service.is_available():
        test_queries = [
            "what is 2 + 3",
            "calculate 10 * 5",
            "2 plus 3 times 4",
            "hello world"
        ]

        for query in test_queries:
            print(f"\nQuery: {query}")
            result = service.process_math_query(query)
            if result['success']:
                print(f"Response: {result['response']}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")

        print(f"\nService Info: {service.get_calculator_info()}")
    else:
        print("Calculator service is not available")