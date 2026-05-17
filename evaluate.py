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
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR, RESULTS_DIR
from core.evaluators.syntax_evaluator import SyntaxEvaluator
from core.evaluators.security_evaluator import SecurityEvaluator
from core.evaluators.execution_evaluator import ExecutionEvaluator
from core.evaluators.performance_evaluator import PerformanceEvaluator
from core.evaluators.radon_evaluator import RadonEvaluator
from core.evaluators.functional_test_evaluator import FunctionalTestEvaluator
from core.evaluators.style_evaluator import StyleEvaluator


def load_generated_script(task_folder: Path) -> str:
    """Load the generated Python script from a task folder."""
    script_file = task_folder / "generated_script.py"
    if script_file.exists():
        with open(script_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def run_quality_evaluation(task_folder: Path, model_name: str, task_id: str) -> Dict[str, Any]:
    """
    Run all quality evaluators on a generated script.
    
    Returns:
        Dictionary with results from all quality evaluators
    """
    code_content = load_generated_script(task_folder)
    
    if not code_content:
        return {
            "error": "No generated script found",
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
            # Use absolute path to avoid path doubling issues
            script_path = (task_folder / "generated_script.py").resolve()
            result = evaluator.evaluate(
                file_path=str(script_path),
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
    
    # Initialize functional test evaluator
    func_evaluator = FunctionalTestEvaluator()
    
    # Storage for all results
    all_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_models": 0,
        "total_tasks": 0,
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
                "quality_passed": 0,
                "functional_passed": 0
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
            
            task_result = {
                "task_id": task_id,
                "task_folder": str(task_folder_abs),
                "quality": {},
                "functional": {},
                "overall_passed": False
            }
            
            # Run quality evaluations
            print(f"      Running quality checks...", end=" ")
            quality_result = run_quality_evaluation(task_folder_abs, model_name, task_id)
            
            if quality_result["error"]:
                print(f"❌ ERROR: {quality_result['error']}")
                task_result["quality"] = {"error": quality_result["error"]}
            else:
                task_result["quality"] = quality_result["evaluations"]
                quality_passed = all(r["passed"] for r in quality_result["evaluations"].values())
                print(f"{'✅ All passed' if quality_passed else '⚠️  Some failed'}")
                if quality_passed:
                    model_results["summary"]["quality_passed"] += 1
            
            # Run functional test
            print(f"      Running functional test...", end=" ")
            func_result = func_evaluator.run_task_test(task_folder_abs)
            
            task_result["functional"] = {
                "test_ran": func_result["test_ran"],
                "test_passed": func_result["test_passed"],
                "error": func_result["error"] if func_result["error"] else None,
                "stderr": func_result["stderr"] if func_result["stderr"] else None
            }
            
            if func_result["test_passed"]:
                print("✅ PASS")
                model_results["summary"]["functional_passed"] += 1
                task_result["overall_passed"] = True
            elif not func_result["test_ran"]:
                print("⚠️  SKIP")
            else:
                print(f"❌ FAIL - {func_result['error'][:40]}...")
            
            # Save individual task result
            task_result_file = model_results_dir / f"{task_id}_result.json"
            with open(task_result_file, 'w', encoding='utf-8') as f:
                json.dump(task_result, f, indent=2)
            
            model_results["tasks"][task_id] = task_result
            print()
        
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
        print(f"   Total tasks:     {summary['total_tasks']}")
        print(f"   Quality passed:  {summary['quality_passed']}/{summary['total_tasks']}")
        print(f"   Functional pass: {summary['functional_passed']}/{summary['total_tasks']}")
    
    print(f"\n💾 All results saved to: {run_dir}")
    print("=" * 70)
    print("🎉 Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_all_tasks()
