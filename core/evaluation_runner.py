"""
Evaluation Runner Module

Runs all registered evaluators on generated code files.
Organizes results by evaluation run with separate folders for each evaluator.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import shutil

from config import OUTPUT_DIR, RESULTS_DIR
from core.evaluators import BaseEvaluator, EvaluationResult
from typing import Optional


class EvaluationRunner:
    """
    Runner that executes all evaluators on generated code files.
    
    Creates a folder structure per evaluation run:
    results/
    └── run_20260502_143530/
        ├── evaluation_report.json       # Combined results from all evaluators
        ├── summary.csv                  # CSV summary for easy viewing
        ├── syntax/                      # Syntax evaluator results
        │   ├── results.json
        │   └── details/
        ├── security/                    # Security evaluator results
        │   ├── results.json
        │   └── details/
        └── ...                          # Other evaluators
    
    Usage:
        runner = EvaluationRunner()
        runner.register_evaluator(SyntaxEvaluator())
        runner.register_evaluator(SecurityEvaluator())
        results = runner.run_evaluation()
    """
    
    def __init__(self, generated_code_dir: str = OUTPUT_DIR, results_dir: str = RESULTS_DIR):
        self.generated_code_dir = Path(generated_code_dir)
        self.results_dir = Path(results_dir)
        self.evaluators: List[BaseEvaluator] = []
        self.results: List[EvaluationResult] = []
        self.current_run_dir: Optional[Path] = None
        self.run_timestamp: Optional[str] = None
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def register_evaluator(self, evaluator: BaseEvaluator):
        """Register an evaluator to be run."""
        self.evaluators.append(evaluator)
        print(f"   ✓ Registered evaluator: {evaluator.get_name()}")
    
    def _create_run_directory(self):
        """Create a new directory for this evaluation run."""
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = self.results_dir / f"run_{self.run_timestamp}"
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each evaluator
        for evaluator in self.evaluators:
            evaluator_dir = self.current_run_dir / evaluator.get_name().lower()
            evaluator_dir.mkdir(parents=True, exist_ok=True)
            # Create details subdirectory
            (evaluator_dir / "details").mkdir(parents=True, exist_ok=True)
        
        print(f"   ✓ Created evaluation run directory: {self.current_run_dir.name}")
        return self.current_run_dir
    
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
        
        # Create directory structure for this run
        self._create_run_directory()
        
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
        """
        Save evaluation results organized by evaluator in separate folders.
        """
        if not self.results:
            print("\n⚠️ No results to save")
            return
        
        if not self.current_run_dir:
            print("\n⚠️ No run directory created")
            return
        
        print(f"\n💾 Saving results to: {self.current_run_dir.name}")
        
        # Group results by evaluator
        results_by_evaluator: Dict[str, List[EvaluationResult]] = {}
        for result in self.results:
            evaluator_name = result.evaluator_name
            if evaluator_name not in results_by_evaluator:
                results_by_evaluator[evaluator_name] = []
            results_by_evaluator[evaluator_name].append(result)
        
        # Save individual evaluator results
        for evaluator_name, evaluator_results in results_by_evaluator.items():
            self._save_evaluator_results(evaluator_name, evaluator_results)
        
        # Save combined report
        self._save_combined_report(results_by_evaluator)
        
        # Save CSV summary
        self._save_csv_summary(results_by_evaluator)
        
        print(f"   ✓ All results saved successfully")
    
    def _save_evaluator_results(self, evaluator_name: str, results: List[EvaluationResult]):
        """Save results for a specific evaluator."""
        if self.current_run_dir is None:
            return
        evaluator_dir = self.current_run_dir / evaluator_name.lower()
        
        # Prepare evaluator-specific data
        evaluator_data = {
            "evaluator_name": evaluator_name,
            "run_timestamp": self.run_timestamp,
            "total_files": len(set(r.file_path for r in results)),
            "total_evaluations": len(results),
            "summary": {
                "total_passed": sum(1 for r in results if r.passed),
                "total_failed": sum(1 for r in results if not r.passed),
                "pass_rate": sum(1 for r in results if r.passed) / len(results) if results else 0,
                "average_score": sum(r.score for r in results) / len(results) if results else 0
            },
            "results": [
                {
                    "file_path": r.file_path,
                    "prompt_id": r.prompt_id,
                    "model_name": r.model_name,
                    "passed": r.passed,
                    "score": r.score,
                    "details": r.details,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in results
            ]
        }
        
        # Save to JSON
        results_file = evaluator_dir / "results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(evaluator_data, f, indent=2)
        
        print(f"   ✓ {evaluator_name}: {len(results)} result(s) saved")
    
    def _save_combined_report(self, results_by_evaluator: Dict[str, List[EvaluationResult]]):
        """Save a combined report with all evaluator results."""
        if self.current_run_dir is None:
            return
        # Calculate overall statistics
        all_results = []
        for results in results_by_evaluator.values():
            all_results.extend(results)
        
        combined_data = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "run_timestamp": self.run_timestamp,
            "run_directory": str(self.current_run_dir.name),
            "total_files_evaluated": len(set(r.file_path for r in all_results)),
            "total_evaluations": len(all_results),
            "evaluators_used": list(results_by_evaluator.keys()),
            "overall_summary": {
                "total_passed": sum(1 for r in all_results if r.passed),
                "total_failed": sum(1 for r in all_results if not r.passed),
                "pass_rate": sum(1 for r in all_results if r.passed) / len(all_results) if all_results else 0
            },
            "evaluator_summaries": {
                evaluator_name: {
                    "total_evaluations": len(results),
                    "passed": sum(1 for r in results if r.passed),
                    "failed": sum(1 for r in results if not r.passed),
                    "pass_rate": sum(1 for r in results if r.passed) / len(results) if results else 0,
                    "average_score": sum(r.score for r in results) / len(results) if results else 0
                }
                for evaluator_name, results in results_by_evaluator.items()
            },
            "all_results": [
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
                for r in all_results
            ]
        }
        
        # Save combined report
        report_file = self.current_run_dir / "evaluation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2)
        
        print(f"   ✓ Combined report saved")
    
    def _save_csv_summary(self, results_by_evaluator: Dict[str, List[EvaluationResult]]):
        """Save CSV summaries for easy spreadsheet viewing."""
        if self.current_run_dir is None:
            return
        import csv
        
        # Save detailed CSV with all results
        csv_file = self.current_run_dir / "summary.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'File', 'Model', 'Prompt', 'Evaluator', 'Passed', 
                'Score', 'Error Message', 'Timestamp'
            ])
            
            for evaluator_name, results in results_by_evaluator.items():
                for result in results:
                    writer.writerow([
                        Path(result.file_path).name,
                        result.model_name,
                        result.prompt_id,
                        result.evaluator_name,
                        'YES' if result.passed else 'NO',
                        f"{result.score:.2f}",
                        result.error_message if result.error_message else '',
                        result.timestamp
                    ])
        
        print(f"   ✓ CSV summary saved")
        
        # Save per-evaluator CSV files
        for evaluator_name, results in results_by_evaluator.items():
            evaluator_csv = self.current_run_dir / f"{evaluator_name.lower()}_summary.csv"
            with open(evaluator_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'File', 'Model', 'Prompt', 'Passed', 
                    'Score', 'Details', 'Error Message'
                ])
                
                for result in results:
                    writer.writerow([
                        Path(result.file_path).name,
                        result.model_name,
                        result.prompt_id,
                        'YES' if result.passed else 'NO',
                        f"{result.score:.2f}",
                        json.dumps(result.details),
                        result.error_message if result.error_message else ''
                    ])
    
    def print_summary(self):
        """Print a summary of evaluation results."""
        if not self.results:
            print("\n⚠️ No results to display")
            return
        
        print("\n" + "=" * 70)
        print("📊 EVALUATION SUMMARY")
        print("=" * 70)
        print(f"Run Directory: {self.current_run_dir.name if self.current_run_dir else 'N/A'}")
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
            avg_score = sum(r.score for r in self.results if r.evaluator_name == evaluator) / stats['total']
            print(f"  • {evaluator}:")
            print(f"    - Passed: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
            print(f"    - Avg Score: {avg_score:.2f}")
        
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
