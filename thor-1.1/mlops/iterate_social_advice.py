"""
Iteration loop: train -> (optional) judge-eval -> register -> promote.

This implements the workflow described in the Social Advice plan. It is safe to run without
external API access: if OPENAI_API_KEY is not set, judge evaluation is skipped and the loop
will still register artifacts with whatever metrics are available.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

# Allow running from repo root without installing as a package.
_THOR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THOR_ROOT not in sys.path:
    sys.path.insert(0, _THOR_ROOT)

from mlops.model_registry import ModelRegistry  # noqa: E402
from mlops.training_manager import TrainingManager  # noqa: E402
from mlops.evaluation_pipeline import evaluate_social_advice_with_judge  # noqa: E402
from mlops.judges.external_llm_judge import OpenAICompatibleJudge  # noqa: E402
from mlops.predictors.all_rounder_greedy import AllRounderGreedyPredictor  # noqa: E402
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
    parser = argparse.ArgumentParser(description="Iterate social advice improvements (train -> eval -> register)")
    parser.add_argument("--config", type=str, default="thor-1.1/config/config.yaml")
    parser.add_argument("--base_model", type=str, default="thor-1.1/models/final_model.pt")
    parser.add_argument("--tokenizer", type=str, default="thor-1.1/models/tokenizer.json")
    parser.add_argument("--train_data", type=str, default="training_data/social_advice_sft.jsonl")
    parser.add_argument("--eval_data", type=str, default="training_data/social_advice_eval.jsonl")
    parser.add_argument("--spec", type=str, default="thor-1.1/mlops/social_advice_spec.md")

    parser.add_argument("--adapters_dir", type=str, default="thor-1.1/models/adapters")
    parser.add_argument("--registry_dir", type=str, default="thor-1.1/models/registry")
    parser.add_argument("--iterations", type=int, default=2)

    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--num_epochs", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--max_batches_per_epoch", type=int, default=1)
    parser.add_argument("--val_split", type=float, default=0.1)

    args = parser.parse_args()

    config = _load_config(args.config)
    tasks = _task_configs(config)
    tokenizer = SimpleTokenizer.load(args.tokenizer)
    base_model = AllRounderModel.load_model(args.base_model, tasks, config)

    # Clamp tokenizer IDs to the model vocab to avoid embedding index errors.
    if hasattr(base_model, "vocab_size"):
        tokenizer.vocab_size = int(base_model.vocab_size)

    loader = MultiTaskDataLoader(tokenizer=tokenizer, batch_size=args.batch_size, max_length=args.max_length)
    data = loader.load_data(args.train_data)

    # Stable split: last portion is validation
    split_idx = int(len(data) * (1.0 - args.val_split)) if len(data) >= 10 else len(data)
    train_data = data[:split_idx]
    val_data = data[split_idx:] if split_idx < len(data) else []

    train_loader = loader.create_dataloader(train_data, task="text_generation", shuffle=True)
    val_loader = loader.create_dataloader(val_data, task="text_generation", shuffle=False) if val_data else None

    trainer = TrainingManager(base_model_path=args.base_model, output_dir=args.adapters_dir)
    registry = ModelRegistry(registry_path=args.registry_dir)

    report: Dict[str, Any] = {"iterations": [], "timestamp": datetime.now().isoformat()}
    best_version: Optional[str] = None
    best_score: Optional[float] = None

    can_judge = bool(os.getenv("OPENAI_API_KEY"))
    judge = OpenAICompatibleJudge() if can_judge else None

    for i in range(args.iterations):
        iter_name = f"social_advice_iter_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        model = AllRounderModel.load_model(args.base_model, tasks, config)
        if hasattr(model, "vocab_size"):
            tokenizer.vocab_size = int(model.vocab_size)

        train_result = trainer.train_with_lora(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            num_epochs=args.num_epochs,
            learning_rate=args.learning_rate,
            output_name=iter_name,
            task="text_generation",
            max_batches_per_epoch=args.max_batches_per_epoch,
        )

        metrics: Dict[str, float] = {}
        train_loss = train_result.get("training_history", {}).get("train_loss", [])
        val_loss = train_result.get("training_history", {}).get("val_loss", [])
        if train_loss:
            metrics["train_loss"] = float(train_loss[-1])
        if val_loss:
            metrics["val_loss"] = float(val_loss[-1])

        eval_result: Optional[Dict[str, Any]] = None
        if can_judge and judge is not None:
            predictor = AllRounderGreedyPredictor(model=model, tokenizer=tokenizer)
            eval_result = evaluate_social_advice_with_judge(
                predictor=predictor,
                judge=judge,
                eval_path=args.eval_data,
                spec_path=args.spec,
                max_new_tokens=128,
            )
            metrics["social_advice_overall_mean"] = float(eval_result.get("overall_mean", 0.0))
            metrics["social_advice_must_not_violation_rate"] = float(eval_result.get("must_not_violation_rate", 0.0))

        version = registry.register_model(
            model_name="thor-1.1-social-advice",
            model_path=train_result["adapter_path"],
            version=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
            metrics=metrics,
            metadata={"iteration": i, "output_name": iter_name, "judge_enabled": bool(can_judge)},
        )

        score = metrics.get("social_advice_overall_mean")
        if score is not None:
            if best_score is None or score > best_score:
                best_score = score
                best_version = version

        report["iterations"].append(
            {
                "iteration": i,
                "adapter_path": train_result.get("adapter_path"),
                "registered_version": version,
                "metrics": metrics,
                "eval_summary": {
                    "overall_mean": eval_result.get("overall_mean") if eval_result else None,
                    "must_not_violation_rate": eval_result.get("must_not_violation_rate") if eval_result else None,
                    "top_issues": list((eval_result.get("issue_histogram") or {}).keys())[:10] if eval_result else [],
                },
            }
        )

    # Promote best (only meaningful if judge ran)
    if best_version is not None:
        registry.set_production_version("thor-1.1-social-advice", best_version)
        report["promoted_version"] = best_version
        report["promoted_score"] = best_score
    else:
        report["promoted_version"] = None
        report["promoted_score"] = None

    out_path = "thor-1.1/mlops/social_advice_iteration_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=== Iteration Loop Complete ===")
    print(f"Wrote report: {out_path}")
    if best_version is not None:
        print(f"Promoted version: {best_version} (score={best_score})")
    else:
        print("No judge available; registered iterations without promotion scoring.")


if __name__ == "__main__":
    main()


