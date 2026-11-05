"""Reproduce measured artifacts. Run from PROJECT_01 with Python 3.11."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diabetes_agent.config import ARTIFACTS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all", "models", "rl", "evaluation"], default="all")
    args = parser.parse_args()
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "figures").mkdir(exist_ok=True)
    if args.stage in ("all", "models"):
        from diabetes_agent.models import train_all
        results, manifest = train_all()
        print(results.to_string(index=False), flush=True)
        print("Default selected on validation:", manifest["default_model"], flush=True)
    if args.stage in ("all", "rl"):
        from diabetes_agent.rl import run_experiment
        print(run_experiment().to_string(), flush=True)
    if args.stage in ("all", "evaluation"):
        from diabetes_agent.evaluation import evaluate_all
        print(json.dumps(evaluate_all(), ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
