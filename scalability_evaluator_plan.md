# ScalabilityEvaluator — Implementation Specification

## Overview

Add a new `ScalabilityEvaluator` to the existing evaluation pipeline that measures how generated Python code handles progressively larger datasets. The evaluator scales up input CSV files, runs the generated script at each scale, monitors memory and execution time, and kills the process if it exceeds 4GB RAM.

---

## Files to Create

### 1. `core/evaluators/scalability_utils.py`

Helper functions for scaling CSV datasets.

```python
# core/evaluators/scalability_utils.py

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Optional


def scale_csv(input_path: str, output_path: str, scale_factor: int, seed: int = 42) -> int:
    """
    Scale a CSV file by replicating rows with realistic variation.
    
    Args:
        input_path: Path to original CSV
        output_path: Path to write scaled CSV
        scale_factor: Multiply rows by this factor (1 = copy as-is)
        seed: Random seed for reproducible jitter
    
    Returns:
        Number of rows in the scaled CSV
    """
    np.random.seed(seed)
    
    df = pd.read_csv(input_path)
    original_rows = len(df)
    
    if scale_factor == 1:
        df.to_csv(output_path, index=False)
        return original_rows
    
    target_rows = original_rows * scale_factor
    
    # Tile the dataframe to reach target_rows
    repeats = int(np.ceil(target_rows / original_rows))
    scaled_df = pd.concat([df] * repeats, ignore_index=True)
    scaled_df = scaled_df.iloc[:target_rows]
    
    # Apply transformations for realistic data
    id_pattern = re.compile(r'.*[Ii][Dd]$|.*_id$|.*_Id$')
    
    for col in df.columns:
        if id_pattern.match(col):
            # Re-increment ID columns sequentially
            scaled_df[col] = range(1, target_rows + 1)
            continue
        
        if pd.api.types.is_numeric_dtype(df[col]):
            # Add ±1% jitter to numeric columns
            noise = np.random.uniform(0.99, 1.01, size=target_rows)
            scaled_df[col] = scaled_df[col] * noise
            # Round integers back
            if pd.api.types.is_integer_dtype(df[col]):
                scaled_df[col] = scaled_df[col].round().astype(int)
            continue
        
        if pd.api.types.is_object_dtype(df[col]):
            # For categorical/text columns, randomly sample from existing unique values
            # with some probability of introducing the column's mode
            unique_vals = df[col].dropna().unique().tolist()
            if unique_vals:
                # Keep original values where possible, fill rest randomly
                scaled_df[col] = np.random.choice(unique_vals, size=target_rows)
    
    scaled_df.to_csv(output_path, index=False)
    return target_rows


def find_csv_files(task_folder: str) -> List[str]:
    """Find all CSV files in a task folder (excluding output.csv)."""
    folder = Path(task_folder)
    csv_files = []
    for f in folder.glob("*.csv"):
        if f.name != "output.csv":
            csv_files.append(str(f))
    return sorted(csv_files)


def estimate_input_rows(task_folder: str) -> int:
    """Read the first CSV found and return its row count."""
    csv_files = find_csv_files(task_folder)
    if not csv_files:
        return 0
    df = pd.read_csv(csv_files[0])
    return len(df)
```

---

### 2. `core/evaluators/scalability_evaluator.py`

The main evaluator class.

