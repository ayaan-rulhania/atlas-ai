"""
Calculate model loading percentage based on various factors.
This module provides functions to calculate and track model loading progress.
"""

from typing import Dict, Optional, Tuple
import time


def calculate_loading_percentage(
    model_name: str,
    start_time: Optional[float] = None,
    current_step: int = 0,
    total_steps: int = 100,
    file_size_loaded: int = 0,
    total_file_size: int = 0,
    memory_used: int = 0,
    total_memory_required: int = 0
) -> Dict[str, any]:
    """
    Calculate model loading percentage based on multiple factors.
    
    Args:
        model_name: Name of the model being loaded
        start_time: Timestamp when loading started (optional)
        current_step: Current loading step (0-based)
        total_steps: Total number of loading steps
        file_size_loaded: Bytes of model files loaded so far
        total_file_size: Total bytes of model files to load
        memory_used: Memory currently used for loading (bytes)
        total_memory_required: Total memory required (bytes)
    
    Returns:
        Dictionary with progress information including:
        - progress: Percentage (0-100)
        - status: Current status string
        - message: Detailed message
        - estimated_time_remaining: Estimated seconds remaining (if start_time provided)
    """
    # Calculate progress from different factors
    step_progress = (current_step / total_steps * 100) if total_steps > 0 else 0
    file_progress = (file_size_loaded / total_file_size * 100) if total_file_size > 0 else 0
    memory_progress = (memory_used / total_memory_required * 100) if total_memory_required > 0 else 0
    
    # Weighted average (step progress is most reliable)
    if total_steps > 0:
        progress = step_progress
    elif total_file_size > 0:
        progress = file_progress
    elif total_memory_required > 0:
        progress = memory_progress
    else:
        progress = 0
    
    # Ensure progress is between 0 and 100
    progress = max(0, min(100, progress))
    
    # Calculate estimated time remaining if start_time is provided
    estimated_time_remaining = None
    if start_time and progress > 0:
        elapsed_time = time.time() - start_time
        if progress < 100:
            estimated_total_time = elapsed_time / (progress / 100)
            estimated_time_remaining = max(0, estimated_total_time - elapsed_time)
    
    # Generate status message
    if progress == 0:
        status = "not_started"
        message = f"Model {model_name} loading not started"
    elif progress < 25:
        status = "initializing"
        message = f"Initializing {model_name}... ({progress:.1f}%)"
    elif progress < 50:
        status = "loading"
        message = f"Loading {model_name} weights... ({progress:.1f}%)"
    elif progress < 75:
        status = "loading"
        message = f"Loading {model_name} components... ({progress:.1f}%)"
    elif progress < 100:
        status = "finalizing"
        message = f"Finalizing {model_name}... ({progress:.1f}%)"
    else:
        status = "loaded"
        message = f"Model {model_name} loaded successfully"
    
    result = {
        "progress": round(progress, 2),
        "status": status,
        "message": message,
        "step_progress": round(step_progress, 2),
        "file_progress": round(file_progress, 2),
        "memory_progress": round(memory_progress, 2),
        "current_step": current_step,
        "total_steps": total_steps
    }
    
    if estimated_time_remaining is not None:
        result["estimated_time_remaining"] = round(estimated_time_remaining, 2)
    
    return result


def get_default_loading_steps(model_name: str) -> int:
    """
    Get default number of loading steps for a model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        Default number of steps for the model
    """
    # Different models may have different loading steps
    step_map = {
        "thor-1.0": 5,
        "thor-1.1": 8,
        "thor-1.2": 8,  # same as thor-1.1 (qwen3-thor)
        "qwen3-thor": 10,
        "antelope-1.0": 5,
        "antelope-1.1": 5
    }
    return step_map.get(model_name.lower(), 10)


def interpolate_progress(
    previous_progress: float,
    current_progress: float,
    time_elapsed: float,
    smoothing_factor: float = 0.3
) -> float:
    """
    Smooth progress updates to avoid jittery progress bars.
    
    Args:
        previous_progress: Previous progress percentage
        current_progress: Current progress percentage
        time_elapsed: Time elapsed since last update (seconds)
        smoothing_factor: Smoothing factor (0-1), higher = more smoothing
    
    Returns:
        Smoothed progress percentage
    """
    # Exponential moving average
    smoothed = previous_progress * (1 - smoothing_factor) + current_progress * smoothing_factor
    return max(previous_progress, smoothed)  # Never go backwards
