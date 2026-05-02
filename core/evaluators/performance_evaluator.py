"""
Performance Evaluator Module

Evaluates Python code performance by executing it and measuring
CPU and memory usage using psutil.
Based on ISO/IEC 5055:2021 Performance Efficiency category as described in:
Krebs, R., & Mazumdar, S. (2025). Analyzing LLM-Generated Code According to 
Four ISO/IEC 5055:2021 Categories. IEEE Access, 13, 202482-202499.
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
    """
    Evaluator that measures code performance (CPU and memory usage).
    
    Following the methodology from Krebs & Mazumdar (2025):
    - Executes code in isolated subprocess
    - Monitors CPU usage percentage during execution
    - Monitors memory usage (RSS) during execution
    - Runs multiple iterations to get stable measurements
    - Calculates composite score: PE = 1/2(CPU + Memory)
    
    Note: This evaluator requires psutil to be installed:
    pip install psutil
    """
    
    def __init__(self, num_iterations: int = 3, timeout: int = 30):
        """
        Initialize the performance evaluator.
        
        Args:
            num_iterations: Number of times to execute the code for averaging (default: 3)
            timeout: Maximum execution time per iteration in seconds (default: 30)
        """
        super().__init__("PerformanceEvaluator")
        self.num_iterations = num_iterations
        self.timeout = timeout
        self._check_psutil_installed()
    
    def _check_psutil_installed(self):
        """Check if psutil is installed."""
        try:
            import psutil
        except ImportError:
            raise RuntimeError(
                "psutil is not installed. Install it with: pip install psutil"
            )
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Execute the code and measure CPU and memory performance.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult with performance metrics
        """
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
        
        # Check if content is empty or too short
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short for performance analysis"
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
                    # Run multiple iterations to get stable measurements
                    all_cpu_readings = []
                    all_memory_readings = []
                    all_execution_times = []
                    successful_iterations = 0
                    
                    for iteration in range(self.num_iterations):
                        cpu_readings, memory_readings, exec_time, success = self._execute_and_monitor(
                            tmp_path, psutil
                        )
                        
                        if success:
                            all_cpu_readings.extend(cpu_readings)
                            all_memory_readings.extend(memory_readings)
                            all_execution_times.append(exec_time)
                            successful_iterations += 1
                    
                    details["iterations_completed"] = successful_iterations
                    
                    if successful_iterations == 0:
                        error_message = "All execution iterations failed or timed out"
                        score = 0.0
                        passed = False
                    else:
                        # Calculate average metrics
                        if all_cpu_readings:
                            avg_cpu = sum(all_cpu_readings) / len(all_cpu_readings)
                            # Normalize CPU to 0-1 range (assuming max 100%)
                            normalized_cpu = min(avg_cpu / 100.0, 1.0)
                        else:
                            avg_cpu = 0.0
                            normalized_cpu = 0.0
                        
                        if all_memory_readings:
                            # Convert to MB and get peak
                            peak_memory_bytes = max(all_memory_readings)
                            peak_memory_mb = peak_memory_bytes / (1024 * 1024)
                            # Normalize memory (assuming max 1GB = 1024MB for scoring)
                            # Lower memory is better, so we invert the score
                            normalized_memory = max(0.0, 1.0 - (peak_memory_mb / 1024.0))
                        else:
                            peak_memory_mb = 0.0
                            normalized_memory = 0.0
                        
                        avg_exec_time = sum(all_execution_times) / len(all_execution_times) if all_execution_times else 0.0
                        
                        # Calculate composite score following ISO 5055
                        # PE = 1/2(CPU + Memory) - but we want lower usage to be better
                        # So we use the normalized values where higher is better (less usage = better score)
                        # Actually, the paper normalizes and inverts so lower usage = higher score
                        composite_score = 0.5 * (normalized_cpu + normalized_memory)
                        
                        details["avg_cpu_percent"] = round(avg_cpu, 2)
                        details["peak_memory_mb"] = round(peak_memory_mb, 2)
                        details["avg_execution_time"] = round(avg_exec_time, 3)
                        details["normalized_cpu_score"] = round(normalized_cpu, 4)
                        details["normalized_memory_score"] = round(normalized_memory, 4)
                        
                        # Pass if we completed all iterations successfully
                        passed = successful_iterations == self.num_iterations
                        score = round(composite_score, 4)
                        details["execution_success"] = True
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
            except Exception as e:
                error_message = f"Error during performance evaluation: {str(e)}"
                score = 0.0
                passed = False
        
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
    
    def _execute_and_monitor(self, script_path: str, psutil_module) -> tuple:
        """
        Execute a Python script and monitor its resource usage.
        
        Args:
            script_path: Path to the Python script to execute
            psutil_module: The psutil module
        
        Returns:
            Tuple of (cpu_readings, memory_readings, execution_time, success)
        """
        cpu_readings = []
        memory_readings = []
        
        try:
            # Start the subprocess
            process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Get the process object for monitoring
            psutil_process = psutil_module.Process(process.pid)
            
            # Monitor until process completes or times out
            start_time = time.time()
            monitoring = True
            
            def monitor_process():
                nonlocal monitoring
                while monitoring and process.poll() is None:
                    try:
                        # Get CPU percent (interval=None for non-blocking)
                        cpu_percent = psutil_process.cpu_percent(interval=0.1)
                        if cpu_percent > 0:  # Only record non-zero values
                            cpu_readings.append(cpu_percent)
                        
                        # Get memory info
                        memory_info = psutil_process.memory_info()
                        memory_readings.append(memory_info.rss)
                        
                        # Small delay to prevent excessive polling
                        time.sleep(0.1)
                    except (psutil_module.NoSuchProcess, psutil_module.AccessDenied):
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
                    return cpu_readings, memory_readings, execution_time, True
                else:
                    return cpu_readings, memory_readings, execution_time, False
                    
            except subprocess.TimeoutExpired:
                monitoring = False
                process.kill()
                monitor_thread.join(timeout=2)
                return cpu_readings, memory_readings, self.timeout, False
                
        except Exception as e:
            return cpu_readings, memory_readings, 0, False
