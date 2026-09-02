#!/usr/bin/env python3


import json
import statistics
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

MODEL_COLORS = {
    'deepseek-coder-v2_latest': '#e74c3c',
    'gemma4_latest': '#3498db',
    'llama3_latest': '#2ecc71',
    'mistral_latest': '#f39c12',
    'qwen2.5-coder_latest': '#9b59b6',
    'phi4-mini_latest': '#1abc9c',
    'qwen3.5_latest': '#e91e63',
    'codellama': '#95a5a6',
}

EVAL_COLORS = {
    'Syntax': '#2ecc71',
    'Style': '#e67e22',
    'Security': '#3498db',
    'Execution': '#f39c12',
    'Performance': '#e74c3c',
    'Radon': '#9b59b6',
    'Functional': '#1abc9c',
    'Scalability': '#e91e63'
}

DATA_DIR = Path("results/evaluation_merged")
GRAPH_DIR = Path("graphs/evaluation_merged")


def load_results():
    path = DATA_DIR / "overall_results.json"
    if not path.exists():
        print(f"[ERROR] {path} not found. Run merge_results.py first.")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_model_color(model_name):
    return MODEL_COLORS.get(model_name, '#95a5a6')


def get_evaluator_stats(task_data, evaluator_name):
    stats = task_data.get("statistics", {})
    eval_stats = stats.get(evaluator_name, {})
    if eval_stats and "mean_score" in eval_stats:
        return eval_stats.get("mean_score", 0.0), eval_stats.get("pass_rate", 0.0)
    return 0.0, 0.0


def load_difficulty_map():
    prompts_dir = Path("prompts")
    mapping = {}
    for prompt_dir in prompts_dir.iterdir():
        if prompt_dir.is_dir() and not prompt_dir.name.startswith('_'):
            prompt_file = prompt_dir / "prompt.json"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                task_id = data.get("id", prompt_dir.name)
                mapping[task_id] = data.get("difficulty", "unknown")
    return mapping


