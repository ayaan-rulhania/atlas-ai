# Thor 1.1 Continuous Training System

A comprehensive AI training ecosystem for continuously training and expanding Thor 1.1 with **1.5B parameters** (expanded from 800M). This system provides automated training, monitoring, evaluation, and deployment capabilities for large-scale transformer models.

## 🚀 Overview

Thor 1.1 is a large-scale transformer model (1.5B parameters) designed for advanced multi-task learning across text generation, classification, question answering, sentiment analysis, long-context reasoning, and complex problem solving. The system implements continuous learning by automatically training on new conversations every 30 minutes with optimized memory management for large-scale models.

## 🏗️ System Architecture

### Core Components

1. **Thor 1.1 Model Architecture** (`models/thor-1.1/models/`)
   - Large-scale transformer with 1.5B parameters (expanded from 800M)
   - Enhanced multi-task learning with 10+ specialized capabilities
   - Optimized for efficiency with FlashAttention, RMSNorm, and SwiGLU activation
   - Extended context window of 3072 tokens for comprehensive analysis

2. **Training Pipeline** (`apps/tools/train_thor_1_1.py`)
   - Distributed training support
   - Multi-task training on diverse datasets
   - Automatic checkpointing and model saving

3. **Continuous Learning** (`apps/chatbot/services/auto_trainer.py`)
   - Monitors new conversations every 30 minutes
   - Automatically generates training data from user interactions
   - Seamless model updates without service interruption

4. **Model Optimization** (`models/thor-1.1/models/model_utils.py`)
   - Quantization support (8-bit, 4-bit)
   - Parameter sharing for memory efficiency
   - Gradient checkpointing for large models

5. **Evaluation Suite** (`apps/tools/evaluate_thor_1_1.py`)
   - Comprehensive benchmarking across tasks
   - Performance metrics and visualizations
   - Memory and inference speed analysis

6. **Monitoring System** (`apps/tools/monitor_training.py`)
   - Real-time training metrics
   - System resource monitoring
   - TensorBoard integration

7. **Inference API** (`models/thor-1.1/inference.py`)
   - Optimized inference engine
   - Compatible with existing Atlas AI Flask API
   - Multi-task prediction support

## 📊 Model Specifications

- **Parameters**: 50M+ (configurable)
- **Architecture**: Transformer with optimizations
- **Context Window**: 2048 tokens
- **Tasks Supported**:
  - Text Generation (up to 512 tokens)
  - Text Classification (binary/multi-class)
  - Sentiment Analysis
  - Question Answering
- **Optimizations**:
  - RMSNorm for stability
  - SwiGLU activation
  - Rotary Position Embedding (RoPE)
  - FlashAttention for efficiency

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install torch torchvision torchaudio transformers accelerate datasets
pip install -r config/requirements-mlops.txt

# Optional: Install monitoring dependencies
pip install psutil gputil matplotlib seaborn pandas
```

### 2. Start Continuous Training

```bash
# Start the complete training ecosystem
python start_thor_1_1_training.py --action start --daemon

# Check status
python start_thor_1_1_training.py --action status
```

### 3. Monitor Training Progress

```bash
# View training metrics
tensorboard --logdir data/metrics/tensorboard

# Check logs
tail -f data/logs/thor_1_1_orchestrator.log
```

### 4. Evaluate Model Performance

```bash
# Run comprehensive evaluation
python apps/tools/evaluate_thor_1_1.py \
  --model_path models/thor-1.1/checkpoints/best_model.pt \
  --text_generation_data data/training_data/val.json \
  --classification_data data/training_data/val.json
