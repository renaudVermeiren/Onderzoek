#!/usr/bin/env python3


import json
import statistics
from pathlib import Path

FOLDER1 = Path("results/evaluation_20260528_160118")
FOLDER2 = Path("results/evaluation_20260819_154149")
OUTPUT_DIR = Path("results/evaluation_merged")
OUTPUT_FILE = OUTPUT_DIR / "overall_results.json"


def load_results(path):
    with open(path / "overall_results.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_stats(scores, passes):
    n = len(scores)
    if n == 0:
        return {"mean_score": 0.0, "std_dev": 0.0, "pass_rate": 0.0, "pass_count": "0/0"}

    mean_score = statistics.mean(scores)
    std_dev = statistics.stdev(scores) if n > 1 else 0.0
    pass_rate = sum(passes) / n
    pass_count = f"{sum(passes)}/{n}"

    return {
        "mean_score": round(mean_score, 4),
        "std_dev": round(std_dev, 4),
        "pass_rate": pass_rate,
        "pass_count": pass_count
    }


def merge_results(data1, data2):
    merged = {
        "total_models": data1["total_models"],
        "total_tasks": data1["total_tasks"],
        "models": {}
    }

    for model_name in data1["models"]:
        merged_tasks = {}
        tasks1 = data1["models"][model_name]["tasks"]
        tasks2 = data2["models"][model_name]["tasks"]

        for task_id in tasks1:
            samples = tasks1[task_id].get("samples", []) + tasks2[task_id].get("samples", [])

            for i, sample in enumerate(samples):
                sample["sample_idx"] = i + 1

            evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon']
            statistics_data = {}

            for eval_name in evaluators:
                scores = []
                passes = []
                for sample in samples:
                    eval_data = sample.get("quality", {}).get(eval_name, {})
                    if eval_data:
                        scores.append(eval_data.get("score", 0.0))
                        passes.append(1 if eval_data.get("passed", False) else 0)

                if scores:
                    statistics_data[eval_name] = compute_stats(scores, passes)

            scal_scores = []
            scal_passes = []
            for sample in samples:
                scal_data = sample.get("quality", {}).get("Scalability", {})
                if scal_data:
                    scal_scores.append(scal_data.get("score", 0.0))
                    scal_passes.append(1 if scal_data.get("passed", False) else 0)

            if scal_scores:
                statistics_data["Scalability"] = compute_stats(scal_scores, scal_passes)

            func_passes = []
            for sample in samples:
                passed = sample.get("functional", {}).get("test_passed", False)
                func_passes.append(1 if passed else 0)

            n = len(func_passes)
            pr = sum(func_passes) / n if n > 0 else 0.0
            statistics_data["Functional"] = {
                "mean_score": pr,
                "std_dev": 0.0,
                "pass_rate": pr,
                "pass_count": f"{sum(func_passes)}/{n}" if n > 0 else "0/0"
            }

            merged_tasks[task_id] = {
                "samples": samples,
                "statistics": statistics_data
            }

        merged["models"][model_name] = {"tasks": merged_tasks}

    return merged


def main():
    print("Loading evaluation results from both folders...")
    data1 = load_results(FOLDER1)
    data2 = load_results(FOLDER2)

    print(f"  Folder 1: {data1['total_models']} models, {data1['total_tasks']} tasks")
    print(f"  Folder 2: {data2['total_models']} models, {data2['total_tasks']} tasks")

    print("Merging samples (3 + 3 = 6 per model-task)...")
    merged = merge_results(data1, data2)

    for model_name in merged["models"]:
        for task_id in merged["models"][model_name]["tasks"]:
            n = len(merged["models"][model_name]["tasks"][task_id]["samples"])
            assert n == 6, f"{model_name}/{task_id}: expected 6 samples, got {n}"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"Merged results saved to: {OUTPUT_FILE}")
    print("Done.")


if __name__ == "__main__":
    main()