# MLOps Infrastructure v2.0.0mini

This directory contains the MLOps infrastructure for Thor models, providing advanced training, evaluation, and model management capabilities.

## Features

### 1. Parameter-Efficient Fine-Tuning (PEFT/LoRA)
- Train lightweight adapter models using LoRA (Low-Rank Adaptation)
- Reduce training parameters by 10-100x compared to full fine-tuning
- Merge adapters into base model for deployment
- Support for QLoRA (Quantized LoRA) for even more efficient training

### 2. Automated Hyperparameter Tuning
- Optuna integration for automatic hyperparameter optimization
- Supports learning rate, batch size, LoRA parameters, and more
- Web dashboard available with optuna-dashboard

### 3. Model Evaluation Pipeline
- Standardized benchmarks for:
  - Question Answering
  - Text Summarization
  - Text Classification
- Automatic model comparison
- Performance metrics tracking

### 4. Model Registry
- Version tracking for all trained models
- Metrics and metadata storage
- Production deployment management
- Model comparison tools
- MLflow integration ready

### 5. Inference Server Abstraction
- Unified interface for multiple backends:
  - PyTorch (default)
  - vLLM (for production)
  - TensorRT-LLM (for optimized inference)
- Easy backend switching
- Memory-efficient model loading

## Installation

Install the MLOps dependencies:

```bash
pip install -r requirements-mlops.txt
```

## Usage

### Training with LoRA

```python
from mlops import TrainingManager, ModelRegistry, EvaluationPipeline

# Initialize training manager
trainer = TrainingManager(base_model_path="models/base_model.pt")

# Train with LoRA
result = trainer.train_with_lora(
    model=your_model,
    train_loader=train_loader,
    val_loader=val_loader,
    num_epochs=3,
    learning_rate=1e-4,
    lora_r=8,
    lora_alpha=16
)

# Register model
registry = ModelRegistry()
version = registry.register_model(
    model_name="thor-1.1",
    model_path=result["adapter_path"],
    metrics={"accuracy": 0.95}
)
```

### Hyperparameter Tuning

```python
# Automatically find best hyperparameters
tuning_result = trainer.tune_hyperparameters(
    model=your_model,
    train_loader=train_loader,
    val_loader=val_loader,
    n_trials=20
)

print(f"Best learning rate: {tuning_result['best_params']['learning_rate']}")
```

### Model Evaluation

```python
# Evaluate model on benchmarks
evaluator = EvaluationPipeline()
results = evaluator.evaluate_model(
    model=your_model,
    tokenizer=your_tokenizer,
    task_types=["qa", "summarization", "classification"]
)

print(f"Overall score: {results['overall_score']}")
```

### Model Registry

```python
# Register and manage model versions
registry = ModelRegistry()

# Register new version
version = registry.register_model(
    model_name="thor-1.1",
    model_path="models/v2.pt",
    metrics={"accuracy": 0.96, "f1": 0.94}
)

# Set as production
registry.set_production_version("thor-1.1", version)

# Compare versions
comparison = registry.compare_versions("thor-1.1", "v1", "v2")
```

### Inference Server

```python
from mlops import InferenceServer

# Initialize server
server = InferenceServer(backend_type="pytorch")

# Load model
server.load_model("models/final_model.pt")

# Run inference
result = server.predict("Hello, how are you?", task="text_generation")

# Unload when done
server.unload_model()
```

## Whisper Integration

For speech recognition, use the Whisper integration:

```python
from poseidon.whisper_integration import get_whisper_transcriber

# Initialize transcriber
transcriber = get_whisper_transcriber(model_size="base", use_faster=True)

# Transcribe audio
result = transcriber.transcribe("audio.wav", language="en")
print(result["text"])
```

## Configuration

Set environment variables for configuration:

- `INFERENCE_BACKEND`: Backend type ("pytorch", "vllm", "tensorrt")
- `CUDA_AVAILABLE`: Set to "1" if CUDA is available
- `MLFLOW_TRACKING_URI`: MLflow tracking server URI (optional)

## Future Enhancements

- Full MLflow integration
- vLLM backend implementation
- TensorRT-LLM support
- Distributed training support
- Model serving API
- A/B testing framework

