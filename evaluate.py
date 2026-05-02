#!/usr/bin/env python3
"""
Code Evaluation Script

This script evaluates all generated code files for syntax correctness.
It can be extended with additional evaluators in the future.

Usage:
    python evaluate.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.evaluation_runner import EvaluationRunner
from core.evaluators.syntax_evaluator import SyntaxEvaluator
from core.evaluators.security_evaluator import SecurityEvaluator
from core.evaluators.execution_evaluator import ExecutionEvaluator
from core.evaluators.performance_evaluator import PerformanceEvaluator
from core.evaluators.radon_evaluator import RadonEvaluator


def main():
    """Main entry point for the evaluation script."""
    print("=" * 70)
    print("🔍 CODE EVALUATION RUNNER")
    print("=" * 70)
    print("\nThis script evaluates generated code for syntax, security, executability, performance, and maintainability.")
    print("Results will be saved in the 'results' folder.\n")
    
    # Create evaluation runner
    runner = EvaluationRunner()
    
    # Register evaluators
    # Note: ExecutionEvaluator should run before PerformanceEvaluator
    # to clearly separate "code doesn't run" from "code runs but slow"
    print("📋 Registering evaluators...")
    runner.register_evaluator(SyntaxEvaluator())
    runner.register_evaluator(SecurityEvaluator())
    runner.register_evaluator(ExecutionEvaluator())
    runner.register_evaluator(PerformanceEvaluator())
    runner.register_evaluator(RadonEvaluator())
    # Add more evaluators here in the future, for example:
    # runner.register_evaluator(StyleEvaluator())
    
    # Run evaluation
    results = runner.run_evaluation()
    
    if not results:
        print("\n❌ No evaluation results generated.")
        sys.exit(1)
    
    # Save results
    runner.save_results()
    
    # Print summary
    runner.print_summary()
    
    print("\n🎉 Evaluation complete!")


if __name__ == "__main__":
    main()
