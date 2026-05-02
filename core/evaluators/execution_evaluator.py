"""
Execution Evaluator Module

Simple evaluator that checks if Python code can be executed without errors.
This provides a clear pass/fail indication for code executability,
separate from performance metrics or other quality checks.

Usage:
    This evaluator should typically run BEFORE the PerformanceEvaluator,
    so you know if code execution failed due to runtime errors or performance issues.
"""

import subprocess
import tempfile
import os
from typing import Dict, Any
from datetime import datetime

from core.evaluators import BaseEvaluator, EvaluationResult


class ExecutionEvaluator(BaseEvaluator):
    """
    Evaluator that checks if Python code can be executed successfully.
    
    This is a simple pass/fail evaluator that attempts to run the code
    and reports whether it executed without errors. It does NOT measure
    performance metrics - use PerformanceEvaluator for that.
    
    Benefits:
    - Clear separation between "code doesn't run" and "code runs but slow"
    - Can be used as a prerequisite check before performance testing
    - Provides detailed error output when execution fails
    - Uses timeout to prevent hanging on infinite loops
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the execution evaluator.
        
        Args:
            timeout: Maximum execution time in seconds (default: 30)
        """
        super().__init__("ExecutionEvaluator")
        self.timeout = timeout
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Attempt to execute the code and report success/failure.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult with execution status
        """
        passed = False
        score = 0.0
        details = {
            "execution_success": False,
            "execution_time_seconds": 0.0,
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "timeout_occurred": False,
            "error_type": None
        }
        error_message = ""
        
        # Check if content is empty or too short
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short to execute"
            details["error_type"] = "empty_code"
            score = 0.0
            passed = False
        else:
            try:
                # Write code to temporary file
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.py', 
                    delete=False,
                    encoding='utf-8'
                ) as tmp_file:
                    tmp_file.write(code_content)
                    tmp_path = tmp_file.name
                
                try:
                    # Execute the code with timeout
                    start_time = datetime.now()
                    
                    result = subprocess.run(
                        ['python', tmp_path],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    # Store execution details
                    details["execution_time_seconds"] = round(execution_time, 3)
                    details["return_code"] = result.returncode
                    details["stdout"] = result.stdout[:1000] if result.stdout else ""  # Limit output size
                    details["stderr"] = result.stderr[:1000] if result.stderr else ""  # Limit output size
                    
                    if result.returncode == 0:
                        # Success!
                        passed = True
                        score = 1.0
                        details["execution_success"] = True
                        error_message = ""
                    else:
                        # Execution failed with error
                        passed = False
                        score = 0.0
                        details["execution_success"] = False
                        details["error_type"] = "runtime_error"
                        
                        # Extract error message from stderr
                        if result.stderr:
                            # Get first line of error
                            error_lines = result.stderr.strip().split('\n')
                            error_message = error_lines[-1] if error_lines else "Runtime error occurred"
                        else:
                            error_message = f"Process exited with code {result.returncode}"
                        
                except subprocess.TimeoutExpired:
                    # Execution timed out
                    passed = False
                    score = 0.0
                    details["execution_success"] = False
                    details["timeout_occurred"] = True
                    details["error_type"] = "timeout"
                    error_message = f"Execution timed out after {self.timeout} seconds"
                    
                except Exception as e:
                    # Other execution error
                    passed = False
                    score = 0.0
                    details["execution_success"] = False
                    details["error_type"] = "execution_exception"
                    error_message = f"Execution failed: {str(e)}"
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
            except Exception as e:
                # File creation or other error
                error_message = f"Failed to prepare code for execution: {str(e)}"
                score = 0.0
                passed = False
                details["error_type"] = "preparation_error"
        
        return EvaluationResult(
            file_path=file_path,
            prompt_id=metadata.get("prompt_id", "unknown"),
            model_name=metadata.get("model_name", "unknown"),
            evaluator_name=self.name,
            passed=passed,
            score=score,
            details=details,
            timestamp=datetime.now().isoformat(),
            error_message=error_message
        )
