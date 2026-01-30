# Handle model loading errors gracefully and provide informative error messages.
# This R script provides error handling utilities for model loading operations.

handle_model_loading_error <- function(
  model_name,
  error,
  loading_progress = NULL,
  context = NULL
) {
  #' Handle a model loading error and return a user-friendly error response.
  #'
  #' @param model_name Name of the model that failed to load
  #' @param error The error message or exception that occurred
  #' @param loading_progress Current loading progress list (if available)
  #' @param context Additional context about the error
  #'
  #' @return List with error information including:
  #'   - error: Error message
  #'   - model_status: Status of the model
  #'   - loading_progress: Progress percentage (even if failed)
  #'   - error_type: Type of error
  #'   - suggestion: Suggested action for user
  
  # Convert error to string if it's not already
  error_message <- if (is.character(error)) error else as.character(error)
  
  # Determine error type
  error_type <- "unknown"
  
  if (grepl("FileNotFoundError|file", error_message, ignore.case = TRUE)) {
    error_type <- "file_not_found"
  } else if (grepl("MemoryError|memory|OOM", error_message, ignore.case = TRUE)) {
    error_type <- "memory_error"
  } else if (grepl("CUDA|cuda|gpu", error_message, ignore.case = TRUE)) {
    error_type <- "cuda_error"
  } else if (grepl("import|ImportError", error_message, ignore.case = TRUE)) {
    error_type <- "import_error"
  } else if (grepl("timeout|Timeout", error_message, ignore.case = TRUE)) {
    error_type <- "timeout_error"
  } else if (grepl("permission|Permission", error_message, ignore.case = TRUE)) {
    error_type <- "permission_error"
  }
  
  # Get progress if available
  progress <- 0
  if (!is.null(loading_progress)) {
    progress <- if (!is.null(loading_progress$progress)) loading_progress$progress else 0
  }
  
  # Generate user-friendly error message
  base_error <- paste0("Model ", model_name, " is not available. The model has not been loaded.")
  
  # Generate suggestions based on error type
  suggestions <- list(
    file_not_found = "Please check server logs and ensure the model files are present. Restart the server to load models.",
    memory_error = "The model requires more memory than available. Try closing other applications or using a smaller model.",
    cuda_error = "GPU/CUDA error detected. Check GPU availability and drivers. The model may fall back to CPU.",
    import_error = "Required dependencies are missing. Check server logs and install missing packages.",
    timeout_error = "Model loading timed out. The model may still be loading in the background. Please wait and try again.",
    permission_error = "Permission denied accessing model files. Check file permissions and server logs.",
    unknown = "Please check server logs and ensure the model files are present. Restart the server to load models."
  )
  
  suggestion <- if (error_type %in% names(suggestions)) {
    suggestions[[error_type]]
  } else {
    suggestions$unknown
  }
  
  # Always include progress percentage, even on error
  result <- list(
    error = base_error,
    model_status = "unavailable",
    loading_progress = progress,
    error_type = error_type,
    error_message = substr(error_message, 1, 200),  # Truncate long error messages
    suggestion = suggestion,
    progress_percentage = paste0(round(progress, 1), "%")
  )
  
  # Add context if provided
  if (!is.null(context)) {
    result$context <- context
  }
  
  return(result)
}

get_error_progress_message <- function(model_name, progress = 0) {
  #' Get a progress message even when there's an error.
  #'
  #' @param model_name Name of the model
  #' @param progress Current progress percentage (0-100)
  #'
  #' @return Formatted progress message
  
  if (progress == 0) {
    return(paste0("Model ", model_name, " loading not started (0%)"))
  } else if (progress < 100) {
    return(paste0("Model ", model_name, " loading failed at ", round(progress, 1), "%"))
  } else {
    return(paste0("Model ", model_name, " loading completed but failed to initialize"))
  }
}

log_model_loading_error <- function(
  model_name,
  error,
  loading_progress = NULL
) {
  #' Log model loading error with full traceback.
  #'
  #' @param model_name Name of the model
  #' @param error The error message or exception that occurred
  #' @param loading_progress Current loading progress list (if available)
  
  progress_info <- ""
  if (!is.null(loading_progress)) {
    progress <- if (!is.null(loading_progress$progress)) loading_progress$progress else 0
    status <- if (!is.null(loading_progress$status)) loading_progress$status else "unknown"
    progress_info <- paste0(" (Progress: ", progress, "%, Status: ", status, ")")
  }
  
  error_msg <- paste0("[Model Loading Error] ", model_name, progress_info, "\n")
  error_msg <- paste0(error_msg, "Error: ", as.character(error), "\n")
  
  cat(error_msg, file = stderr())
  
  # Optionally write to log file
  tryCatch({
    log_file <- file.path("data", "logs", "model_loading_errors.log")
    dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)
    cat(paste0("\n", paste(rep("=", 80), collapse = ""), "\n"), file = log_file, append = TRUE)
    cat(error_msg, file = log_file, append = TRUE)
  }, error = function(e) {
    # Don't fail if logging fails
  })
}
