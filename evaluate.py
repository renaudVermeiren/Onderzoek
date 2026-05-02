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


def main():
    """Main entry point for the evaluation script."""
    print("=" * 70)
    print("🔍 CODE EVALUATION RUNNER")
    print("=" * 70)
    print("\nThis script evaluates generated code for syntax correctness.")
    print("Results will be saved in the 'results' folder.\n")
    
    # Create evaluation runner
    runner = EvaluationRunner()
    
    # Register evaluators
    print("📋 Registering evaluators...")
    runner.register_evaluator(SyntaxEvaluator())
    # Add more evaluators here in the future, for example:
    # runner.register_evaluator(StyleEvaluator())
    # runner.register_evaluator(SecurityEvaluator())
    
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
