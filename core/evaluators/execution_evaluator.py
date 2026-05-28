"""
Execution Evaluator Module

Simple evaluator that checks if Python code can be executed without errors.
This provides a clear pass/fail indication for code executability,
separate from performance metrics or other quality checks.
"""

import subprocess
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult


class ExecutionEvaluator(BaseEvaluator):
    """Evaluator that checks if Python code can be executed successfully."""
    
    def __init__(self, timeout: int = 30):
        super().__init__("ExecutionEvaluator")
        self.timeout = timeout
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """Attempt to execute the code and report success/failure."""
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
        else:
            working_dir = None
            script_path = None
            use_temp = True
            
            try:
                # Determine working directory and script path
                file_path_obj = Path(file_path)
                
                # Check if this is a task folder with generated_script_v*.py
                if file_path_obj.name.startswith("generated_script") and file_path_obj.name.endswith(".py") and file_path_obj.parent.exists():
                    # Use the task folder as working directory
                    working_dir = str(file_path_obj.parent)
                    # Use relative filename when setting cwd to avoid path doubling
                    script_path = file_path_obj.name
                    use_temp = False
                else:
                    # Write code to temporary file
                    with tempfile.NamedTemporaryFile(
                        mode='w', 
                        suffix='.py', 
                        delete=False,
                        encoding='utf-8'
                    ) as tmp_file:
                        tmp_file.write(code_content)
                        script_path = tmp_file.name
                    working_dir = None
                    use_temp = True
                
                # Execute the code with timeout
                start_time = datetime.now()
                
                # Prepare subprocess arguments
                subprocess_args = {
                    'capture_output': True,
                    'text': True,
                    'timeout': self.timeout
                }
                
                # Set working directory if we have one
                if working_dir:
                    subprocess_args['cwd'] = working_dir
                
                result = subprocess.run(
                    ['python', script_path],
                    **subprocess_args
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Store execution details
                details["execution_time_seconds"] = round(execution_time, 3)
                details["return_code"] = result.returncode
                details["stdout"] = result.stdout[:1000] if result.stdout else ""
                details["stderr"] = result.stderr[:1000] if result.stderr else ""
                
                if result.returncode == 0:
                    passed = True
                    score = 1.0
                    details["execution_success"] = True
                else:
                    details["execution_success"] = False
                    details["error_type"] = "runtime_error"
                    if result.stderr:
                        error_lines = result.stderr.strip().split('\n')
                        error_message = error_lines[-1] if error_lines else "Runtime error occurred"
                    else:
                        error_message = f"Process exited with code {result.returncode}"
                
            except subprocess.TimeoutExpired:
                details["execution_success"] = False
                details["timeout_occurred"] = True
                details["error_type"] = "timeout"
                error_message = f"Execution timed out after {self.timeout} seconds"
            except Exception as e:
                details["execution_success"] = False
                details["error_type"] = "execution_exception"
                error_message = f"Execution failed: {str(e)}"
            finally:
                # Clean up temporary file only if we used one
                if use_temp and script_path:
                    try:
                        os.unlink(script_path)
                    except:
                        pass
        
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
