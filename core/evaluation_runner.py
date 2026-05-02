"""
Evaluation Runner Module

Runs all registered evaluators on generated code files.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config import OUTPUT_DIR, RESULTS_DIR
from core.evaluators import BaseEvaluator, EvaluationResult
from core.evaluators.syntax_evaluator import SyntaxEvaluator


class EvaluationRunner:
    """
    Runner that executes all evaluators on generated code files.
    
    Usage:
        runner = EvaluationRunner()
        runner.register_evaluator(SyntaxEvaluator())
        results = runner.run_evaluation()
    """
    
    def __init__(self, generated_code_dir: str = OUTPUT_DIR, results_dir: str = RESULTS_DIR):
        self.generated_code_dir = Path(generated_code_dir)
        self.results_dir = Path(results_dir)
        self.evaluators: List[BaseEvaluator] = []
        self.results: List[EvaluationResult] = []
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def register_evaluator(self, evaluator: BaseEvaluator):
        """Register an evaluator to be run."""
        self.evaluators.append(evaluator)
        print(f"   ✓ Registered evaluator: {evaluator.get_name()}")
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load the most recent metadata file from generated_code directory."""
        metadata_files = list(self.generated_code_dir.glob("metadata_*.json"))
        
        if not metadata_files:
            print("   ⚠️ No metadata files found")
            return {}
        
        # Get the most recent metadata file
        latest_metadata = max(metadata_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_metadata, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"   ⚠️ Error loading metadata: {e}")
            return {}
    
    def find_generated_files(self) -> List[Path]:
        """Find all Python files in the generated_code directory."""
        python_files = []
        
        if not self.generated_code_dir.exists():
            print(f"   ⚠️ Generated code directory not found: {self.generated_code_dir}")
            return python_files
        
        # Look for .py files in model subdirectories
        for model_dir in self.generated_code_dir.iterdir():
            if model_dir.is_dir():
                for py_file in model_dir.glob("*.py"):
                    python_files.append(py_file)
        
        return python_files
    
    def extract_metadata_from_path(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path and name."""
        # File is in format: generated_code/<model_name>/<prompt_id>_<timestamp>.py
        model_name = file_path.parent.name
        filename = file_path.stem  # prompt_id_timestamp
        
        # Extract prompt_id (everything before the last underscore)
        parts = filename.rsplit('_', 1)
        prompt_id = parts[0] if len(parts) > 1 else filename
        
        return {
            "model_name": model_name,
            "prompt_id": prompt_id,
            "file_name": file_path.name
        }
    
    def run_evaluation(self) -> List[EvaluationResult]:
        """
        Run all registered evaluators on all generated files.
        
        Returns:
            List of EvaluationResult objects
        """
        if not self.evaluators:
            print("   ⚠️ No evaluators registered")
            return []
        
        print("🔍 Finding generated code files...")
        generated_files = self.find_generated_files()
        
        if not generated_files:
            print("   ⚠️ No Python files found in generated_code directory")
            return []
        
        print(f"   ✓ Found {len(generated_files)} file(s) to evaluate")
        
        print("\n🧪 Running evaluators...")
        self.results = []
        total_evaluations = len(generated_files) * len(self.evaluators)
        current = 0
        
        for file_path in generated_files:
            print(f"\n   📄 {file_path.name}")
            
            # Read the file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except Exception as e:
                print(f"      ❌ Error reading file: {e}")
                continue
            
            # Extract metadata
            metadata = self.extract_metadata_from_path(file_path)
            
            # Run each evaluator
            for evaluator in self.evaluators:
                current += 1
                print(f"      [{current}/{total_evaluations}] {evaluator.get_name()}...", end=" ")
                
                try:
                    result = evaluator.evaluate(
                        file_path=str(file_path),
                        code_content=code_content,
                        metadata=metadata
                    )
                    self.results.append(result)
                    
                    status = "✅ PASS" if result.passed else "❌ FAIL"
                    print(f"{status}")
                    
                    if result.error_message and result.error_message.strip():
                        print(f"         Error: {result.error_message}")
                        
                except Exception as e:
                    print(f"💥 ERROR: {e}")
        
        return self.results
    
    def save_results(self):
        """Save evaluation results to JSON file."""
        if not self.results:
            print("\n⚠️ No results to save")
            return
        
        print("\n💾 Saving results...")
        
        # Prepare results data
        results_data = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_files_evaluated": len(set(r.file_path for r in self.results)),
            "total_evaluations": len(self.results),
            "evaluators_used": [e.get_name() for e in self.evaluators],
            "summary": {
                "total_passed": sum(1 for r in self.results if r.passed),
                "total_failed": sum(1 for r in self.results if not r.passed),
                "pass_rate": sum(1 for r in self.results if r.passed) / len(self.results) if self.results else 0
            },
            "results": [
                {
                    "file_path": r.file_path,
                    "prompt_id": r.prompt_id,
                    "model_name": r.model_name,
                    "evaluator": r.evaluator_name,
                    "passed": r.passed,
                    "score": r.score,
                    "details": r.details,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"evaluation_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"   ✓ Results saved to: {results_file}")
        
        # Also save a summary CSV for easy viewing
        self._save_csv_summary(results_data, timestamp)
    
    def _save_csv_summary(self, results_data: Dict[str, Any], timestamp: str):
        """Save a CSV summary for easy spreadsheet viewing."""
        import csv
        
        csv_file = self.results_dir / f"evaluation_summary_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'File', 'Model', 'Prompt', 'Evaluator', 'Passed', 
                'Score', 'Error Message', 'Timestamp'
            ])
            
            for result in results_data['results']:
                writer.writerow([
                    Path(result['file_path']).name,
                    result['model_name'],
                    result['prompt_id'],
                    result['evaluator'],
                    'YES' if result['passed'] else 'NO',
                    f"{result['score']:.2f}",
                    result.get('error_message', '') if result.get('error_message') else '',
                    result['timestamp']
                ])
        
        print(f"   ✓ CSV summary saved to: {csv_file}")
    
    def print_summary(self):
        """Print a summary of evaluation results."""
        if not self.results:
            print("\n⚠️ No results to display")
            return
        
        print("\n" + "=" * 70)
        print("📊 EVALUATION SUMMARY")
        print("=" * 70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Evaluations: {total}")
        print(f"Passed:            {passed} ✅")
        print(f"Failed:            {failed} ❌")
        print(f"Pass Rate:         {pass_rate:.1f}%")
        
        # Group by evaluator
        print("\nResults by Evaluator:")
        evaluator_results = {}
        for result in self.results:
            evaluator = result.evaluator_name
            if evaluator not in evaluator_results:
                evaluator_results[evaluator] = {'total': 0, 'passed': 0}
            evaluator_results[evaluator]['total'] += 1
            if result.passed:
                evaluator_results[evaluator]['passed'] += 1
        
        for evaluator, stats in evaluator_results.items():
            rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  • {evaluator}: {stats['passed']}/{stats['total']} passed ({rate:.1f}%)")
        
        # Group by model
        print("\nResults by Model:")
        model_results = {}
        for result in self.results:
            model = result.model_name
            if model not in model_results:
                model_results[model] = {'total': 0, 'passed': 0}
            model_results[model]['total'] += 1
            if result.passed:
                model_results[model]['passed'] += 1
        
        for model, stats in model_results.items():
            rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  • {model}: {stats['passed']}/{stats['total']} passed ({rate:.1f}%)")
        
        print("\n" + "=" * 70)
