"""
Utility to run R scripts from Python.
This module provides functions to execute R scripts and retrieve their results.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
import tempfile


def run_r_script(
    script_path: str,
    function_name: str,
    args: Optional[Dict[str, Any]] = None,
    r_script_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Run an R script function and return the result.
    
    Args:
        script_path: Path to the R script file
        function_name: Name of the function to call
        args: Arguments to pass to the function
        r_script_dir: Directory containing R scripts (defaults to app_utils)
    
    Returns:
        Dictionary with the result, or None if execution failed
    """
    if r_script_dir is None:
        r_script_dir = Path(__file__).parent
    
    full_script_path = Path(r_script_dir) / script_path
    if not full_script_path.exists():
        return None
    
    # Create a temporary R script that sources the original and calls the function
    temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.r', delete=False)
    
    try:
        # Write the temporary R script
        temp_script.write(f'source("{full_script_path}")\n')
        
        # Prepare arguments
        if args:
            # Convert args to R syntax
            args_str = ', '.join([f'{k}={json.dumps(v)}' for k, v in args.items()])
            temp_script.write(f'result <- {function_name}({args_str})\n')
        else:
            temp_script.write(f'result <- {function_name}()\n')
        
        # Output result as JSON
        temp_script.write('cat(jsonlite::toJSON(result, auto_unbox=TRUE))\n')
        temp_script.close()
        
        # Run R script
        try:
            result = subprocess.run(
                ['Rscript', temp_script.name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse JSON output
                output = result.stdout.strip()
                if output:
                    return json.loads(output)
            else:
                print(f"[R Script Error] {result.stderr}", file=__import__('sys').stderr)
                return None
        except subprocess.TimeoutExpired:
            print(f"[R Script Error] Timeout executing R script", file=__import__('sys').stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"[R Script Error] Failed to parse JSON output: {e}", file=__import__('sys').stderr)
            return None
        except FileNotFoundError:
            # R not installed
            return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_script.name)
        except Exception:
            pass
    
    return None


def check_r_available() -> bool:
    """
    Check if R is available on the system.
    
    Returns:
        True if R is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['Rscript', '--version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def call_r_percent_load_calc(
    model_name: str,
    current_step: int = 0,
    total_steps: int = 100,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Call the R version of calculate_loading_percentage.
    
    Args:
        model_name: Name of the model
        current_step: Current loading step
        total_steps: Total number of steps
        **kwargs: Additional arguments
    
    Returns:
        Result dictionary or None if R is not available
    """
    if not check_r_available():
        return None
    
    args = {
        'model_name': model_name,
        'current_step': current_step,
        'total_steps': total_steps,
        **kwargs
    }
    
    return run_r_script('percent_load_calc.r', 'calculate_loading_percentage', args)


def call_r_error_handling(
    model_name: str,
    error: str,
    loading_progress: Optional[Dict] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Call the R version of handle_model_loading_error.
    
    Args:
        model_name: Name of the model
        error: Error message
        loading_progress: Loading progress dictionary
        **kwargs: Additional arguments
    
    Returns:
        Result dictionary or None if R is not available
    """
    if not check_r_available():
        return None
    
    args = {
        'model_name': model_name,
        'error': error,
        'loading_progress': loading_progress,
        **kwargs
    }
    
    return run_r_script('model_loading_error_handling.r', 'handle_model_loading_error', args)