```python
# core/evaluators/scalability_evaluator.py

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
    """
    Evaluator that measures how generated code scales with increasing data size.
    
    Runs the generated script at multiple scale factors (50x, 100x, 500x, 1000x, 5000x)
    and measures execution time and peak memory usage. Enforces a 4GB memory limit.
    
    Tasks without CSV input files are skipped (score = 0, passed = False).
    """
    
    def __init__(self, 
                 scale_factors: List[int] = None,
                 timeout: int = 60, 
                 memory_limit_mb: int = 4096):
        """
        Args:
            scale_factors: Multipliers to apply to input data size
            timeout: Seconds per scale level before killing the process
            memory_limit_mb: Kill process if RSS exceeds this
        """
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
            return EvaluationResult(...)
        
        # Determine task folder
        file_path_obj = Path(file_path)
        task_folder = str(file_path_obj.parent)
        
        # Find CSV input files
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
        
        # Get baseline info
        baseline_rows = estimate_input_rows(task_folder)
        details["baseline_rows"] = baseline_rows
        
        # Include 1x in the factors for baseline measurement
        all_factors = [1] + self.scale_factors
        script_name = file_path_obj.name
        
        scale_results = []
        last_passed_scale = 0
        last_passed_factor = 0
        
        for factor in all_factors:
            temp_dir = None
            try:
                # Create temp directory and copy all task files
                temp_dir = tempfile.mkdtemp(prefix=f"scalability_{factor}x_")
                temp_path = Path(temp_dir)
                
                # Copy all files from task folder
                for item in Path(task_folder).iterdir():
                    if item.is_file():
                        shutil.copy2(item, temp_path / item.name)
                
                # Scale CSV files (factor=1 means copy as-is for baseline)
                for csv_file in csv_files:
                    csv_name = Path(csv_file).name
                    scale_csv(csv_file, str(temp_path / csv_name), factor)
                
                # Run the generated script
                start_time = time.time()
                
                process = subprocess.Popen(
                    ['python', script_name],
                    cwd=str(temp_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Monitor memory in background thread
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
                    break  # Stop at first failure
                
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
                
                # Record baseline time from factor=1
                if factor == 1 and status == "passed":
                    details["baseline_time_sec"] = round(execution_time, 3)
                
                # Stop if scale test failed (don't continue to larger scales)
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
        
        # Compute composite score
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
                
                # Time score: 1.0 if perfectly linear, lower if super-linear
                time_score = min(1.0, expected_time / actual_time) if actual_time > 0 else 0.0
                
                # Memory score: 1.0 if using 0MB, ~1.0 if using small fraction, penalized near limit
                mem_used = r["peak_memory_mb"]
                mem_score = max(0.0, 1.0 - (mem_used / self.memory_limit_mb))
                
                combined = 0.5 * time_score + 0.5 * mem_score
                scale_scores.append(combined)
            
            # Average score across passed scales, penalized by how many scales were attempted but failed
            total_attempted = len([r for r in scale_results if r["scale_factor"] > 0])
            passed_count = len(passed_results)
            completion_ratio = passed_count / total_attempted if total_attempted > 0 else 0
            
            score = round(sum(scale_scores) / len(scale_scores) * completion_ratio, 4)
            passed = score > 0.3  # Threshold: at least survived some scaling reasonably
        
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
```

---

## Files to Modify

### 3. `core/evaluators/__init__.py`

Add the import and `__all__` entry:

```python
from core.evaluators.scalability_evaluator import ScalabilityEvaluator

__all__ = ['BaseEvaluator', 'EvaluationResult', 'SyntaxEvaluator', 'SecurityEvaluator', 
           'PerformanceEvaluator', 'RadonEvaluator', 'ExecutionEvaluator', 
           'FunctionalTestEvaluator', 'StyleEvaluator', 'ScalabilityEvaluator']
```

### 4. `evaluate.py`

Add `ScalabilityEvaluator` to the evaluator list in `run_quality_evaluation_for_sample()`:

```python
from core.evaluators.scalability_evaluator import ScalabilityEvaluator

# Inside run_quality_evaluation_for_sample(), add to evaluators list:
evaluators = [
    ("Syntax", SyntaxEvaluator()),
    ("Style", StyleEvaluator()),
    ("Security", SecurityEvaluator()),
    ("Execution", ExecutionEvaluator()),
    ("Performance", PerformanceEvaluator()),
    ("Radon", RadonEvaluator()),
    ("Scalability", ScalabilityEvaluator()),
]
```

### 5. `analyze_results.py`

Add two new chart functions + call them from `main()`:

