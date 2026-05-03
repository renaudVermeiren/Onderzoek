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

# Define consistent colors for models (up to 6 models)
MODEL_COLORS = {
    'deepseek-coder-v2_latest': '#e74c3c',  # Red
    'gemma4_latest': '#3498db',              # Blue  
    'llama3_latest': '#2ecc71',              # Green
    'starcoder2_latest': '#f39c12',          # Orange
    'codellama': '#9b59b6',                  # Purple
    'mistral': '#1abc9c',                    # Teal
}

# Evaluator colors
EVAL_COLORS = {
    'Syntax': '#2ecc71',
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
        print(f"❌ Error: {overall_file} not found")
        sys.exit(1)
    
    with open(overall_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_model_color(model_name):
    """Get consistent color for a model."""
    return MODEL_COLORS.get(model_name, '#95a5a6')  # Default gray


def create_evaluator_comparison_bars(data, output_dir):
    """Chart 1: Side-by-side bar chart comparing all evaluators across models."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    models = list(data["models"].keys())
    evaluators = ['Syntax', 'Security', 'Execution', 'Performance', 'Radon', 'Functional']
    
    # Prepare data
    model_data = {model: {evaluator: 0 for evaluator in evaluators} for model in models}
    
    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            quality = task_data.get("quality", {})
            
            # Count passes for each evaluator
            if quality.get("Syntax", {}).get("passed", False):
                model_data[model_name]["Syntax"] += 1
            if quality.get("Security", {}).get("passed", False):
                model_data[model_name]["Security"] += 1
            if quality.get("Execution", {}).get("passed", False):
                model_data[model_name]["Execution"] += 1
            if quality.get("Performance", {}).get("passed", False):
                model_data[model_name]["Performance"] += 1
            if quality.get("Radon", {}).get("passed", False):
                model_data[model_name]["Radon"] += 1
            
            # Functional test
            if task_data.get("functional", {}).get("test_passed", False):
                model_data[model_name]["Functional"] += 1
    
    # Convert to percentages
    num_tasks = len(list(data["models"].values())[0]["tasks"])
    for model in models:
        for evaluator in evaluators:
            model_data[model][evaluator] = (model_data[model][evaluator] / num_tasks) * 100
    
    # Create grouped bar chart
    x = np.arange(len(evaluators))
    width = 0.15
    
    for i, model in enumerate(models):
        values = [model_data[model][eval] for eval in evaluators]
        offset = (i - len(models)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=model, color=get_model_color(model), 
               edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Evaluator', fontweight='bold')
    ax.set_ylabel('Pass Rate (%)', fontweight='bold')
    ax.set_title('Model Performance Comparison by Evaluator\n(Higher is better)', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(evaluators)
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '01_evaluator_comparison.png', bbox_inches='tight')
    plt.close()
    print("✅ Created: 01_evaluator_comparison.png")


def create_task_success_bars(data, output_dir):
    """Chart 2: Grouped bar chart showing success rate per task for each model."""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    models = list(data["models"].keys())
    tasks = sorted(list(list(data["models"].values())[0]["tasks"].keys()))
    
    # Prepare data
    task_results = {task: {model: 0 for model in models} for task in tasks}
    
    for model_name, model_info in data["models"].items():
        for task_id, task_data in model_info["tasks"].items():
            if task_data.get("overall_passed", False):
                task_results[task_id][model_name] = 100
            else:
                # Count partial success (how many evaluators passed)
                quality = task_data.get("quality", {})
                passed = sum(1 for q in quality.values() if q.get("passed", False))
                task_results[task_id][model_name] = (passed / 6) * 100
    
    # Create grouped bar chart
    x = np.arange(len(tasks))
    width = 0.12
    
    for i, model in enumerate(models):
        values = [task_results[task][model] for task in tasks]
        offset = (i - len(models)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=model, color=get_model_color(model),
               edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Task', fontweight='bold')
    ax.set_ylabel('Success Score (%)', fontweight='bold')
    ax.set_title('Task Performance by Model\n(100% = all evaluators passed, 0% = all failed)', 
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, rotation=45, ha='right')
    ax.legend(title='Models', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '02_task_performance.png', bbox_inches='tight')
    plt.close()
    print("✅ Created: 02_task_performance.png")


def create_maintainability_bars(data, output_dir):
    """Chart 3: Bar chart comparing maintainability index per model."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    models = []
    avg_mi = []
    min_mi = []
    max_mi = []
    
    for model_name, model_info in data["models"].items():
        mi_scores = []
        for task_data in model_info["tasks"].values():
            mi = task_data.get("quality", {}).get("Radon", {}).get("details", {}).get("maintainability_index", 0)
            if mi > 0:
                mi_scores.append(mi)
        
        if mi_scores:
            models.append(model_name)
            avg_mi.append(np.mean(mi_scores))
            min_mi.append(np.min(mi_scores))
            max_mi.append(np.max(mi_scores))
    
    x = np.arange(len(models))
    
    # Create bars with error range
    bars = ax.bar(x, avg_mi, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)
    
    # Add error bars showing min-max range
    for i, (avg, min_val, max_val) in enumerate(zip(avg_mi, min_mi, max_mi)):
        ax.errorbar(i, avg, yerr=[[avg - min_val], [max_val - avg]], 
                   fmt='none', color='black', capsize=5, capthick=2)
    
    # Add reference lines
    ax.axhline(80, color='#2ecc71', linestyle='--', linewidth=2, alpha=0.7, label='Excellent (≥80)')
    ax.axhline(60, color='#f39c12', linestyle='--', linewidth=2, alpha=0.7, label='Good (≥60)')
    ax.axhline(40, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7, label='Fair (≥40)')
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Maintainability Index', fontweight='bold')
    ax.set_title('Maintainability Index by Model\n(Error bars show min-max range)', 
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
    print("✅ Created: 03_maintainability.png")


def create_lines_of_code_bars(data, output_dir):
    """Chart 4: Bar chart comparing average lines of code per model."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    models = []
    avg_loc = []
    
    for model_name, model_info in data["models"].items():
        locs = []
        for task_data in model_info["tasks"].values():
            loc = task_data.get("quality", {}).get("Radon", {}).get("details", {}).get("lines_of_code", 0)
            if loc > 0:
                locs.append(loc)
        
        if locs:
            models.append(model_name)
            avg_loc.append(np.mean(locs))
    
    x = np.arange(len(models))
    bars = ax.bar(x, avg_loc, color=[get_model_color(m) for m in models],
                  edgecolor='black', linewidth=1)
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Average Lines of Code', fontweight='bold')
    ax.set_title('Code Size Comparison by Model\n(Lower is often better)', 
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / '04_lines_of_code.png', bbox_inches='tight')
    plt.close()
    print("✅ Created: 04_lines_of_code.png")


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
    print("✅ Created: 05_execution_times.png")


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
    print("✅ Created: 06_security_issues.png")


def create_model_ranking_bars(data, output_dir):
    """Chart 7: Horizontal bar chart ranking models by overall performance."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calculate overall score per model (average of all evaluator pass rates)
    model_scores = []
    
    for model_name, model_info in data["models"].items():
        scores = []
        for task_data in model_info["tasks"].values():
            quality = task_data.get("quality", {})
            # Count how many evaluators passed
            passed = sum(1 for q in quality.values() if q.get("passed", False))
            scores.append((passed / 6) * 100)  # 6 evaluators total
        
        avg_score = np.mean(scores)
        model_scores.append((model_name, avg_score))
    
    # Sort by score (descending)
    model_scores.sort(key=lambda x: x[1], reverse=True)
    
    models = [m for m, _ in model_scores]
    scores = [s for _, s in model_scores]
    
    # Create horizontal bar chart
    y = np.arange(len(models))
    bars = ax.barh(y, scores, color=[get_model_color(m) for m in models],
                   edgecolor='black', linewidth=1)
    
    ax.set_xlabel('Average Pass Rate (%)', fontweight='bold')
    ax.set_ylabel('Model', fontweight='bold')
    ax.set_title('Model Performance Ranking\n(Based on average pass rate across all evaluators)', 
                 fontweight='bold', pad=20)
    ax.set_yticks(y)
    ax.set_yticklabels(models)
    ax.set_xlim(0, 105)
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, scores)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                f'{score:.1f}%', ha='left', va='center', fontweight='bold')
    
    # Invert y-axis so best model is at top
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_dir / '07_model_ranking.png', bbox_inches='tight')
    plt.close()
    print("✅ Created: 07_model_ranking.png")


