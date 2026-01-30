# Calculate model loading percentage based on various factors.
# This R script provides functions to calculate and track model loading progress.

calculate_loading_percentage <- function(
  model_name,
  start_time = NULL,
  current_step = 0,
  total_steps = 100,
  file_size_loaded = 0,
  total_file_size = 0,
  memory_used = 0,
  total_memory_required = 0
) {
  #' Calculate model loading percentage based on multiple factors.
  #'
  #' @param model_name Name of the model being loaded
  #' @param start_time Timestamp when loading started (optional)
  #' @param current_step Current loading step (0-based)
  #' @param total_steps Total number of loading steps
  #' @param file_size_loaded Bytes of model files loaded so far
  #' @param total_file_size Total bytes of model files to load
  #' @param memory_used Memory currently used for loading (bytes)
  #' @param total_memory_required Total memory required (bytes)
  #'
  #' @return List with progress information including:
  #'   - progress: Percentage (0-100)
  #'   - status: Current status string
  #'   - message: Detailed message
  #'   - estimated_time_remaining: Estimated seconds remaining (if start_time provided)
  
  # Calculate progress from different factors
  step_progress <- if (total_steps > 0) (current_step / total_steps * 100) else 0
  file_progress <- if (total_file_size > 0) (file_size_loaded / total_file_size * 100) else 0
  memory_progress <- if (total_memory_required > 0) (memory_used / total_memory_required * 100) else 0
  
  # Weighted average (step progress is most reliable)
  if (total_steps > 0) {
    progress <- step_progress
  } else if (total_file_size > 0) {
    progress <- file_progress
  } else if (total_memory_required > 0) {
    progress <- memory_progress
  } else {
    progress <- 0
  }
  
  # Ensure progress is between 0 and 100
  progress <- max(0, min(100, progress))
  
  # Calculate estimated time remaining if start_time is provided
  estimated_time_remaining <- NULL
  if (!is.null(start_time) && progress > 0) {
    elapsed_time <- as.numeric(Sys.time()) - start_time
    if (progress < 100) {
      estimated_total_time <- elapsed_time / (progress / 100)
      estimated_time_remaining <- max(0, estimated_total_time - elapsed_time)
    }
  }
  
  # Generate status message
  if (progress == 0) {
    status <- "not_started"
    message <- paste0("Model ", model_name, " loading not started")
  } else if (progress < 25) {
    status <- "initializing"
    message <- paste0("Initializing ", model_name, "... (", round(progress, 1), "%)")
  } else if (progress < 50) {
    status <- "loading"
    message <- paste0("Loading ", model_name, " weights... (", round(progress, 1), "%)")
  } else if (progress < 75) {
    status <- "loading"
    message <- paste0("Loading ", model_name, " components... (", round(progress, 1), "%)")
  } else if (progress < 100) {
    status <- "finalizing"
    message <- paste0("Finalizing ", model_name, "... (", round(progress, 1), "%)")
  } else {
    status <- "loaded"
    message <- paste0("Model ", model_name, " loaded successfully")
  }
  
  result <- list(
    progress = round(progress, 2),
    status = status,
    message = message,
    step_progress = round(step_progress, 2),
    file_progress = round(file_progress, 2),
    memory_progress = round(memory_progress, 2),
    current_step = current_step,
    total_steps = total_steps
  )
  
  if (!is.null(estimated_time_remaining)) {
    result$estimated_time_remaining <- round(estimated_time_remaining, 2)
  }
  
  return(result)
}

get_default_loading_steps <- function(model_name) {
  #' Get default number of loading steps for a model.
  #'
  #' @param model_name Name of the model
  #'
  #' @return Default number of steps for the model
  
  step_map <- list(
    "thor-1.0" = 5,
    "thor-1.1" = 8,
    "qwen3-thor" = 10,
    "antelope-1.0" = 5,
    "antelope-1.1" = 5
  )
  
  model_lower <- tolower(model_name)
  if (model_lower %in% names(step_map)) {
    return(step_map[[model_lower]])
  } else {
    return(10)
  }
}

interpolate_progress <- function(
  previous_progress,
  current_progress,
  time_elapsed,
  smoothing_factor = 0.3
) {
  #' Smooth progress updates to avoid jittery progress bars.
  #'
  #' @param previous_progress Previous progress percentage
  #' @param current_progress Current progress percentage
  #' @param time_elapsed Time elapsed since last update (seconds)
  #' @param smoothing_factor Smoothing factor (0-1), higher = more smoothing
  #'
  #' @return Smoothed progress percentage
  
  # Exponential moving average
  smoothed <- previous_progress * (1 - smoothing_factor) + current_progress * smoothing_factor
  return(max(previous_progress, smoothed))  # Never go backwards
}
