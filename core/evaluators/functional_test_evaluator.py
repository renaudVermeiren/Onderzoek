"""
Functional Test Evaluator Module

This evaluator runs the functional test.py files for each generated task
to verify if the code correctly implements the required functionality.
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from core.evaluators import BaseEvaluator, EvaluationResult


class FunctionalTestEvaluator(BaseEvaluator):
    """
    Evaluator that runs functional tests (test.py) for each generated task.
    """
    
    def __init__(self, timeout: int = 30):
        super().__init__("FunctionalTestEvaluator")
        self.timeout = timeout
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """This method is not used directly."""
        return EvaluationResult(
            file_path=file_path,
            prompt_id=metadata.get("prompt_id", "unknown"),
            model_name=metadata.get("model_name", "unknown"),
            evaluator_name=self.name,
            passed=True,
            score=1.0,
            details={},
            timestamp=datetime.now().isoformat(),
            error_message=""
        )
    
    def run_task_test(self, task_folder: Path) -> Dict[str, Any]:
        """Run the test.py script in a task folder."""
        test_file = task_folder / "test.py"
        
        if not test_file.exists():
            return {
                "test_ran": False,
                "test_passed": False,
                "error": "test.py not found",
                "stdout": "",
                "stderr": ""
            }
        
        try:
            result = subprocess.run(
                ['python', 'test.py'],
                cwd=str(task_folder),
                capture_output=True,
                text=True,
                timeout=self.timeout
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
                "error": f"Timeout after {self.timeout}s",
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