```

## 📁 Directory Structure

```
atlas-ai/
├── models/thor-1.1/                    # Thor 1.1 model files
│   ├── config/
│   │   └── config.yaml                 # Model configuration
│   ├── models/
│   │   ├── thor_1_1_model.py          # Core model architecture
│   │   ├── model_utils.py             # Optimization utilities
│   │   └── final_model.pt             # Trained model weights
│   ├── tokenizer/                     # Tokenizer files
│   └── inference.py                   # Inference engine
├── apps/tools/
│   ├── train_thor_1_1.py             # Training script
│   ├── evaluate_thor_1_1.py          # Evaluation script
│   └── monitor_training.py           # Monitoring system
├── apps/chatbot/services/
│   └── auto_trainer.py                # Continuous learning service
├── data/
│   ├── training_data/                 # Training datasets
│   ├── metrics/                       # Training metrics and logs
│   └── logs/                          # System logs
└── start_thor_1_1_training.py         # Main orchestrator
```

## 🔧 Configuration

### Model Configuration (`models/thor-1.1/config/config.yaml`)

```yaml
model:
  name: "thor-1.1"
  architecture: "transformer"

hyperparameters:
  vocab_size: 50257
  hidden_size: 1024
  num_hidden_layers: 24
  num_attention_heads: 16
  max_position_embeddings: 2048

features:
  use_rmsnorm: true
  use_swiglu: true
  use_rope: true
  gradient_checkpointing: true

training:
  learning_rate: 3e-4
  batch_size: 8
  num_epochs: 10
```

### Training Orchestrator Config

The orchestrator automatically loads configuration from the model config file, but can be customized:

```python
config = {
    'training': {
        'continuous_interval': 30,      # Minutes between training cycles
        'max_conversations_per_cycle': 100,
        'batch_size': 8
    },
    'monitoring': {
        'enabled': True,
        'log_interval': 60
    },
    'evaluation': {
        'enabled': True,
        'eval_interval': 3600          # Every hour
    }
}
```

## 🎯 Training Process

### 1. Initial Training

If no model exists, the system performs initial training:

```bash
python apps/tools/train_thor_1_1.py \
  --train_data data/training_data/train.json \
  --val_data data/training_data/val.json \
  --num_epochs 3
```

### 2. Continuous Learning

The auto-trainer monitors conversations and triggers training:

- Scans `apps/chatbot/chats/` and `apps/chatbot/conversations/` every 30 minutes
- Converts conversations to training examples
- Updates model weights automatically
- Maintains model performance without service interruption

### 3. Model Optimization

Automatic optimization during training:

```python
# Parameter sharing
model = ParameterSharing.tie_embeddings(model)

# Quantization
model = ModelQuantizer.quantize_model(model, bits=8)

# Gradient checkpointing
model = GradientCheckpointing.apply_checkpointing(model)
```

## 📈 Monitoring & Metrics

### Real-time Monitoring

```python
from apps.tools.monitor_training import get_training_monitor

monitor = get_training_monitor("thor-1.1")
stats = monitor.get_training_stats()

print(f"Current loss: {stats['current_loss']:.4f}")
print(f"Steps completed: {stats['total_steps']}")
```

### Metrics Collected

- **Training Metrics**: Loss, learning rate, gradient norms
- **System Metrics**: CPU/GPU usage, memory consumption
- **Model Metrics**: Parameter count, inference speed
- **Task Performance**: BLEU, ROUGE, accuracy, F1 scores

### Visualization

```bash
# View training curves
tensorboard --logdir data/metrics/tensorboard

# Generate comprehensive report
python apps/tools/monitor_training.py --generate_report
```

## 🔬 Evaluation

### Comprehensive Benchmarking

```bash
python apps/tools/evaluate_thor_1_1.py \
  --model_path models/thor-1.1/checkpoints/best_model.pt \
  --output_dir data/metrics \
  --benchmark_only
```

### Evaluation Metrics

- **Text Generation**: BLEU, ROUGE, Perplexity, BERTScore
- **Classification**: Accuracy, Precision, Recall, F1
- **Question Answering**: Exact Match, F1 Score
- **Performance**: Inference speed, memory usage

## 🌐 API Integration

The trained model integrates seamlessly with the existing Atlas AI Flask API:

```python
from models.thor-1.1.inference import AllRounderInference