def create_evaluator_comparison(data, output_dir):
    """Chart 1: Grouped bar chart — pass rate of all 8 evaluators for all 6 models."""
    fig, ax = plt.subplots(figsize=(14, 8))
    models = list(data["models"].keys())
    evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional', 'Scalability']

    model_pass_rates = {m: {e: [] for e in evaluators} for m in models}

    for model_name, model_info in data["models"].items():
        for task_data in model_info["tasks"].values():
            for evaluator in evaluators:
                _, pass_rate = get_evaluator_stats(task_data, evaluator)
                model_pass_rates[model_name][evaluator].append(pass_rate)

    means = {}
    for m in models:
        means[m] = {}
        for e in evaluators:
            rates = model_pass_rates[m][e]
            means[m][e] = np.mean(rates) * 100 if rates else 0.0

    x = np.arange(len(evaluators))
    width = 0.15

    for i, model in enumerate(models):
        vals = [means[model][e] for e in evaluators]
        offset = (i - len(models) / 2 + 0.5) * width
        ax.bar(x + offset, vals, width, label=model,
               color=get_model_color(model), edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Evaluator', fontweight='bold')
    ax.set_ylabel('Mean Pass Rate (%)', fontweight='bold')
    ax.set_title('Model Performance Comparison by Evaluator (6 samples)\nMean across tasks',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(evaluators)
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '01_evaluator_comparison.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 01_evaluator_comparison.png")


def create_functional_by_difficulty(data, output_dir):
    """Chart 2: Grouped bar chart — functional pass rate by difficulty level per model."""
    difficulty_map = load_difficulty_map()

    models = list(data["models"].keys())
    difficulties = ['easy', 'medium', 'hard']

    model_diff_rates = {m: {d: [] for d in difficulties} for m in models}

    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            diff = difficulty_map.get(task_id, 'unknown')
            if diff not in difficulties:
                continue
            _, pass_rate = get_evaluator_stats(task_data, "Functional")
            model_diff_rates[model_name][diff].append(pass_rate)

    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(difficulties))
    width = 0.15

    diff_labels = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}

    for i, model in enumerate(models):
        vals = []
        for d in difficulties:
            rates = model_diff_rates[model][d]
            vals.append(np.mean(rates) * 100 if rates else 0.0)
        offset = (i - len(models) / 2 + 0.5) * width
        ax.bar(x + offset, vals, width, label=model,
               color=get_model_color(model), edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Difficulty Level', fontweight='bold')
    ax.set_ylabel('Functional Pass Rate (%)', fontweight='bold')
    ax.set_title('Functional Correctness by Task Difficulty\n(Mean across 6 samples)',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([diff_labels[d] for d in difficulties])
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '02_functional_by_difficulty.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 02_functional_by_difficulty.png")


def create_overall_ranking(data, output_dir):
    """Chart 3: 3 grouped bars per model — quality, functional, scalability."""
    models = list(data["models"].keys())
    quality_evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon']

    model_scores = {m: {'quality': [], 'functional': [], 'scalability': []} for m in models}

    for model_name, model_info in data["models"].items():
        for task_data in model_info["tasks"].values():
            qual_rates = []
            for ev in quality_evaluators:
                _, pr = get_evaluator_stats(task_data, ev)
                qual_rates.append(pr)
            model_scores[model_name]['quality'].append(np.mean(qual_rates) if qual_rates else 0.0)

            _, func_pr = get_evaluator_stats(task_data, "Functional")
            model_scores[model_name]['functional'].append(func_pr)

            _, scal_pr = get_evaluator_stats(task_data, "Scalability")
            model_scores[model_name]['scalability'].append(scal_pr)

    means = {}
    for m in models:
        means[m] = {
            'Quality': np.mean(model_scores[m]['quality']) * 100,
            'Functional': np.mean(model_scores[m]['functional']) * 100,
            'Scalability': np.mean(model_scores[m]['scalability']) * 100,
        }

    fig, ax = plt.subplots(figsize=(12, 7))
    categories = ['Quality', 'Functional', 'Scalability']
    x = np.arange(len(models))
    width = 0.25

    cat_colors = {'Quality': '#2c3e50', 'Functional': '#1abc9c', 'Scalability': '#e91e63'}

    for i, cat in enumerate(categories):
        vals = [means[m][cat] for m in models]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width, label=cat, color=cat_colors[cat],
                      edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Score (%)', fontweight='bold')
    ax.set_title('Overall Model Ranking: Quality vs. Functional vs. Scalability\n(Mean across tasks, 6 samples)',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend(title='Dimension')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '03_overall_ranking.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 03_overall_ranking.png")


def create_scalability_chart(data, output_dir):
    """Chart 4: Bar chart — scalability composite score per model."""
    models = list(data["models"].keys())

    model_scores = {m: [] for m in models}

    for model_name, model_info in data["models"].items():
        for task_data in model_info["tasks"].values():
            for sample in task_data.get("samples", []):
                details = sample.get("quality", {}).get("Scalability", {}).get("details", {})
                if details and "composite_score" in details:
                    model_scores[model_name].append(details["composite_score"])

    fig, ax = plt.subplots(figsize=(10, 7))

    names = []
    means_list = []
    mins = []
    maxs = []

    for model in models:
        scores = model_scores[model]
        if scores:
            names.append(model)
            means_list.append(np.mean(scores))
            mins.append(np.min(scores))
            maxs.append(np.max(scores))

    x = np.arange(len(names))
    bars = ax.bar(x, means_list, color=[get_model_color(m) for m in names],
                  edgecolor='black', linewidth=1)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Scalability Score', fontweight='bold')
    ax.set_title('Scalability Score per Model (6 samples)\nMean composite score across tasks',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, means_list):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.02,
                f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '04_scalability.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 04_scalability.png")


def create_maintainability_chart(data, output_dir):
    """Chart 5: Bar chart — maintainability index per model."""
    fig, ax = plt.subplots(figsize=(10, 7))

    models = []
    avg_mi = []

    for model_name, model_info in data["models"].items():
        mi_scores = []
        for task_data in model_info["tasks"].values():
            mean_score, _ = get_evaluator_stats(task_data, "Radon")
            if mean_score > 0:
                mi_scores.append(mean_score * 100)
        if mi_scores:
            models.append(model_name)
            avg_mi.append(np.mean(mi_scores))

    x = np.arange(len(models))
    bars = ax.bar(x, avg_mi, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Maintainability Index', fontweight='bold')
    ax.set_title('Maintainability Index by Model (6 samples)\nMean across tasks',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, avg_mi):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 2,
                f'{val:.1f}', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / '05_maintainability.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 05_maintainability.png")


def create_execution_times_chart(data, output_dir):
    """Chart 6: Bar chart — mean execution time per model."""
    fig, ax = plt.subplots(figsize=(10, 7))

    models = []
    avg_times = []

    for model_name, model_info in data["models"].items():
        times = []
        for task_data in model_info["tasks"].values():
            for sample in task_data.get("samples", []):
                t = sample.get("quality", {}).get("Execution", {}).get("details", {}).get("execution_time_seconds", 0)
                if t > 0:
                    times.append(t)
        if times:
            models.append(model_name)
            avg_times.append(np.mean(times))

    x = np.arange(len(models))
    bars = ax.bar(x, avg_times, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Mean Execution Time (seconds)', fontweight='bold')
    ax.set_title('Mean Execution Time by Model (6 samples)\nLower is better',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, avg_times):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                f'{val:.3f}s', ha='center', va='bottom', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '06_execution_times.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 06_execution_times.png")


def create_lines_of_code_chart(data, output_dir):
    """Chart 7: Bar chart — mean lines of code per model."""
    fig, ax = plt.subplots(figsize=(10, 7))

    models = []
    avg_locs = []

    for model_name, model_info in data["models"].items():
        locs = []
        for task_data in model_info["tasks"].values():
            for sample in task_data.get("samples", []):
                loc = sample.get("quality", {}).get("Radon", {}).get("details", {}).get("lines_of_code", 0)
                if loc > 0:
                    locs.append(loc)
        if locs:
            models.append(model_name)
            avg_locs.append(np.mean(locs))

    x = np.arange(len(models))
    bars = ax.bar(x, avg_locs, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Mean Lines of Code', fontweight='bold')
    ax.set_title('Mean Lines of Code by Model (6 samples)\nLower is often better',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, avg_locs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                f'{val:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '07_lines_of_code.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 07_lines_of_code.png")


def create_sample_consistency(data, output_dir):
    """Chart 8: Grouped bar chart — pass rate per evaluator per model with pass fractions."""
    fig, ax = plt.subplots(figsize=(16, 9))
    models = list(data["models"].keys())
    evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional', 'Scalability']

    model_rates = {m: {e: [] for e in evaluators} for m in models}
    model_counts = {m: {e: [] for e in evaluators} for m in models}

    for model_name, model_info in data["models"].items():
        for task_data in model_info["tasks"].values():
            samples = task_data.get("samples", [])
            for evaluator in evaluators:
                passes = []
                for sample in samples:
                    if evaluator == "Functional":
                        passed = sample.get("functional", {}).get("test_passed", False)
                    else:
                        eval_data = sample.get("quality", {}).get(evaluator, {})
                        passed = eval_data.get("passed", False) if eval_data else False
                    passes.append(1 if passed else 0)
                rate = sum(passes) / len(passes) if passes else 0.0
                model_rates[model_name][evaluator].append(rate)
                model_counts[model_name][evaluator].append(f"{sum(passes)}/{len(passes)}")

    avg_rates = {}
    avg_counts = {}
    for m in models:
        avg_rates[m] = {}
        avg_counts[m] = {}
        for e in evaluators:
            avg_rates[m][e] = np.mean(model_rates[m][e]) * 100 if model_rates[m][e] else 0.0
            avg_counts[m][e] = model_counts[m][e][0] if model_counts[m][e] else "0/0"

    x = np.arange(len(evaluators))
    width = 0.15

    for i, model in enumerate(models):
        vals = [avg_rates[model][e] for e in evaluators]
        counts = [avg_counts[model][e] for e in evaluators]
        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width, label=model,
                      color=get_model_color(model), edgecolor='black', linewidth=0.5)

        for bar, count in zip(bars, counts):
            height = bar.get_height()
            if height > 5:
                ax.text(bar.get_x() + bar.get_width() / 2., height / 2,
                        count, ha='center', va='center',
                        fontsize=7, fontweight='bold', color='white')

    ax.set_xlabel('Evaluator', fontweight='bold')
    ax.set_ylabel('Mean Pass Rate (%)', fontweight='bold')
    ax.set_title('Sample Consistency: Pass Fractions per Model and Evaluator (6 samples)\nLabels show fraction (e.g., 4/6 = 4 passed out of 6)',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(evaluators)
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '08_sample_consistency.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 08_sample_consistency.png")


def create_generation_speed(data, output_dir):
    """Chart 9: Bar chart — tokens per second per model."""
    fig, ax = plt.subplots(figsize=(12, 7))

    model_speeds = {}
    model_tokens = {}

    metadata_dir = Path("generated_code")
    for metadata_file in sorted(metadata_dir.glob("metadata_*.json")):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            for result in metadata.get("results", []):
                if result.get("status") == "success":
                    model_name = result.get("model_name", "")
                    timing = result.get("timing", {})
                    if timing and timing.get("tokens_per_second"):
                        if model_name not in model_speeds:
                            model_speeds[model_name] = []
                            model_tokens[model_name] = []
                        model_speeds[model_name].append(timing["tokens_per_second"])
                        if timing.get("eval_count"):
                            model_tokens[model_name].append(timing["eval_count"])
        except Exception:
            pass

    if not model_speeds:
        print("[SKIP] No timing data found for generation speed chart")
        plt.close()
        return

    models = sorted(model_speeds.keys())
    avg_speeds = []
    avg_tokens = []

    for model in models:
        speeds = model_speeds[model]
        avg_speeds.append(np.mean(speeds))
        if model in model_tokens and model_tokens[model]:
            avg_tokens.append(np.mean(model_tokens[model]))
        else:
            avg_tokens.append(0)

    x = np.arange(len(models))
    bars = ax.bar(x, avg_speeds, color=[get_model_color(m.replace(":", "_")) for m in models],
                  edgecolor='black', linewidth=1)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Tokens per Second', fontweight='bold')
    ax.set_title('Code Generation Speed by Model\n(Higher is faster)',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    for bar, speed, tokens in zip(bars, avg_speeds, avg_tokens):
        height = bar.get_height()
        label = f'{speed:.1f}'
        if tokens > 0:
            label += f'\n({tokens:.0f} tok)'
        ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                label, ha='center', va='bottom', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '09_generation_speed.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 09_generation_speed.png")


def main():
    print("=" * 70)
    print("LLM MODEL COMPARISON — GRAPH GENERATION (9 charts)")
    print("=" * 70)

    print("\nLoading merged evaluation data...")
    data = load_results()
    print(f"[OK] Loaded {data['total_models']} models and {data['total_tasks']} tasks (6 samples each)")

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Graphs will be saved to: {GRAPH_DIR}\n")

    print("Creating charts...\n")
    print("=" * 70)

    create_evaluator_comparison(data, GRAPH_DIR)
    create_functional_by_difficulty(data, GRAPH_DIR)
    create_overall_ranking(data, GRAPH_DIR)
    create_scalability_chart(data, GRAPH_DIR)
    create_maintainability_chart(data, GRAPH_DIR)
    create_execution_times_chart(data, GRAPH_DIR)
    create_lines_of_code_chart(data, GRAPH_DIR)
    create_sample_consistency(data, GRAPH_DIR)
    create_generation_speed(data, GRAPH_DIR)

    print("=" * 70)
    print("\nALL 9 CHARTS CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n  Output: {GRAPH_DIR}")
    print("  1. 01_evaluator_comparison.png    — Pass rate all 8 evaluators")
    print("  2. 02_functional_by_difficulty.png — Functional pass rate by difficulty")
    print("  3. 03_overall_ranking.png          — Quality vs Functional vs Scalability")
    print("  4. 04_scalability.png              — Scalability composite score")
    print("  5. 05_maintainability.png          — Maintainability index (Radon)")
    print("  6. 06_execution_times.png          — Mean execution time")
    print("  7. 07_lines_of_code.png            — Mean lines of code")
    print("  8. 08_sample_consistency.png       — Pass fractions (6 samples)")
    print("  9. 09_generation_speed.png         — Generation speed (tok/s)")
    print("=" * 70)


if __name__ == "__main__":
    main()