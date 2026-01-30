"""
Handle model loading errors gracefully and provide informative error messages.
This module provides error handling utilities for model loading operations.
"""

from typing import Dict, Optional, Any
import traceback
import sys


class ModelLoadingError(Exception):
    """Custom exception for model loading errors."""
    def __init__(self, model_name: str, message: str, error_type: str = "unknown", details: Optional[Dict] = None):
        self.model_name = model_name
        self.error_type = error_type
        self.details = details or {}
        super().__init__(message)


def handle_model_loading_error(
    model_name: str,
    error: Exception,
    loading_progress: Optional[Dict] = None,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Handle a model loading error and return a user-friendly error response.
    
    Args:
        model_name: Name of the model that failed to load
        error: The exception that occurred
        loading_progress: Current loading progress dict (if available)
        context: Additional context about the error
    
    Returns:
        Dictionary with error information including:
        - error: Error message
        - model_status: Status of the model
        - loading_progress: Progress percentage (even if failed)
        - error_type: Type of error
        - suggestion: Suggested action for user
    """
    # Determine error type
    error_type = "unknown"
    error_message = str(error)
    
    if "FileNotFoundError" in str(type(error)) or "file" in error_message.lower():
        error_type = "file_not_found"
    elif "MemoryError" in str(type(error)) or "memory" in error_message.lower() or "OOM" in error_message:
        error_type = "memory_error"
    elif "CUDA" in error_message or "cuda" in error_message.lower() or "gpu" in error_message.lower():
        error_type = "cuda_error"
    elif "import" in error_message.lower() or "ImportError" in str(type(error)):
        error_type = "import_error"
    elif "timeout" in error_message.lower() or "Timeout" in error_message:
        error_type = "timeout_error"
    elif "permission" in error_message.lower() or "Permission" in error_message:
        error_type = "permission_error"
    
    # Get progress if available
    progress = 0
    if loading_progress:
        progress = loading_progress.get('progress', 0)
    
    # Generate user-friendly error message
    base_error = f"Model {model_name} is not available. The model has not been loaded."
    
    # Generate suggestions based on error type
    suggestions = {
        "file_not_found": "Please check server logs and ensure the model files are present. Restart the server to load models.",
        "memory_error": "The model requires more memory than available. Try closing other applications or using a smaller model.",
        "cuda_error": "GPU/CUDA error detected. Check GPU availability and drivers. The model may fall back to CPU.",
        "import_error": "Required dependencies are missing. Check server logs and install missing packages.",
        "timeout_error": "Model loading timed out. The model may still be loading in the background. Please wait and try again.",
        "permission_error": "Permission denied accessing model files. Check file permissions and server logs.",
        "unknown": "Please check server logs and ensure the model files are present. Restart the server to load models."
    }
    
    suggestion = suggestions.get(error_type, suggestions["unknown"])
    
    # Always include progress percentage, even on error
    result = {
        "error": base_error,
        "model_status": "unavailable",
        "loading_progress": progress,
        "error_type": error_type,
        "error_message": error_message[:200],  # Truncate long error messages
        "suggestion": suggestion,
        "progress_percentage": f"{progress:.1f}%"
    }
    
    # Add context if provided
    if context:
        result["context"] = context
    
    return result


def get_error_progress_message(model_name: str, progress: float = 0) -> str:
    """
    Get a progress message even when there's an error.
    
    Args:
        model_name: Name of the model
        progress: Current progress percentage (0-100)
    
    Returns:
        Formatted progress message
    """
    if progress == 0:
        return f"Model {model_name} loading not started (0%)"
    elif progress < 100:
        return f"Model {model_name} loading failed at {progress:.1f}%"
    else:
        return f"Model {model_name} loading completed but failed to initialize"


def log_model_loading_error(
    model_name: str,
    error: Exception,
    loading_progress: Optional[Dict] = None
):
    """
    Log model loading error with full traceback.
    
    Args:
        model_name: Name of the model
        error: The exception that occurred
        loading_progress: Current loading progress dict (if available)
    """
    progress_info = ""
    if loading_progress:
        progress = loading_progress.get('progress', 0)
        status = loading_progress.get('status', 'unknown')
        progress_info = f" (Progress: {progress}%, Status: {status})"
    
    error_msg = f"[Model Loading Error] {model_name}{progress_info}\n"
    error_msg += f"Error: {str(error)}\n"
    error_msg += f"Type: {type(error).__name__}\n"
    error_msg += "Traceback:\n"
    error_msg += traceback.format_exc()
    
    print(error_msg, file=sys.stderr)
    
    # Optionally write to log file
    try:
        from config import DATA_ROOT
        log_file = DATA_ROOT / "logs" / "model_loading_errors.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"{error_msg}\n")
    except Exception:
        pass  # Don't fail if logging fails