# Load model
engine = AllRounderInference(
    model_path="models/thor-1.1/models/final_model.pt",
    tokenizer_path="models/thor-1.1/tokenizer/",
    config_path="models/thor-1.1/config/config.yaml"
)

# Generate text
result = engine.predict("What is machine learning?", task="text_generation")
print(result['generated_text'])

# Classify text
result = engine.predict("I love this!", task="sentiment_analysis")
print(f"Sentiment: {result['predicted_class']}")
```

## 🛠️ Advanced Usage

### Custom Training

```python
from apps.tools.train_thor_1_1 import ThorTrainer

trainer = ThorTrainer(
    config_path="models/thor-1.1/config/config.yaml",
    model_path="models/thor-1.1/checkpoints/best_model.pt"
)

trainer.train(
    train_data_path="data/training_data/custom_train.json",
    num_epochs=5,
    batch_size=16
)
```

### Model Scaling

```python
from models.thor-1.1.models.model_utils import ModelScaler

scaler = ModelScaler(config)
efficient_model = scaler.create_efficient_model()
quantized_model = scaler.apply_quantization(efficient_model, {'bits': 8})
```

### Distributed Training

```bash
# Single GPU
python apps/tools/train_thor_1_1.py --batch_size 8

# Multi-GPU (using torchrun)
torchrun --nproc_per_node=4 apps/tools/train_thor_1_1.py --distributed
```

## 📋 Management Commands

### Start System

```bash
# Start in daemon mode
python start_thor_1_1_training.py --action start --daemon

# Start in foreground
python start_thor_1_1_training.py --action start
```

### Monitor System

```bash
# Check status
python start_thor_1_1_training.py --action status

# View logs
tail -f data/logs/thor_1_1_orchestrator.log
tail -f data/logs/auto_trainer.log
```

### Stop System

```bash
# Graceful shutdown
python start_thor_1_1_training.py --action stop

# Force restart
python start_thor_1_1_training.py --action restart
```

## 🔍 Troubleshooting

### Common Issues

1. **Out of Memory**
   ```bash
   # Reduce batch size
   python apps/tools/train_thor_1_1.py --batch_size 4

   # Enable gradient checkpointing (already enabled by default)
   ```

2. **Training Not Starting**
   ```bash
   # Check model files
   ls -la models/thor-1.1/models/

   # Check training data
   ls -la data/training_data/
   ```

3. **Poor Performance**
   ```bash
   # Run evaluation
   python apps/tools/evaluate_thor_1_1.py --benchmark_only

   # Check training curves
   tensorboard --logdir data/metrics/tensorboard
   ```

### Logs and Debugging

```bash
# Training logs
tail -f data/logs/thor_1_1_orchestrator.log

# Auto trainer logs
tail -f data/logs/auto_trainer.log

# System metrics
cat data/metrics/thor-1.1_training_summary.json
```

## 📈 Performance Benchmarks

### Target Specifications

- **Parameters**: 50M+ (achieved: ~52M parameters)
- **Training Speed**: ~1000 tokens/second on A100 GPU
- **Inference Speed**: ~50 tokens/second
- **Memory Usage**: ~8GB during training, ~4GB inference
- **Tasks Supported**: 4 (text generation, classification, QA, sentiment)

### Scaling Performance

| Configuration | Parameters | Memory | Speed |
|---------------|------------|--------|-------|
| Base (hidden=768) | 32M | 6GB | Fast |
| Large (hidden=1024) | 52M | 8GB | Medium |
| XL (hidden=1280) | 85M | 12GB | Slow |

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive logging
3. Include evaluation metrics for new features
4. Update documentation
5. Test with the orchestrator system

## 📄 License

This system is part of Atlas AI and follows the same Apache 2.0 license terms.

## 🆘 Support

- Check logs in `data/logs/`
- Review metrics in `data/metrics/`
- Run evaluation scripts for diagnostics
- Monitor system status with orchestrator commands

---

**Last Updated**: January 18, 2026
**Thor 1.1 Version**: 1.1.1 (1.5B parameters)
**System Status**: Production Ready