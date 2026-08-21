import subprocess
import tempfile
import shutil
import os
import time
import threading
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult
from core.evaluators.scalability_utils import scale_csv, find_csv_files, estimate_input_rows


class ScalabilityEvaluator(BaseEvaluator):
    def __init__(self,
                 scale_factors: List[int] = None,
                 timeout: int = 60,
                 memory_limit_mb: int = 2048):
        super().__init__("ScalabilityEvaluator")
        self.scale_factors = scale_factors or [50, 100, 500, 1000, 5000]
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self._check_psutil_installed()

    def _check_psutil_installed(self):
        try:
            import psutil
        except ImportError:
            raise RuntimeError("psutil is not installed. Install with: pip install psutil")

    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        import psutil

        passed = False
        score = 0.0
        details = {
            "memory_limit_mb": self.memory_limit_mb,
            "scale_results": [],
            "max_scale_passed": 0,
            "max_scale_factor": 0,
            "composite_score": 0.0,
            "baseline_time_sec": 0.0,
            "baseline_rows": 0,
            "tasks_without_csv": False
        }
        error_message = ""

        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short"
            return EvaluationResult(
                file_path=file_path,
                prompt_id=metadata.get("prompt_id", "unknown"),
                model_name=metadata.get("model_name", "unknown"),
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                details=details,
                timestamp=datetime.now().isoformat(),
                error_message=error_message
            )

        file_path_obj = Path(file_path)
        task_folder = str(file_path_obj.parent)

        csv_files = find_csv_files(task_folder)
        if not csv_files:
            details["tasks_without_csv"] = True
            error_message = "No CSV input files found in task folder - cannot test scalability"
            return EvaluationResult(
                file_path=file_path,
                prompt_id=metadata.get("prompt_id", "unknown"),
                model_name=metadata.get("model_name", "unknown"),
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                details=details,
                timestamp=datetime.now().isoformat(),
                error_message=error_message
            )

        baseline_rows = estimate_input_rows(task_folder)
        details["baseline_rows"] = baseline_rows

        all_factors = [1] + self.scale_factors
        script_name = file_path_obj.name

        scale_results = []
        last_passed_scale = 0
        last_passed_factor = 0

        for factor in all_factors:
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp(prefix=f"scalability_{factor}x_")
                temp_path = Path(temp_dir)

                for item in Path(task_folder).iterdir():
                    if item.is_file():
                        shutil.copy2(item, temp_path / item.name)

                for csv_file in csv_files:
                    csv_name = Path(csv_file).name
                    scale_csv(csv_file, str(temp_path / csv_name), factor)

                start_time = time.time()

                process = subprocess.Popen(
                    ['python', script_name],
                    cwd=str(temp_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                peak_memory_mb = 0.0
                killed_oom = False
                monitor_event = threading.Event()

                def monitor_memory(proc, limit_mb, stop_event):
                    nonlocal peak_memory_mb, killed_oom
                    try:
                        psutil_proc = psutil.Process(proc.pid)
                        while not stop_event.is_set() and proc.poll() is None:
                            try:
                                rss = psutil_proc.memory_info().rss
                                rss_mb = rss / (1024 * 1024)
                                peak_memory_mb = max(peak_memory_mb, rss_mb)
                                if rss_mb > limit_mb:
                                    proc.kill()
                                    killed_oom = True
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                break
                            time.sleep(0.05)
                    except Exception:
                        pass

                monitor_thread = threading.Thread(
                    target=monitor_memory,
                    args=(process, self.memory_limit_mb, monitor_event)
                )
                monitor_thread.start()

                try:
                    stdout, stderr = process.communicate(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    monitor_event.set()
                    monitor_thread.join(timeout=3)

                    result_entry = {
                        "scale_factor": factor,
                        "status": "timeout",
                        "execution_time_sec": round(time.time() - start_time, 3),
                        "peak_memory_mb": round(peak_memory_mb, 2),
                        "input_rows": baseline_rows * factor if factor > 1 else baseline_rows
                    }
                    scale_results.append(result_entry)
                    break

                monitor_event.set()
                monitor_thread.join(timeout=3)

                execution_time = time.time() - start_time
                input_rows = baseline_rows * factor if factor > 1 else baseline_rows

                if killed_oom:
                    status = "killed_OOM"
                elif process.returncode == 0:
                    status = "passed"
                    if factor > 1:
                        last_passed_scale = factor
                    last_passed_factor = factor
                else:
                    status = "crashed"

                result_entry = {
                    "scale_factor": factor,
                    "status": status,
                    "execution_time_sec": round(execution_time, 3),
                    "peak_memory_mb": round(peak_memory_mb, 2),
                    "input_rows": input_rows
                }
                scale_results.append(result_entry)

                if factor == 1 and status == "passed":
                    details["baseline_time_sec"] = round(execution_time, 3)

                if status != "passed":
                    break

            except Exception as e:
                scale_results.append({
                    "scale_factor": factor,
                    "status": "error",
                    "execution_time_sec": 0.0,
                    "peak_memory_mb": 0.0,
                    "error": str(e)
                })
                break
            finally:
                if temp_dir:
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass

        details["scale_results"] = scale_results
        details["max_scale_passed"] = last_passed_scale
        details["max_scale_factor"] = last_passed_factor

        passed_results = [r for r in scale_results if r["status"] == "passed" and r["scale_factor"] > 0]

        if not passed_results or details["baseline_time_sec"] == 0:
            score = 0.0
            passed = False
        else:
            scale_scores = []
            for r in passed_results:
                s = r["scale_factor"]
                expected_time = details["baseline_time_sec"] * s
                actual_time = r["execution_time_sec"]

                time_score = min(1.0, expected_time / actual_time) if actual_time > 0 else 0.0

                mem_used = r["peak_memory_mb"]
                mem_score = max(0.0, 1.0 - (mem_used / self.memory_limit_mb))

                combined = 0.5 * time_score + 0.5 * mem_score
                scale_scores.append(combined)

            total_attempted = len([r for r in scale_results if r["scale_factor"] > 0])
            passed_count = len(passed_results)
            completion_ratio = passed_count / total_attempted if total_attempted > 0 else 0

            score = round(sum(scale_scores) / len(scale_scores) * completion_ratio, 4)
            passed = score > 0.3

        details["composite_score"] = score

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