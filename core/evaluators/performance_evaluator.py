"""
Performance Evaluator Module

Evaluates Python code performance by executing it and measuring
CPU and memory usage using psutil.
"""

import subprocess
import tempfile
import os
import time
import threading
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult


class PerformanceEvaluator(BaseEvaluator):
    """Evaluator that measures code performance (CPU and memory usage)."""
    
    def __init__(self, num_iterations: int = 3, timeout: int = 30):
        super().__init__("PerformanceEvaluator")
        self.num_iterations = num_iterations
        self.timeout = timeout
        self._check_psutil_installed()
    
    def _check_psutil_installed(self):
        """Check if psutil is installed."""
        try:
            import psutil
        except ImportError:
            raise RuntimeError("psutil is not installed. Install it with: pip install psutil")
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """Execute the code and measure CPU and memory performance."""
        import psutil
        
        passed = False
        score = 0.0
        details = {
            "execution_success": False,
            "num_iterations": self.num_iterations,
            "iterations_completed": 0,
            "avg_cpu_percent": 0.0,
            "peak_memory_mb": 0.0,
            "avg_execution_time": 0.0,
            "cpu_scores": [],
            "memory_scores": [],
            "execution_times": []
        }
        error_message = ""
        
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short for performance analysis"
        else:
            working_dir = None
            script_path = None
            use_temp = True
            
            try:
                # Determine working directory and script path
                file_path_obj = Path(file_path)
                
                # Check if this is a task folder with generated_script_v*.py
                if file_path_obj.name.startswith("generated_script") and file_path_obj.name.endswith(".py") and file_path_obj.parent.exists():
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
                
                # Run multiple iterations
                all_cpu_readings = []
                all_memory_readings = []
                all_execution_times = []
                successful_iterations = 0
                
                for iteration in range(self.num_iterations):
                    cpu_readings = []
                    memory_readings = []
                    
                    try:
                        # Start the subprocess with working directory if available
                        popen_args = {
                            'stdout': subprocess.PIPE,
                            'stderr': subprocess.PIPE,
                            'text': True
                        }
                        if working_dir:
                            popen_args['cwd'] = working_dir
                        
                        process = subprocess.Popen(
                            ['python', script_path],
                            **popen_args
                        )
                        
                        # Get the process object for monitoring
                        psutil_process = psutil.Process(process.pid)
                        
                        # Monitor until process completes or times out
                        start_time = time.time()
                        monitoring = True
                        
                        def monitor_process():
                            while monitoring and process.poll() is None:
                                try:
                                    cpu_percent = psutil_process.cpu_percent(interval=0.1)
                                    if cpu_percent > 0:
                                        cpu_readings.append(cpu_percent)
                                    
                                    memory_info = psutil_process.memory_info()
                                    memory_readings.append(memory_info.rss)
                                    
                                    time.sleep(0.1)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    break
                        
                        # Start monitoring in a separate thread
                        monitor_thread = threading.Thread(target=monitor_process)
                        monitor_thread.start()
                        
                        # Wait for process with timeout
                        try:
                            stdout, stderr = process.communicate(timeout=self.timeout)
                            monitoring = False
                            monitor_thread.join(timeout=2)
                            
                            execution_time = time.time() - start_time
                            
                            if process.returncode == 0:
                                all_cpu_readings.extend(cpu_readings)
                                all_memory_readings.extend(memory_readings)
                                all_execution_times.append(execution_time)
                                successful_iterations += 1
                        except subprocess.TimeoutExpired:
                            monitoring = False
                            process.kill()
                            monitor_thread.join(timeout=2)
                            
                    except Exception:
                        pass
                
                details["iterations_completed"] = successful_iterations
                
                if successful_iterations > 0:
                    # Calculate metrics
                    if all_cpu_readings:
                        avg_cpu = sum(all_cpu_readings) / len(all_cpu_readings)
                        normalized_cpu = min(avg_cpu / 100.0, 1.0)
                    else:
                        avg_cpu = 0.0
                        normalized_cpu = 0.0
                    
                    if all_memory_readings:
                        peak_memory_bytes = max(all_memory_readings)
                        peak_memory_mb = peak_memory_bytes / (1024 * 1024)
                        normalized_memory = max(0.0, 1.0 - (peak_memory_mb / 1024.0))
                    else:
                        peak_memory_mb = 0.0
                        normalized_memory = 0.0
                    
                    avg_exec_time = sum(all_execution_times) / len(all_execution_times) if all_execution_times else 0.0
                    
                    # Calculate composite score
                    composite_score = 0.5 * (normalized_cpu + normalized_memory)
                    
                    details["avg_cpu_percent"] = round(avg_cpu, 2)
                    details["peak_memory_mb"] = round(peak_memory_mb, 2)
                    details["avg_execution_time"] = round(avg_exec_time, 3)
                    
                    passed = successful_iterations == self.num_iterations
                    score = round(composite_score, 4)
                    details["execution_success"] = True
                else:
                    error_message = "All execution iterations failed or timed out"
                    
            except Exception as e:
                error_message = f"Error during performance evaluation: {str(e)}"
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