def main():
    """Main function to run all analyses."""
    print("=" * 70)
    print("📊 LLM MODEL COMPARISON ANALYSIS")
    print("=" * 70)
    
    # Determine results directory
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_path = Path("results")
        if not results_path.exists():
            print("❌ Error: results folder not found")
            sys.exit(1)
        
        eval_folders = [f for f in results_path.iterdir() if f.is_dir() and f.name.startswith("evaluation_")]
        if not eval_folders:
            print("❌ Error: No evaluation folders found")
            sys.exit(1)
        
        results_dir = str(sorted(eval_folders)[-1])
    
    print(f"\n📁 Analyzing results from: {results_dir}")
    
    # Create graphs output directory
    output_dir = Path("graphs") / Path(results_dir).name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 Graphs will be saved to: {output_dir}\n")
    
    # Load data
    print("📂 Loading evaluation data...")
    data = load_results(results_dir)
    print(f"✅ Loaded {data['total_models']} models and {data['total_tasks']} tasks\n")
    
    # Create all charts
    print("🎨 Creating comparison charts...\n")
    print("=" * 70)
    
    create_evaluator_comparison_bars(data, output_dir)
    create_task_success_bars(data, output_dir)
    create_maintainability_bars(data, output_dir)
    create_lines_of_code_bars(data, output_dir)
    create_execution_time_boxplot(data, output_dir)
    create_security_issues_bars(data, output_dir)
    create_model_ranking_bars(data, output_dir)
    
    print("=" * 70)
    print("\n✅ ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Generated 7 comparison charts in: {output_dir}")
    print("\nCharts created:")
    print("  1. Evaluator comparison (side-by-side bars)")
    print("  2. Task performance (grouped bars)")
    print("  3. Maintainability index (bars with error ranges)")
    print("  4. Lines of code (simple bars)")
    print("  5. Execution times (boxplot)")
    print("  6. Security issues (grouped bars by severity)")
    print("  7. Model ranking (horizontal bars)")
    print("\nEach model has a consistent color across all charts:")
    for model, color in MODEL_COLORS.items():
        if model in data["models"]:
            print(f"  • {model}: {color}")
    print("=" * 70)


if __name__ == "__main__":
    main()
