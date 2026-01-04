"""
Train Thor-1.1 on chat-style Social Advice SFT data.

This script is intentionally simple: it loads the existing AllRounderModel + SimpleTokenizer,
uses the JSONL chat SFT format in `training_data/social_advice_sft.jsonl`,
and runs supervised fine-tuning with optional LoRA (if PEFT supports the model).
"""

import argparse
import os
import sys
from typing import Dict, Any, List

import yaml

# Allow running from repo root without installing as a package.
_THOR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THOR_ROOT not in sys.path:
    sys.path.insert(0, _THOR_ROOT)

from mlops.training_manager import TrainingManager  # noqa: E402
from models import AllRounderModel  # noqa: E402
from utils import SimpleTokenizer  # noqa: E402
from utils.data_loader import MultiTaskDataLoader  # noqa: E402


def _load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _task_configs(full_config: Dict[str, Any]) -> Dict[str, Any]:
    tasks_config: List[Dict[str, Any]] = full_config.get("tasks", [])
    return {t["name"]: t for t in tasks_config if t.get("enabled", True) and "name" in t}


def main():
    parser = argparse.ArgumentParser(description="Train thor-1.1 social advice adapters (chat SFT)")
    parser.add_argument("--config", type=str, default="thor-1.1/config/config.yaml")
    parser.add_argument("--base_model", type=str, default="thor-1.1/models/final_model.pt")
    parser.add_argument("--tokenizer", type=str, default="thor-1.1/models/tokenizer.json")
    parser.add_argument("--train_data", type=str, default="training_data/social_advice_sft.jsonl")
    parser.add_argument("--output_dir", type=str, default="thor-1.1/models/adapters")
    parser.add_argument("--output_name", type=str, default=None)

    parser.add_argument("--max_length", type=int, default=None, help="Override max sequence length (default: config model max_position_embeddings)")
    parser.add_argument("--batch_size", type=int, default=None, help="Override config training batch_size")
    parser.add_argument("--num_epochs", type=int, default=None, help="Override config training num_epochs")
    parser.add_argument("--learning_rate", type=float, default=None, help="Override config training learning_rate")
    parser.add_argument("--max_batches_per_epoch", type=int, default=None, help="Optional cap for quick smoke tests")

    parser.add_argument("--lora_r", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=16)
    parser.add_argument("--val_split", type=float, default=0.1, help="If no val set exists, split train data for validation")

    args = parser.parse_args()

    config = _load_config(args.config)
    tasks = _task_configs(config)

    tokenizer = SimpleTokenizer.load(args.tokenizer)
    model = AllRounderModel.load_model(args.base_model, tasks, config)
    # Ensure tokenizer does not emit IDs outside the model embedding vocab.
    if hasattr(model, "vocab_size"):
        tokenizer.vocab_size = int(model.vocab_size)

    # Data
    max_len = args.max_length or int(config.get("model", {}).get("max_position_embeddings", 512))
    batch_size = args.batch_size or int(config.get("training", {}).get("batch_size", 32))

    loader = MultiTaskDataLoader(tokenizer=tokenizer, batch_size=batch_size, max_length=max_len)
    data = loader.load_data(args.train_data)

    # Train/val split if needed (use last portion as validation for stability)
    val_loader = None
    if args.val_split and 0.0 < args.val_split < 1.0 and len(data) >= 10:
        split_idx = int(len(data) * (1.0 - args.val_split))
        train_data = data[:split_idx]
        val_data = data[split_idx:]
        train_loader = loader.create_dataloader(train_data, task="text_generation", shuffle=True)
        val_loader = loader.create_dataloader(val_data, task="text_generation", shuffle=False)
    else:
        train_loader = loader.create_dataloader(data, task="text_generation", shuffle=True)

    trainer = TrainingManager(base_model_path=args.base_model, output_dir=args.output_dir)

    result = trainer.train_with_lora(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=args.num_epochs or int(config.get("training", {}).get("num_epochs", 3)),
        learning_rate=args.learning_rate or float(config.get("training", {}).get("learning_rate", 1e-4)),
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        output_name=args.output_name,
        task="text_generation",
        max_batches_per_epoch=args.max_batches_per_epoch,
    )

    print("\n=== Training Complete ===")
    print(f"Adapter/checkpoint saved to: {result.get('adapter_path')}")
    print(f"Used PEFT: {result.get('use_peft')}")
    print(f"History: {result.get('training_history')}")


if __name__ == "__main__":
    main()


