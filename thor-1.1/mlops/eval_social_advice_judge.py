"""
Run social-advice evaluation using an external LLM judge.

Example:
  export OPENAI_API_KEY=...
  python3 thor-1.1/mlops/eval_social_advice_judge.py \
    --model thor-1.1/models/final_model.pt \
    --tokenizer thor-1.1/models/tokenizer.json \
    --eval training_data/social_advice_eval.jsonl
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import yaml

# Allow running from repo root without installing as a package.
_THOR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THOR_ROOT not in sys.path:
    sys.path.insert(0, _THOR_ROOT)

from mlops.evaluation_pipeline import evaluate_social_advice_with_judge  # noqa: E402
from mlops.judges.external_llm_judge import OpenAICompatibleJudge  # noqa: E402
from mlops.predictors.all_rounder_greedy import AllRounderGreedyPredictor  # noqa: E402
from models import AllRounderModel  # noqa: E402
from utils import SimpleTokenizer  # noqa: E402


def _load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _task_configs(full_config: Dict[str, Any]) -> Dict[str, Any]:
    tasks_config: List[Dict[str, Any]] = full_config.get("tasks", [])
    return {t["name"]: t for t in tasks_config if t.get("enabled", True) and "name" in t}


def main():
    parser = argparse.ArgumentParser(description="Judge-scored evaluation for Thor social advice")
    parser.add_argument("--config", type=str, default="thor-1.1/config/config.yaml")
    parser.add_argument("--model", type=str, default="thor-1.1/models/final_model.pt")
    parser.add_argument("--tokenizer", type=str, default="thor-1.1/models/tokenizer.json")
    parser.add_argument("--eval", type=str, default="training_data/social_advice_eval.jsonl")
    parser.add_argument("--spec", type=str, default="thor-1.1/mlops/social_advice_spec.md")
    parser.add_argument("--out", type=str, default="thor-1.1/mlops/social_advice_judge_results.json")
    parser.add_argument("--max_new_tokens", type=int, default=128)
    args = parser.parse_args()

    config = _load_config(args.config)
    tasks = _task_configs(config)
    tokenizer = SimpleTokenizer.load(args.tokenizer)
    model = AllRounderModel.load_model(args.model, tasks, config)

    # Clamp tokenizer IDs to the model vocab to avoid embedding index errors.
    if hasattr(model, "vocab_size"):
        tokenizer.vocab_size = int(model.vocab_size)

    predictor = AllRounderGreedyPredictor(model=model, tokenizer=tokenizer)
    judge = OpenAICompatibleJudge()

    results = evaluate_social_advice_with_judge(
        predictor=predictor,
        judge=judge,
        eval_path=args.eval,
        spec_path=args.spec,
        max_new_tokens=args.max_new_tokens,
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Social Advice Judge Eval ===")
    print(f"Wrote: {args.out}")
    print(f"Overall mean: {results.get('overall_mean'):.3f}")
    print(f"Must-not violation rate: {results.get('must_not_violation_rate'):.3f}")
    print("Top issues:", list((results.get('issue_histogram') or {}).keys())[:10])


if __name__ == "__main__":
    main()


