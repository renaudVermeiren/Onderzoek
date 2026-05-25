#!/usr/bin/env python3
"""
LLM Model Comparison Analysis - Bar Charts & Boxplots Only

This script creates simplified bar charts and boxplots for comparing
LLM models across different metrics and tasks.

All graphs are saved to the 'graphs/' folder.

Usage:
    python analyze_results.py
    python analyze_results.py results/evaluation_20260503_152114
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Set consistent style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Define consistent colors for models (up to 8 models)
MODEL_COLORS = {
    'deepseek-coder-v2_latest': '#e74c3c',   # Red
    'gemma4_latest': '#3498db',               # Blue  
    'llama3_latest': '#2ecc71',               # Green
    'mistral_latest': '#f39c12',              # Orange
    'qwen2.5-coder_latest': '#9b59b6',        # Purple
    'phi4-mini_latest': '#1abc9c',             # Teal
    'qwen3.5_latest': '#e91e63',              # Pink
    'codellama': '#95a5a6',                   # Gray
}

# Evaluator colors
EVAL_COLORS = {
    'Syntax': '#2ecc71',
    'Style': '#e67e22',
    'Security': '#3498db',
    'Execution': '#f39c12',
    'Performance': '#e74c3c',
    'Radon': '#9b59b6',
    'Functional': '#1abc9c'
}


def load_results(results_dir):
    """Load overall_results.json from the results directory."""
    results_path = Path(results_dir)
    overall_file = results_path / "overall_results.json"
    
    if not overall_file.exists():
        print(f"[ERROR] {overall_file} not found")
        sys.exit(1)
    
    with open(overall_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_model_color(model_name):
    """Get consistent color for a model."""
    return MODEL_COLORS.get(model_name, '#95a5a6')  # Default gray


def get_task_statistics(task_data):
    """Extract sample statistics from task data."""
    return task_data.get("statistics", {})


def get_evaluator_stats(task_data, evaluator_name):
    """Get mean score and std dev for an evaluator from statistics.
    
    Returns:
        (mean_score, std_dev, pass_count_str) tuple
    """
    stats = get_task_statistics(task_data)
    eval_stats = stats.get(evaluator_name, {})
    mean_score = eval_stats.get("mean_score", 0.0)
    std_dev = eval_stats.get("std_dev", 0.0)
    pass_count = eval_stats.get("pass_count", "0/0")
    return mean_score, std_dev, pass_count


def get_functional_pass_fraction(task_data):
    """Get functional test pass fraction as string (e.g., '2/3')."""
    stats = get_task_statistics(task_data)
    func_stats = stats.get("Functional", {})
    return func_stats.get("pass_count", "0/0")


def load_task_categories():
    """Load prompt categories and map to merged categories for representative groups."""
    prompts_dir = Path("prompts")
    task_to_category = {}
    
    # Load individual task categories from prompt.json files
    for prompt_dir in prompts_dir.iterdir():
        if prompt_dir.is_dir():
            prompt_file = prompt_dir / "prompt.json"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                task_id = prompt_data.get("id", prompt_dir.name)
                original_category = prompt_data.get("category", "unknown")
                task_to_category[task_id] = original_category
    
    # Merge small categories into representative groups
    category_mapping = {
        "data_cleaning": "Data Cleaning",
        "data_transformation": "Data Transformation",
        "joins": "Joins & Aggregation",
        "performance": "Performance Optimization",
        # Merge small categories into "Data Operations"
        "data_loading": "Data Operations",
        "data_validation": "Data Operations",
        "data_filtering": "Data Operations",
        "time_series": "Data Operations",
    }
    
    # Map each task to its merged category
    task_to_merged = {}
    for task_id, original_cat in task_to_category.items():
        merged_cat = category_mapping.get(original_cat, "Other")
        task_to_merged[task_id] = merged_cat
    
    return task_to_merged


def create_evaluator_comparison_bars(data, output_dir):
    """Chart 1: Side-by-side bar chart comparing all evaluators across models.
    
    Shows mean pass rate with standard deviation error bars across 3 samples.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    models = list(data["models"].keys())
    evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional']
    
    # Prepare data: mean pass rate and std dev per model-evaluator
    model_data = {model: {evaluator: {"mean": 0.0, "std": 0.0} for evaluator in evaluators} for model in models}
    
    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            stats = get_task_statistics(task_data)
            
            for evaluator in evaluators:
                if evaluator in stats:
                    eval_stats = stats[evaluator]
                    pass_rate = eval_stats.get("pass_rate", 0.0)
                    std_dev = eval_stats.get("std_dev", 0.0)
                    
                    # Accumulate for averaging across tasks
                    if model_data[model_name][evaluator]["mean"] == 0.0:
                        model_data[model_name][evaluator]["mean"] = pass_rate
                        model_data[model_name][evaluator]["std"] = std_dev
                    else:
                        # Average pass rates and propagate std dev
                        old_mean = model_data[model_name][evaluator]["mean"]
                        old_std = model_data[model_name][evaluator]["std"]
                        model_data[model_name][evaluator]["mean"] = (old_mean + pass_rate) / 2
                        model_data[model_name][evaluator]["std"] = np.sqrt((old_std**2 + std_dev**2) / 2)
    
    # Convert to percentages
    for model in models:
        for evaluator in evaluators:
            model_data[model][evaluator]["mean"] *= 100
            model_data[model][evaluator]["std"] *= 100
    
    # Create grouped bar chart
    x = np.arange(len(evaluators))
    width = 0.15
    
    for i, model in enumerate(models):
        means = [model_data[model][eval]["mean"] for eval in evaluators]
        stds = [model_data[model][eval]["std"] for eval in evaluators]
        offset = (i - len(models)/2 + 0.5) * width
        
        bars = ax.bar(x + offset, means, width, label=model, color=get_model_color(model), 
               edgecolor='black', linewidth=0.5)
        
        # Add error bars (std dev)
        ax.errorbar(x + offset, means, yerr=stds, fmt='none', 
                   color='black', capsize=3, capthick=1, alpha=0.7)
    
    ax.set_xlabel('Evaluator', fontweight='bold')
    ax.set_ylabel('Mean Pass Rate (%)', fontweight='bold')
    ax.set_title('Model Performance Comparison by Evaluator (3 samples)\nMean ± Std Dev across tasks',
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


def create_task_success_bars(data, output_dir):
    """Chart 2: Grouped bar chart showing average success rate per task category for each model.
    
    Uses mean scores from sample statistics with standard deviation error bars.
    """
    models = list(data["models"].keys())
    
    # Load category mapping
    task_to_merged = load_task_categories()
    
    # Collect scores per merged category per model (mean ± std)
    category_scores = {model: {} for model in models}
    
    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            # Get merged category for this task
            merged_category = task_to_merged.get(task_id, "Other")
            
            # Calculate score from statistics: average of all evaluator mean scores
            stats = get_task_statistics(task_data)
            if stats:
                eval_scores = []
                eval_stds = []
                for eval_name, eval_stats in stats.items():
                    if eval_name != "Functional" and "mean_score" in eval_stats:
                        eval_scores.append(eval_stats["mean_score"])
                        eval_stds.append(eval_stats.get("std_dev", 0.0))
                
                if eval_scores:
                    score = np.mean(eval_scores) * 100
                    std = np.sqrt(np.mean([s**2 for s in eval_stds])) * 100 if eval_stds else 0.0
                else:
                    score = 0.0
                    std = 0.0
            else:
                score = 0.0
                std = 0.0
            
            # Add to category
            if merged_category not in category_scores[model_name]:
                category_scores[model_name][merged_category] = {"scores": [], "stds": []}
            category_scores[model_name][merged_category]["scores"].append(score)
            category_scores[model_name][merged_category]["stds"].append(std)
    
    # Calculate averages per category
    categories = sorted(list(set(cat for model_cats in category_scores.values() for cat in model_cats.keys())))
    
    category_averages = {model: {} for model in models}
    category_stds = {model: {} for model in models}
    
    for model in models:
        for category in categories:
            scores = category_scores[model].get(category, {}).get("scores", [])
            stds = category_scores[model].get(category, {}).get("stds", [])
            if scores:
                category_averages[model][category] = np.mean(scores)
                category_stds[model][category] = np.sqrt(np.mean([s**2 for s in stds])) if stds else 0.0
            else:
                category_averages[model][category] = 0.0
                category_stds[model][category] = 0.0
    
    # Count tasks per category for labels
    task_counts = {}
    for task_id, merged_cat in task_to_merged.items():
        task_counts[merged_cat] = task_counts.get(merged_cat, 0) + 1
    
    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(categories))
    width = 0.15
    
    for i, model in enumerate(models):
        means = [category_averages[model][cat] for cat in categories]
        stds = [category_stds[model][cat] for cat in categories]
        offset = (i - len(models)/2 + 0.5) * width
        
        bars = ax.bar(x + offset, means, width, label=model, color=get_model_color(model),
               edgecolor='black', linewidth=0.5)
        
        # Add error bars (std dev)
        ax.errorbar(x + offset, means, yerr=stds, fmt='none', 
                   color='black', capsize=3, capthick=1, alpha=0.7)
    
    # Create category labels with task counts
    category_labels = [f"{cat}\n({task_counts.get(cat, 0)} tasks)" for cat in categories]
    
    ax.set_xlabel('Task Category', fontweight='bold')
    ax.set_ylabel('Average Quality Score (%)', fontweight='bold')
    ax.set_title('Average Task Performance by Category and Model (3 samples)\nMean ± Std Dev of evaluator scores',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(category_labels)
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '02_task_performance.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 02_task_performance.png")


def create_maintainability_bars(data, output_dir):
    """Chart 3: Bar chart comparing maintainability index per model.
    
    Uses mean scores from sample statistics with standard deviation error bars.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    models = []
    avg_mi = []
    std_mi = []
    
    for model_name, model_info in data["models"].items():
        mi_scores = []
        mi_stds = []
        
        for task_data in model_info["tasks"].values():
            mean, std, _ = get_evaluator_stats(task_data, "Radon")
            if mean > 0:
                # Radon score is 0-1 scale, convert to 0-100
                mi_scores.append(mean * 100)
                mi_stds.append(std * 100)
        
        if mi_scores:
            models.append(model_name)
            avg_mi.append(np.mean(mi_scores))
            # Propagate standard deviations
            std_mi.append(np.sqrt(np.mean([s**2 for s in mi_stds])) if mi_stds else 0.0)
    
    x = np.arange(len(models))
    
    # Create bars with std dev error bars
    bars = ax.bar(x, avg_mi, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)
    
    # Add error bars showing standard deviation
    for i, (avg, std) in enumerate(zip(avg_mi, std_mi)):
        ax.errorbar(i, avg, yerr=std, 
                   fmt='none', color='black', capsize=5, capthick=2)
    
    # Add reference lines
    ax.axhline(80, color='#2ecc71', linestyle='--', linewidth=2, alpha=0.7, label='Excellent (≥80)')
    ax.axhline(60, color='#f39c12', linestyle='--', linewidth=2, alpha=0.7, label='Good (≥60)')
    ax.axhline(40, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7, label='Fair (≥40)')
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Maintainability Index', fontweight='bold')
    ax.set_title('Maintainability Index by Model (3 samples)\nMean ± Std Dev across tasks', 
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend(loc='upper right')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, avg_mi)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / '03_maintainability.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 03_maintainability.png")


def create_lines_of_code_boxplot(data, output_dir):
    """Chart 4: Boxplot comparing lines of code distribution per model."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    model_locs = {}
    
    for model_name, model_info in data["models"].items():
        locs = []
        for task_data in model_info["tasks"].values():
            loc = task_data.get("quality", {}).get("Radon", {}).get("details", {}).get("lines_of_code", 0)
            if loc > 0:
                locs.append(loc)
        
        if locs:
            model_locs[model_name] = locs
    
    if model_locs:
        # Create boxplot
        bp = ax.boxplot(model_locs.values(), tick_labels=model_locs.keys(),
                        patch_artist=True, showmeans=True, meanline=True)
        
        # Color the boxes
        for patch, model in zip(bp['boxes'], model_locs.keys()):
            patch.set_facecolor(get_model_color(model))
            patch.set_alpha(0.7)
        
        # Color the mean lines
        for mean_line in bp['means']:
            mean_line.set_color('red')
            mean_line.set_linewidth(2)
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Lines of Code', fontweight='bold')
    ax.set_title('Lines of Code Distribution by Model\n(Red line = mean, box = quartiles, lower is often better)',
                 fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_dir / '04_lines_of_code.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 04_lines_of_code.png")


def create_execution_time_boxplot(data, output_dir):
    """Chart 5: Boxplot comparing execution times across models."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    model_times = {}
    
    for model_name, model_info in data["models"].items():
        times = []
        for task_data in model_info["tasks"].values():
            exec_time = task_data.get("quality", {}).get("Execution", {}).get("details", {}).get("execution_time_seconds", 0)
            if exec_time > 0:
                times.append(exec_time)
        
        if times:
            model_times[model_name] = times
    
    if model_times:
        # Create boxplot
        bp = ax.boxplot(model_times.values(), tick_labels=model_times.keys(), 
                        patch_artist=True, showmeans=True, meanline=True)
        
        # Color the boxes
        for patch, model in zip(bp['boxes'], model_times.keys()):
            patch.set_facecolor(get_model_color(model))
            patch.set_alpha(0.7)
        
        # Color the mean lines
        for mean_line in bp['means']:
            mean_line.set_color('red')
            mean_line.set_linewidth(2)
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Execution Time (seconds)', fontweight='bold')
    ax.set_title('Execution Time Distribution by Model\n(Red line = mean, box = quartiles)', 
                 fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_dir / '05_execution_times.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 05_execution_times.png")


def create_security_issues_bars(data, output_dir):
    """Chart 6: Grouped bar chart showing security issues by severity per model."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    models = list(data["models"].keys())
    severities = ['Low', 'Medium', 'High']
    
    # Prepare data
    security_data = {model: {'Low': 0, 'Medium': 0, 'High': 0} for model in models}
    
    for model_name, model_info in data["models"].items():
        for task_data in model_info["tasks"].values():
            details = task_data.get("quality", {}).get("Security", {}).get("details", {})
            security_data[model_name]['Low'] += details.get("low_severity", 0)
            security_data[model_name]['Medium'] += details.get("medium_severity", 0)
            security_data[model_name]['High'] += details.get("high_severity", 0)
    
    # Create grouped bar chart
    x = np.arange(len(models))
    width = 0.25
    
    colors_severity = {'Low': '#f1c40f', 'Medium': '#f39c12', 'High': '#e74c3c'}
    
    for i, severity in enumerate(severities):
        values = [security_data[model][severity] for model in models]
        offset = (i - 1) * width
        ax.bar(x + offset, values, width, label=severity, color=colors_severity[severity],
               edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Number of Security Issues', fontweight='bold')
    ax.set_title('Security Issues by Severity and Model\n(Lower is better)', 
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend(title='Severity')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '06_security_issues.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 06_security_issues.png")


def create_model_ranking_bars(data, output_dir):
    """Chart 7: Horizontal bar chart ranking models by overall performance.
    
    Uses mean scores from sample statistics with standard deviation error bars.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calculate overall score per model (average of all evaluator mean scores)
    model_scores = []
    model_stds = []
    
    for model_name, model_info in data["models"].items():
        task_scores = []
        task_stds = []
        
        for task_data in model_info["tasks"].values():
            stats = get_task_statistics(task_data)
            if stats:
                eval_scores = []
                eval_stds = []
                for eval_name, eval_stats in stats.items():
                    if eval_name != "Functional" and "mean_score" in eval_stats:
                        eval_scores.append(eval_stats["mean_score"])
                        eval_stds.append(eval_stats.get("std_dev", 0.0))
                
                if eval_scores:
                    task_mean = np.mean(eval_scores)
                    task_std = np.sqrt(np.mean([s**2 for s in eval_stds])) if eval_stds else 0.0
                    task_scores.append(task_mean)
                    task_stds.append(task_std)
        
        if task_scores:
            avg_score = np.mean(task_scores) * 100
            avg_std = np.sqrt(np.mean([s**2 for s in task_stds])) * 100 if task_stds else 0.0
            model_scores.append((model_name, avg_score, avg_std))
    
    # Sort by score (descending)
    model_scores.sort(key=lambda x: x[1], reverse=True)
    
    models = [m for m, _, _ in model_scores]
    scores = [s for _, s, _ in model_scores]
    stds = [s for _, _, s in model_scores]
    
    # Create horizontal bar chart
    y = np.arange(len(models))
    bars = ax.barh(y, scores, xerr=stds, color=[get_model_color(m) for m in models],
                   edgecolor='black', linewidth=1, capsize=5)
    
    ax.set_xlabel('Average Quality Score (%)', fontweight='bold')
    ax.set_ylabel('Model', fontweight='bold')
    ax.set_title('Model Performance Ranking (3 samples)\nMean ± Std Dev across all evaluators and tasks', 
                 fontweight='bold', pad=20)
    ax.set_yticks(y)
    ax.set_yticklabels(models)
    ax.set_xlim(0, 105)
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (bar, score, std) in enumerate(zip(bars, scores, stds)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                f'{score:.1f}±{std:.1f}', ha='left', va='center', fontweight='bold', fontsize=9)
    
    # Invert y-axis so best model is at top
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_dir / '07_model_ranking.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 07_model_ranking.png")


def create_sample_consistency_bars(data, output_dir):
    """Chart 8: Grouped bar chart showing sample consistency (pass fractions) per model-evaluator.
    
    Shows how many samples passed out of 3 for each evaluator and model.
    Displays fractions like '2/3' on the bars.
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    models = list(data["models"].keys())
    evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional']
    
    # Prepare data: pass fractions (e.g., "2/3") and pass rates per model-evaluator
    model_data = {model: {evaluator: {"pass_rate": 0.0, "pass_count": "0/0"} 
                         for evaluator in evaluators} for model in models}
    
    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            stats = get_task_statistics(task_data)
            
            for evaluator in evaluators:
                if evaluator in stats:
                    eval_stats = stats[evaluator]
                    pass_rate = eval_stats.get("pass_rate", 0.0)
                    pass_count = eval_stats.get("pass_count", "0/0")
                    
                    # Accumulate pass rates for averaging
                    old_rate = model_data[model_name][evaluator]["pass_rate"]
                    model_data[model_name][evaluator]["pass_rate"] = (old_rate + pass_rate) / 2
                    
                    # Keep the pass count string (just use latest for display)
                    model_data[model_name][evaluator]["pass_count"] = pass_count
    
    # Convert to percentages
    for model in models:
        for evaluator in evaluators:
            model_data[model][evaluator]["pass_rate"] *= 100
    
    # Create grouped bar chart
    x = np.arange(len(evaluators))
    width = 0.15
    
    for i, model in enumerate(models):
        pass_rates = [model_data[model][eval]["pass_rate"] for eval in evaluators]
        pass_counts = [model_data[model][eval]["pass_count"] for eval in evaluators]
        offset = (i - len(models)/2 + 0.5) * width
        
        bars = ax.bar(x + offset, pass_rates, width, label=model, 
                      color=get_model_color(model), edgecolor='black', linewidth=0.5)
        
        # Add pass fraction labels on bars (e.g., "2/3")
        for bar, count in zip(bars, pass_counts):
            height = bar.get_height()
            if height > 5:  # Only show label if bar is tall enough
                ax.text(bar.get_x() + bar.get_width()/2., height/2,
                       count, ha='center', va='center', 
                       fontsize=7, fontweight='bold', color='white')
    
    ax.set_xlabel('Evaluator', fontweight='bold')
    ax.set_ylabel('Mean Pass Rate (%)', fontweight='bold')
    ax.set_title('Sample Consistency: Pass Fractions per Model and Evaluator (3 samples)\nLabels show fraction (e.g., 2/3 = 2 passed out of 3)',
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


def main():
    """Main function to run all analyses."""
    print("=" * 70)
    print("LLM MODEL COMPARISON ANALYSIS")
    print("=" * 70)
    
    # Determine results directory
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_path = Path("results")
        if not results_path.exists():
            print("[ERROR] results folder not found")
            sys.exit(1)
        
        eval_folders = [f for f in results_path.iterdir() if f.is_dir() and f.name.startswith("evaluation_")]
        if not eval_folders:
            print("[ERROR] No evaluation folders found")
            sys.exit(1)
        
        results_dir = str(sorted(eval_folders)[-1])
    
    print(f"\nAnalyzing results from: {results_dir}")
    
    # Create graphs output directory
    output_dir = Path("graphs") / Path(results_dir).name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Graphs will be saved to: {output_dir}\n")
    
    # Load data
    print("Loading evaluation data...")
    data = load_results(results_dir)
    print(f"[OK] Loaded {data['total_models']} models and {data['total_tasks']} tasks\n")
    
    # Create all charts
    print("Creating comparison charts...\n")
    print("=" * 70)
    
    create_evaluator_comparison_bars(data, output_dir)
    create_task_success_bars(data, output_dir)
    create_maintainability_bars(data, output_dir)
    create_lines_of_code_boxplot(data, output_dir)
    create_execution_time_boxplot(data, output_dir)
    create_security_issues_bars(data, output_dir)
    create_model_ranking_bars(data, output_dir)
    create_sample_consistency_bars(data, output_dir)
    
    print("=" * 70)
    print("\nANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated 8 comparison charts in: {output_dir}")
    print("\nCharts created:")
    print("  1. Evaluator comparison (side-by-side bars with std dev)")
    print("  2. Task performance (grouped bars with std dev)")
    print("  3. Maintainability index (bars with std dev)")
    print("  4. Lines of code (boxplot)")
    print("  5. Execution times (boxplot)")
    print("  6. Security issues (grouped bars by severity)")
    print("  7. Model ranking (horizontal bars with std dev)")
    print("  8. Sample consistency (pass fractions: 2/3, 3/3, etc.)")
    print("\nEach model has a consistent color across all charts:")
    for model, color in MODEL_COLORS.items():
        if model in data["models"]:
            print(f"  • {model}: {color}")
    print("=" * 70)


if __name__ == "__main__":
    main()
