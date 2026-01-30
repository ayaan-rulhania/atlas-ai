"""Utility functions for the chatbot application (app_utils to avoid conflict with thor-1.1/utils)."""
from .math_evaluator import safe_evaluate_math
from .path_manager import PathManager
from .percent_load_calc import (
    calculate_loading_percentage,
    get_default_loading_steps,
    interpolate_progress
)
from .model_loading_error_handling import (
    handle_model_loading_error,
    get_error_progress_message,
    log_model_loading_error,
    ModelLoadingError
)
from .r_script_runner import (
    run_r_script,
    check_r_available,
    call_r_percent_load_calc,
    call_r_error_handling
)

__all__ = [
    'safe_evaluate_math',
    'PathManager',
    'calculate_loading_percentage',
    'get_default_loading_steps',
    'interpolate_progress',
    'handle_model_loading_error',
    'get_error_progress_message',
    'log_model_loading_error',
    'ModelLoadingError',
    'run_r_script',
    'check_r_available',
    'call_r_percent_load_calc',
    'call_r_error_handling'
]

