#!/usr/bin/env python3
"""
Code Evaluation Script

This script evaluates all generated code from the 20 ETL tasks.
It runs both quality checks (syntax, security, etc.) and functional tests.
Results are organized per model and saved in the results folder.

Usage:
    python evaluate.py
"""

import sys
import json
import shutil
import subprocess
import tempfile
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR, RESULTS_DIR, NUM_SAMPLES
from core.evaluators.syntax_evaluator import SyntaxEvaluator
from core.evaluators.security_evaluator import SecurityEvaluator
from core.evaluators.execution_evaluator import ExecutionEvaluator
from core.evaluators.performance_evaluator import PerformanceEvaluator
from core.evaluators.radon_evaluator import RadonEvaluator
from core.evaluators.functional_test_evaluator import FunctionalTestEvaluator
from core.evaluators.style_evaluator import StyleEvaluator


def find_generated_scripts(task_folder: Path) -> List[Path]:
    """Find all generated script versions (v1, v2, v3, etc.) in a task folder."""
    scripts = sorted(task_folder.glob("generated_script_v*.py"))
    return scripts


def load_script_content(script_path: Path) -> str:
    """Load the content of a generated script."""
    if script_path.exists():
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def run_quality_evaluation_for_sample(script_path: Path, model_name: str, task_id: str) -> Dict[str, Any]:
    """
    Run all quality evaluators on a single generated script sample.
    
    Returns:
        Dictionary with results from all quality evaluators
    """
    code_content = load_script_content(script_path)
    
    if not code_content:
        return {
            "error": f"No generated script found: {script_path.name}",
            "evaluations": {}
        }
    
    metadata = {
        "model_name": model_name,
        "task_id": task_id
    }
    
    evaluators = [
        ("Syntax", SyntaxEvaluator()),
        ("Style", StyleEvaluator()),
        ("Security", SecurityEvaluator()),
        ("Execution", ExecutionEvaluator()),
        ("Performance", PerformanceEvaluator()),
        ("Radon", RadonEvaluator())
    ]
    
    evaluations = {}
    
    for eval_name, evaluator in evaluators:
        try:
            result = evaluator.evaluate(
                file_path=str(script_path.resolve()),
                code_content=code_content,
                metadata=metadata
            )
            
            evaluations[eval_name] = {
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "error_message": result.error_message if result.error_message else None
            }
        except Exception as e:
            evaluations[eval_name] = {
                "passed": False,
                "score": 0.0,
                "details": {},
                "error_message": str(e)
            }
    
    return {
        "error": None,
        "evaluations": evaluations
    }


