#!/usr/bin/env python3
"""Run only ScalabilityEvaluator on existing generated code."""

import sys
import json
import shutil
import tempfile
import subprocess
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR, RESULTS_DIR, NUM_SAMPLES
from core.evaluators.scalability_evaluator import ScalabilityEvaluator


def find_generated_scripts(task_folder: Path) -> List[Path]:
    return sorted(task_folder.glob("generated_script_v*.py"))


def load_script_content(script_path: Path) -> str:
    if script_path.exists():
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def main():
    print("=" * 70)
    print("SCALABILITY-ONLY EVALUATION")
    print("=" * 70)
    print("\nThis script runs ONLY the ScalabilityEvaluator on existing generated code.")
    print("Results are saved alongside the existing evaluation results.\n")

    gen_path = Path(OUTPUT_DIR)
    if not gen_path.exists():
        print(f"ERROR: Generated code directory not found: {gen_path}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(RESULTS_DIR) / f"evaluation_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    all_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_models": 0,
        "total_tasks": 0,
        "num_samples": NUM_SAMPLES,
        "models": {}
    }

    model_folders = [f for f in gen_path.iterdir() if f.is_dir()]
    all_results["total_models"] = len(model_folders)

    evaluator = ScalabilityEvaluator()

    for model_idx, model_folder in enumerate(model_folders, 1):
        model_name = model_folder.name
        print(f"\n{'='*60}")
        print(f"Model {model_idx}/{len(model_folders)}: {model_name}")
        print(f"{'='*60}")

        model_results_dir = run_dir / model_name
        model_results_dir.mkdir(exist_ok=True)

        model_results = {
            "model_name": model_name,
            "tasks": {},
            "summary": {"total_tasks": 0, "avg_pass_rate": 0.0, "avg_quality_score": 0.0}
        }

        task_folders = sorted([f for f in model_folder.iterdir() if f.is_dir()])
        model_results["summary"]["total_tasks"] = len(task_folders)

        for task_idx, task_folder in enumerate(task_folders, 1):
            task_id = task_folder.name
            print(f"  [{task_idx}/{len(task_folders)}] {task_id}...")

            task_folder_abs = task_folder.resolve()
            sample_scripts = find_generated_scripts(task_folder_abs)

            if not sample_scripts:
                print(f"      No scripts found")
                continue

            task_result = {
                "task_id": task_id,
                "task_folder": str(task_folder_abs),
                "num_samples": len(sample_scripts),
                "samples": [],
                "statistics": {}
            }

            sample_results = []
            for sample_idx, script_path in enumerate(sample_scripts, 1):
                print(f"      Sample {sample_idx}/{len(sample_scripts)}: {script_path.name}")

                code_content = load_script_content(script_path)
                if not code_content:
                    sample_result = {
                        "sample_idx": sample_idx,
                        "script_name": script_path.name,
                        "quality": {"error": "No content"},
                        "scalability": {"error": "No content"}
                    }
                    sample_results.append(sample_result)
                    continue

                sample_result = {
                    "sample_idx": sample_idx,
                    "script_name": script_path.name,
                    "quality": {}
                }

                metadata = {"model_name": model_name, "task_id": task_id}

                try:
                    result = evaluator.evaluate(
                        file_path=str(script_path.resolve()),
                        code_content=code_content,
                        metadata=metadata
                    )
                    sample_result["quality"]["Scalability"] = {
                        "passed": result.passed,
                        "score": result.score,
                        "details": result.details,
                        "error_message": result.error_message
                    }
                    status = "passed" if result.passed else "failed"
                    print(f"         Scalability: {status} (score={result.score:.4f})")
                except Exception as e:
                    sample_result["quality"]["Scalability"] = {
                        "passed": False,
                        "score": 0.0,
                        "details": {},
                        "error_message": str(e)
                    }
                    print(f"         Scalability: error ({e})")

                sample_results.append(sample_result)
                task_result["samples"].append(sample_result)

            scores = [s["quality"]["Scalability"]["score"] for s in sample_results if "Scalability" in s.get("quality", {})]
            passes = [1 if s["quality"]["Scalability"]["passed"] else 0 for s in sample_results if "Scalability" in s.get("quality", {})]

            if scores:
                task_result["statistics"]["Scalability"] = {
                    "mean_score": round(statistics.mean(scores), 3),
                    "std_dev": round(statistics.stdev(scores), 3) if len(scores) > 1 else 0.0,
                    "pass_rate": round(sum(passes) / len(passes), 2),
                    "pass_count": f"{sum(passes)}/{len(passes)}"
                }

            task_result_file = model_results_dir / f"{task_id}_result.json"
            with open(task_result_file, 'w', encoding='utf-8') as f:
                json.dump(task_result, f, indent=2)

            model_results["tasks"][task_id] = task_result

        pass_rates = [t["statistics"]["Scalability"]["pass_rate"] for t in model_results["tasks"].values() if "Scalability" in t.get("statistics", {})]
        quality_scores = [t["statistics"]["Scalability"]["mean_score"] for t in model_results["tasks"].values() if "Scalability" in t.get("statistics", {})]

        if pass_rates:
            model_results["summary"]["avg_pass_rate"] = round(statistics.mean(pass_rates), 2)
        if quality_scores:
            model_results["summary"]["avg_quality_score"] = round(statistics.mean(quality_scores), 3)

        all_results["models"][model_name] = model_results

        model_summary_file = model_results_dir / "model_summary.json"
        with open(model_summary_file, 'w', encoding='utf-8') as f:
            json.dump(model_results, f, indent=2)

    all_results["total_tasks"] = sum(m["summary"]["total_tasks"] for m in all_results["models"].values())
    overall_results_file = run_dir / "overall_results.json"
    with open(overall_results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 70)
    print("SCALABILITY SUMMARY")
    print("=" * 70)
    for model_name, model_data in all_results["models"].items():
        summary = model_data["summary"]
        print(f"\n{model_name}:")
        print(f"   Tasks:          {summary['total_tasks']}")
        print(f"   Avg score:      {summary['avg_quality_score']}")
        print(f"   Avg pass rate:  {summary['avg_pass_rate']:.0%}")

    print(f"\nResults saved to: {run_dir}")
    print("=" * 70)

    return str(run_dir)


if __name__ == "__main__":
    results_path = main()
    print(f"\nTo generate scalability graphs later:\n  python -X utf8 analyze_results.py {results_path}")
    print(f"\nOr run with all results:\n  python -X utf8 analyze_results.py")