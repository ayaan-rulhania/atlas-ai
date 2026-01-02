#!/usr/bin/env python3
"""
Performance benchmark script for Atlas AI model improvements
"""

import torch
import time
import argparse
import sys
import os
from contextlib import contextmanager

# Add paths
sys.path.append('thor-1.1')
sys.path.append('thor-1.0')

from thor_1_1.models.all_rounder_model import AllRounderModel as Thor11Model
from thor_1_0.models.all_rounder_model import AllRounderModel as Thor10Model


@contextmanager
def cuda_timer():
    """Context manager for CUDA timing."""
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        yield lambda: start.elapsed_time(end)
        end.record()
        torch.cuda.synchronize()
    else:
        start = time.time()
        yield lambda: (time.time() - start) * 1000  # Convert to milliseconds


def benchmark_model(model, input_ids, attention_mask=None, task=None, num_runs=10, warmup_runs=3):
    """Benchmark model performance."""
    device = next(model.parameters()).device

    # Move inputs to device
    input_ids = input_ids.to(device)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    # Warmup runs
    model.eval()
    with torch.no_grad():
        for _ in range(warmup_runs):
            _ = model(input_ids, attention_mask, task)

    # Benchmark runs
    times = []
    with torch.no_grad():
        for _ in range(num_runs):
            with cuda_timer() as timer:
                _ = model(input_ids, attention_mask, task)
            times.append(timer())

    avg_time = sum(times) / len(times)
    return avg_time


def benchmark_memory_usage(model, input_ids, attention_mask=None, task=None):
    """Benchmark memory usage."""
    device = next(model.parameters()).device

    # Move inputs to device
    input_ids = input_ids.to(device)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    # Clear cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    model.eval()
    with torch.no_grad():
        _ = model(input_ids, attention_mask, task)

    if torch.cuda.is_available():
        memory_used = torch.cuda.max_memory_allocated() / 1024 / 1024  # MB
        return memory_used
    else:
        return 0.0  # CPU memory tracking is complex


def create_test_input(vocab_size, seq_len, batch_size=1):
    """Create test input tensors."""
    input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
    attention_mask = torch.ones(batch_size, seq_len, dtype=torch.long)
    return input_ids, attention_mask


def run_benchmarks():
    """Run comprehensive benchmarks."""
    print("Atlas AI Model Performance Benchmarks")
    print("=" * 50)

    # Test configurations
    configs = [
        {"name": "Thor 1.0 Base", "model_class": Thor10Model, "config": {}},
        {"name": "Thor 1.0 + RoPE", "model_class": Thor10Model, "config": {"use_rmsnorm": False, "use_swiglu": False}},
        {"name": "Thor 1.0 + RMSNorm", "model_class": Thor10Model, "config": {"use_rmsnorm": True, "use_swiglu": False}},
        {"name": "Thor 1.0 + SwiGLU", "model_class": Thor10Model, "config": {"use_rmsnorm": False, "use_swiglu": True}},
        {"name": "Thor 1.0 Full", "model_class": Thor10Model, "config": {"use_rmsnorm": True, "use_swiglu": True}},
        {"name": "Thor 1.1 Base", "model_class": Thor11Model, "config": {}},
        {"name": "Thor 1.1 + RoPE", "model_class": Thor11Model, "config": {"use_rmsnorm": False, "use_swiglu": False}},
        {"name": "Thor 1.1 + RMSNorm", "model_class": Thor11Model, "config": {"use_rmsnorm": True, "use_swiglu": False}},
        {"name": "Thor 1.1 + SwiGLU", "model_class": Thor11Model, "config": {"use_rmsnorm": False, "use_swiglu": True}},
        {"name": "Thor 1.1 Full", "model_class": Thor11Model, "config": {"use_rmsnorm": True, "use_swiglu": True}},
    ]

    # Test parameters
    seq_lengths = [64, 128, 256]
    batch_size = 1
    num_runs = 5

    for seq_len in seq_lengths:
        print(f"\nSequence Length: {seq_len}")
        print("-" * 30)

        input_ids, attention_mask = create_test_input(1000, seq_len, batch_size)

        for config in configs:
            try:
                # Create model
                model_kwargs = {
                    "vocab_size": 1000,
                    "hidden_size": 256,  # Smaller for benchmarking
                    "num_layers": 4,
                    "num_heads": 8,
                    "intermediate_size": 1024,
                    "max_position_embeddings": max(seq_lengths) * 2,
                    **config["config"]
                }

                model = config["model_class"](**model_kwargs)

                # Move to GPU if available
                if torch.cuda.is_available():
                    model = model.cuda()

                # Benchmark inference time
                avg_time = benchmark_model(
                    model, input_ids, attention_mask,
                    task="text_generation", num_runs=num_runs
                )

                # Benchmark memory usage
                memory_mb = benchmark_memory_usage(model, input_ids, attention_mask, task="text_generation")

                print("25")

            except Exception as e:
                print("25")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Atlas AI model performance")
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark with fewer tests')
    parser.add_argument('--cpu', action='store_true', help='Force CPU benchmarking')

    args = parser.parse_args()

    if args.cpu and torch.cuda.is_available():
        print("Forcing CPU mode...")
        torch.cuda.is_available = lambda: False

    try:
        run_benchmarks()
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