def run_functional_test_for_sample(task_folder: Path, script_path: Path, timeout: int = 30) -> Dict[str, Any]:
    """
    Run functional test for a single sample by executing the script first, then running test.py.
    """
    test_file = task_folder / "test.py"
    
    if not test_file.exists():
        return {
            "test_ran": False,
            "test_passed": False,
            "error": "test.py not found",
            "stdout": "",
            "stderr": ""
        }
    
    temp_dir = None
    try:
        # Create a temporary directory and copy all task artifacts
        temp_dir = tempfile.mkdtemp(prefix="func_test_")
        temp_path = Path(temp_dir)
        
        # Copy all files from task folder to temp directory
        for item in task_folder.iterdir():
            if item.is_file():
                shutil.copy2(item, temp_path / item.name)
            elif item.is_dir():
                shutil.copytree(item, temp_path / item.name)
        
        # Run the generated script first to produce output files
        exec_result = subprocess.run(
            ['python', str(script_path.name)],
            cwd=str(temp_path),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if exec_result.returncode != 0:
            return {
                "test_ran": True,
                "test_passed": False,
                "error": f"Script execution failed: {exec_result.stderr[:100]}",
                "stdout": exec_result.stdout[-500:] if len(exec_result.stdout) > 500 else exec_result.stdout,
                "stderr": exec_result.stderr[-500:] if len(exec_result.stderr) > 500 else exec_result.stderr,
                "return_code": exec_result.returncode
            }
        
        # Run test.py in the isolated temp directory
        result = subprocess.run(
            ['python', 'test.py'],
            cwd=str(temp_path),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        test_passed = result.returncode == 0
        
        return {
            "test_ran": True,
            "test_passed": test_passed,
            "error": "" if test_passed else "Test failed",
            "stdout": result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout,
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "test_ran": True,
            "test_passed": False,
            "error": f"Timeout after {timeout}s",
            "stdout": "",
            "stderr": "",
            "return_code": -1
        }
    except Exception as e:
        return {
            "test_ran": True,
            "test_passed": False,
            "error": str(e),
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }
    finally:
        # Clean up temporary directory
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def compute_sample_statistics(sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics (mean, std dev, pass rate) across samples for all evaluators.
    """
    stats = {}
    
    # Get all evaluator names from first sample
    if not sample_results:
        return stats
    
    first_evals = sample_results[0].get("quality", {}).get("evaluations", {})
    
    for eval_name in first_evals.keys():
        scores = []
        passes = []
        
        for sample in sample_results:
            eval_data = sample.get("quality", {}).get("evaluations", {}).get(eval_name, {})
            scores.append(eval_data.get("score", 0.0))
            passes.append(1 if eval_data.get("passed", False) else 0)
        
        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        pass_rate = sum(passes) / len(passes) if passes else 0.0
        
        stats[eval_name] = {
            "mean_score": round(mean_score, 3),
            "std_dev": round(std_dev, 3),
            "pass_rate": round(pass_rate, 2),
            "pass_count": f"{sum(passes)}/{len(passes)}"
        }
    
    # Functional test stats
    func_passes = []
    for sample in sample_results:
        func_passed = sample.get("functional", {}).get("test_passed", False)
        func_passes.append(1 if func_passed else 0)
    
    func_pass_rate = sum(func_passes) / len(func_passes) if func_passes else 0.0
    stats["Functional"] = {
        "pass_rate": round(func_pass_rate, 2),
        "pass_count": f"{sum(func_passes)}/{len(func_passes)}"
    }
    
    return stats


def evaluate_all_tasks():
    """
    Main evaluation function that evaluates all generated code.
    """
    print("=" * 70)
    print("🔍 COMPREHENSIVE CODE EVALUATION")
    print("=" * 70)
    print("\nThis script evaluates generated code for:")
    print("  • Quality: Syntax, Style, Security, Execution, Performance, Maintainability")
    print("  • Functionality: Task-specific tests")
    print(f"  • Samples per task: {NUM_SAMPLES}")
    print(f"\nResults will be saved in: {RESULTS_DIR}\n")
    
    gen_path = Path(OUTPUT_DIR)
    results_path = Path(RESULTS_DIR)
    
    if not gen_path.exists():
        print(f"❌ ERROR: Generated code directory not found: {gen_path}")
        sys.exit(1)
    
    # Create results directory structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = results_path / f"evaluation_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Created results directory: {run_dir}\n")
    
    # Storage for all results
    all_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_models": 0,
        "total_tasks": 0,
        "num_samples": NUM_SAMPLES,
        "models": {}
    }
    
    # Find all model folders
    model_folders = [f for f in gen_path.iterdir() if f.is_dir()]
    all_results["total_models"] = len(model_folders)
    
    print(f"📊 Found {len(model_folders)} model(s) to evaluate\n")
    
    # Process each model
    for model_idx, model_folder in enumerate(model_folders, 1):
        model_name = model_folder.name
        print(f"{'='*70}")
        print(f"🤖 Model {model_idx}/{len(model_folders)}: {model_name}")
        print(f"{'='*70}\n")
        
        # Create model-specific results folder
        model_results_dir = run_dir / model_name
        model_results_dir.mkdir(exist_ok=True)
        
        model_results = {
            "model_name": model_name,
            "tasks": {},
            "summary": {
                "total_tasks": 0,
                "avg_pass_rate": 0.0,
                "avg_quality_score": 0.0
            }
        }
        
        # Find all task folders for this model
        task_folders = sorted([f for f in model_folder.iterdir() if f.is_dir()])
        model_results["summary"]["total_tasks"] = len(task_folders)
        
        # Process each task
        for task_idx, task_folder in enumerate(task_folders, 1):
            task_id = task_folder.name
            print(f"  [{task_idx}/{len(task_folders)}] Evaluating {task_id}...")
            
            # Use absolute path for task folder
            task_folder_abs = task_folder.resolve()
            
            # Find all sample scripts
            sample_scripts = find_generated_scripts(task_folder_abs)
            
            if not sample_scripts:
                print(f"      ❌ No generated scripts found")
                continue
            
            task_result = {
                "task_id": task_id,
                "task_folder": str(task_folder_abs),
                "num_samples": len(sample_scripts),
                "samples": [],
                "statistics": {}
            }
            
            sample_results = []
            
            # Evaluate each sample
            for sample_idx, script_path in enumerate(sample_scripts, 1):
                print(f"      🔄 Sample {sample_idx}/{len(sample_scripts)}: {script_path.name}")
                
                sample_result = {
                    "sample_idx": sample_idx,
                    "script_name": script_path.name,
                    "quality": {},
                    "functional": {}
                }
                
                # Run quality evaluations
                quality_result = run_quality_evaluation_for_sample(script_path, model_name, task_id)
                
                if quality_result["error"]:
                    print(f"         ⚠️  Quality: {quality_result['error']}")
                    sample_result["quality"] = {"error": quality_result["error"]}
                else:
                    sample_result["quality"] = quality_result["evaluations"]
                    quality_passed = all(r["passed"] for r in quality_result["evaluations"].values())
                    print(f"         {'✅' if quality_passed else '⚠️'} Quality checks")
                
                # Run functional test
                func_result = run_functional_test_for_sample(task_folder_abs, script_path)
                
                sample_result["functional"] = {
                    "test_ran": func_result["test_ran"],
                    "test_passed": func_result["test_passed"],
                    "error": func_result["error"] if func_result["error"] else None,
                    "stderr": func_result["stderr"] if func_result["stderr"] else None
                }
                
                if func_result["test_passed"]:
                    print(f"         ✅ Functional: PASS")
                elif not func_result["test_ran"]:
                    print(f"         ⚠️  Functional: SKIP")
                else:
                    print(f"         ❌ Functional: FAIL")
                
                sample_results.append(sample_result)
                task_result["samples"].append(sample_result)
            
            # Compute statistics across samples
            task_result["statistics"] = compute_sample_statistics(sample_results)
            
            # Save individual task result
            task_result_file = model_results_dir / f"{task_id}_result.json"
            with open(task_result_file, 'w', encoding='utf-8') as f:
                json.dump(task_result, f, indent=2)
            
            model_results["tasks"][task_id] = task_result
            print()
        
        # Compute model-level averages
        all_pass_rates = []
        all_quality_scores = []
        
        for task_data in model_results["tasks"].values():
            stats = task_data.get("statistics", {})
            if "Functional" in stats:
                all_pass_rates.append(stats["Functional"]["pass_rate"])
            
            # Average quality scores across evaluators for this task
            quality_scores = []
            for eval_name, eval_stats in stats.items():
                if eval_name != "Functional" and "mean_score" in eval_stats:
                    quality_scores.append(eval_stats["mean_score"])
            
            if quality_scores:
                all_quality_scores.append(statistics.mean(quality_scores))
        
        if all_pass_rates:
            model_results["summary"]["avg_pass_rate"] = round(statistics.mean(all_pass_rates), 2)
        if all_quality_scores:
            model_results["summary"]["avg_quality_score"] = round(statistics.mean(all_quality_scores), 3)
        
        # Save model summary
        all_results["models"][model_name] = model_results
        
        # Save model results JSON
        model_summary_file = model_results_dir / "model_summary.json"
        with open(model_summary_file, 'w', encoding='utf-8') as f:
            json.dump(model_results, f, indent=2)
        
        print(f"  💾 Saved model results to: {model_results_dir}\n")
    
    # Save overall results
    all_results["total_tasks"] = sum(m["summary"]["total_tasks"] for m in all_results["models"].values())
    
    overall_results_file = run_dir / "overall_results.json"
    with open(overall_results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("=" * 70)
    print("📊 EVALUATION SUMMARY")
    print("=" * 70)
    
    for model_name, model_data in all_results["models"].items():
        summary = model_data["summary"]
        print(f"\n🤖 {model_name}:")
        print(f"   Total tasks:         {summary['total_tasks']}")
        print(f"   Avg quality score:   {summary['avg_quality_score']}")
        print(f"   Avg pass rate:       {summary['avg_pass_rate']:.0%}")
        
        # Per-task statistics
        print(f"\n   Per-task statistics (mean ± std dev, pass rate):")
        for task_id, task_data in model_data["tasks"].items():
            stats = task_data.get("statistics", {})
            print(f"      {task_id}:")
            
            for eval_name, eval_stats in stats.items():
                if eval_name == "Functional":
                    print(f"         {eval_name:12s}: {eval_stats['pass_count']} passed")
                else:
                    mean = eval_stats.get("mean_score", 0)
                    std = eval_stats.get("std_dev", 0)
                    passes = eval_stats.get("pass_count", "0/0")
                    print(f"         {eval_name:12s}: {mean:.3f} ± {std:.3f} | {passes} passed")
    
    print(f"\n💾 All results saved to: {run_dir}")
    print("=" * 70)
    print("🎉 Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_all_tasks()