```python
# New evaluator name in the evaluators list
EVALUATORS.append("Scalability")

# In create_evaluator_comparison_bars():
evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional', 'Scalability']

# In create_sample_consistency_bars():
evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional', 'Scalability']

# In create_individual_evaluator_graphs():
evaluators = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Functional', 'Scalability']

# Add to model ranking (skipping functional):
eval_names = ['Syntax', 'Style', 'Security', 'Execution', 'Performance', 'Radon', 'Scalability']

# New function: create_scalability_curves()
def create_scalability_curves(data, output_dir):
    """
    Chart 17: Two-panel plot showing execution time and memory vs. scale factor.
    - Left: Time (seconds) vs Scale Factor (log scale)
    - Right: Peak Memory (MB) vs Scale Factor (log scale)
    - One line per model (averaged across tasks)
    - Dashed reference line for ideal linear scaling on time plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    models = list(data["models"].keys())
    
    # Collect scale data per model
    model_scale_data = {}
    
    for model_name, model_info in data["models"].items():
        # Aggregate scale results across all tasks
        time_by_factor = {}   # factor -> list of times
        mem_by_factor = {}    # factor -> list of memories
        
        for task_id, task_data in model_info["tasks"].items():
            for sample in task_data.get("samples", []):
                details = sample.get("quality", {}).get("Scalability", {}).get("details", {})
                if not details:
                    continue
                
                for result in details.get("scale_results", []):
                    factor = result["scale_factor"]
                    if factor == 1:
                        continue
                    if result["status"] != "passed":
                        continue
                    
                    if factor not in time_by_factor:
                        time_by_factor[factor] = []
                        mem_by_factor[factor] = []
                    
                    time_by_factor[factor].append(result["execution_time_sec"])
                    mem_by_factor[factor].append(result["peak_memory_mb"])
        
        if time_by_factor:
            model_scale_data[model_name] = {
                "factors": sorted(time_by_factor.keys()),
                "avg_times": [np.mean(time_by_factor[f]) for f in sorted(time_by_factor.keys())],
                "avg_memory": [np.mean(mem_by_factor[f]) for f in sorted(time_by_factor.keys())],
                "std_times": [np.std(time_by_factor[f]) if len(time_by_factor[f]) > 1 else 0 for f in sorted(time_by_factor.keys())],
                "std_memory": [np.std(mem_by_factor[f]) if len(mem_by_factor[f]) > 1 else 0 for f in sorted(time_by_factor.keys())],
            }
    
    if not model_scale_data:
        print("[SKIP] No scalability data found")
        plt.close()
        return
    
    # Plot Time vs Scale (left panel)
    for model_name, data in model_scale_data.items():
        factors = data["factors"]
        ax1.plot(factors, data["avg_times"], marker='o', label=model_name, 
                 color=get_model_color(model_name), linewidth=2)
        ax1.fill_between(factors, 
                         np.array(data["avg_times"]) - np.array(data["std_times"]),
                         np.array(data["avg_times"]) + np.array(data["std_times"]),
                         color=get_model_color(model_name), alpha=0.15)
    
    # Add ideal linear reference line
    all_times = [t for d in model_scale_data.values() for t in d["avg_times"]]
    all_factors = [f for d in model_scale_data.values() for f in d["factors"]]
    if all_times and all_factors:
        min_time = min(all_times)
        min_factor = min(all_factors)
        max_factor = max(all_factors)
        if min_factor > 0:
            ideal_x = [min_factor, max_factor]
            ideal_y = [min_time, min_time * (max_factor / min_factor)]
            ax1.plot(ideal_x, ideal_y, 'k--', linewidth=2, alpha=0.5, label='Ideal linear')
    
    ax1.set_xscale('log')
    ax1.set_xlabel('Scale Factor (log scale)', fontweight='bold')
    ax1.set_ylabel('Execution Time (seconds)', fontweight='bold')
    ax1.set_title('Execution Time vs. Data Size', fontweight='bold', pad=15)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Plot Memory vs Scale (right panel)
    for model_name, data in model_scale_data.items():
        factors = data["factors"]
        ax2.plot(factors, data["avg_memory"], marker='s', label=model_name,
                 color=get_model_color(model_name), linewidth=2)
        ax2.fill_between(factors,
                         np.array(data["avg_memory"]) - np.array(data["std_memory"]),
                         np.array(data["avg_memory"]) + np.array(data["std_memory"]),
                         color=get_model_color(model_name), alpha=0.15)
    
    # Add 4GB memory limit reference line
    ax2.axhline(y=4096, color='r', linestyle='--', linewidth=2, alpha=0.7, label='4GB Limit')
    
    ax2.set_xscale('log')
    ax2.set_xlabel('Scale Factor (log scale)', fontweight='bold')
    ax2.set_ylabel('Peak Memory (MB)', fontweight='bold')
    ax2.set_title('Peak Memory vs. Data Size', fontweight='bold', pad=15)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '17_scalability_curves.png', bbox_inches='tight')
    plt.close()
    print("[OK] Created: 17_scalability_curves.png")


# Also add a new individual chart: 18_scalability.png
def create_scalability_individual_bars(data, output_dir):
    """Chart 18: Individual bar chart for Scalability pass rate per model."""
    # Same pattern as create_individual_evaluator_graphs but just for Scalability
    # (Actually can be skipped if create_individual_evaluator_graphs is updated to include Scalability)


# In main(), add calls:
create_scalability_curves(data, output_dir)
```

---

## Integration Checklist

| Step | File | Action |
|------|------|--------|
| 1 | `core/evaluators/scalability_utils.py` | Create new file |
| 2 | `core/evaluators/scalability_evaluator.py` | Create new file |
| 3 | `core/evaluators/__init__.py` | Add `ScalabilityEvaluator` to imports and `__all__` |
| 4 | `evaluate.py` | Import `ScalabilityEvaluator`, add to evaluators list |
| 5 | `analyze_results.py` | Add Scalability to evaluator lists, add `create_scalability_curves()`, add call in `main()` |

---

## Edge Cases to Handle

1. **No CSV files in task folder**: Score 0, `passed=False`, `tasks_without_csv=True`
2. **Non-pandas script**: Some scripts may use csv module instead of pandas — the scaling still works
3. **Script writes intermediate files**: All run in temp dir, so no pollution
4. **Scale factor already breaks at 1x**: Score 0 immediately
5. **Very fast execution** (< 0.01s baseline): Time ratio calculation still works
6. **psutil not installed**: Raise clear error at evaluator init
7. **Multiple CSV inputs (join tasks)**: Both files get scaled proportionally, preserving relationships

---

## Testing

After implementation, verify with:

```bash
# Run evaluation on existing generated code
python evaluate.py

# Check output includes Scalability results
# Look for "Scalability" in console output

# Generate graphs
python analyze_results.py

# Check for 17_scalability_curves.png in graphs/
```