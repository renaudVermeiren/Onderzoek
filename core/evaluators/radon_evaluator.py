"""
Radon Evaluator Module

Evaluates Python code for complexity and maintainability using Radon.
Based on ISO/IEC 5055:2021 Maintainability category as described in:
Krebs, R., & Mazumdar, S. (2025). Analyzing LLM-Generated Code According to 
Four ISO/IEC 5055:2021 Categories. IEEE Access, 13, 202482-202499.

Radon computes four key software metrics:
1. Cyclomatic Complexity - measures decision points in code
2. Maintainability Index - evaluates code quality based on complexity, size, documentation
3. Halstead Metrics - estimates delivered bugs using software complexity metrics
4. Source Code Statistics - LOC and comments-to-code ratio
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult


class RadonEvaluator(BaseEvaluator):
    """
    Evaluator that measures code complexity and maintainability using Radon.
    
    Following ISO/IEC 5055:2021 Maintainability category from Krebs & Mazumdar (2025):
    - Cyclomatic Complexity: Number of decision points
    - Maintainability Index: Based on complexity, size, and documentation
    - Halstead Bugs: Estimated using Halstead complexity metrics
    - Raw metrics: LOC, SLOC, comments, multi-line strings
    
    The composite maintainability score follows the paper's formula:
    M = 1/3 * (MI + (C+R)/2 + (C-to-LOC + SLOC-to-M)/2)
    
    Where:
    - MI: Maintainability Index
    - C: Convention violations (from other tools)
    - R: Refactoring checks (from other tools)
    - C-to-LOC: Comments to lines of code ratio
    - SLOC-to-M: Source lines per method
    """
    
    def __init__(self):
        super().__init__("RadonEvaluator")
        self._check_radon_installed()
    
    def _check_radon_installed(self):
        """Check if Radon is installed and available."""
        try:
            result = subprocess.run(
                ["radon", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Radon not properly installed")
        except FileNotFoundError:
            raise RuntimeError(
                "Radon is not installed. Install it with: pip install radon"
            )
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Check the code for complexity and maintainability using Radon.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult with Radon analysis results
        """
        passed = False
        score = 0.0
        details = {
            "cyclomatic_complexity": {},
            "maintainability_index": 0.0,
            "halstead_metrics": {},
            "raw_metrics": {},
            "average_complexity": 0.0,
            "max_complexity": 0,
            "total_functions": 0,
            "lines_of_code": 0,
            "source_lines": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "comments_to_loc_ratio": 0.0,
            "radon_analysis_success": False
        }
        error_message = ""
        
        # Check if content is empty or too short
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short for Radon analysis"
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
                    # Run Radon CC (Cyclomatic Complexity)
                    cc_result = self._run_radon_cc(tmp_path)
                    
                    # Run Radon MI (Maintainability Index)
                    mi_result = self._run_radon_mi(tmp_path)
                    
                    # Run Radon Halstead metrics
                    hal_result = self._run_radon_hal(tmp_path)
                    
                    # Run Radon Raw metrics
                    raw_result = self._run_radon_raw(tmp_path)
                    
                    # Parse and combine results
                    details["cyclomatic_complexity"] = cc_result
                    details["maintainability_index"] = mi_result.get("mi", 0)
                    details["halstead_metrics"] = hal_result
                    details["raw_metrics"] = raw_result
                    
                    # Extract key metrics
                    if cc_result:
                        complexities = [item.get("complexity", 0) for item in cc_result.values() if isinstance(item, dict)]
                        if complexities:
                            details["average_complexity"] = round(sum(complexities) / len(complexities), 2)
                            details["max_complexity"] = max(complexities)
                            details["total_functions"] = len(complexities)
                    
                    # Extract raw metrics
                    if raw_result:
                        details["lines_of_code"] = raw_result.get("loc", 0)
                        details["source_lines"] = raw_result.get("sloc", 0)
                        details["blank_lines"] = raw_result.get("blank", 0)
                        details["comment_lines"] = raw_result.get("comments", 0)
                        
                        # Calculate comments-to-LOC ratio
                        if details["lines_of_code"] > 0:
                            details["comments_to_loc_ratio"] = round(
                                details["comment_lines"] / details["lines_of_code"], 4
                            )
                    
                    # Calculate score based on maintainability index (0-100 scale)
                    mi = details["maintainability_index"]
                    if mi >= 80:
                        score = 1.0  # Excellent
                        passed = True
                    elif mi >= 60:
                        score = 0.8  # Good
                        passed = True
                    elif mi >= 40:
                        score = 0.6  # Fair
                        passed = True
                    elif mi >= 20:
                        score = 0.4  # Poor
                        passed = False
                    else:
                        score = 0.2  # Very Poor
                        passed = False
                    
                    # Adjust score based on complexity
                    avg_cc = details["average_complexity"]
                    if avg_cc > 10:
                        # High complexity reduces score
                        score = max(0.0, score - 0.2)
                    elif avg_cc > 7:
                        score = max(0.0, score - 0.1)
                    
                    details["radon_analysis_success"] = True
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
            except Exception as e:
                error_message = f"Error during Radon analysis: {str(e)}"
                score = 0.0
                passed = False
        
        return EvaluationResult(
            file_path=file_path,
            prompt_id=metadata.get("prompt_id", "unknown"),
            model_name=metadata.get("model_name", "unknown"),
            evaluator_name=self.name,
            passed=passed,
            score=round(score, 4),
            details=details,
            timestamp=datetime.now().isoformat(),
            error_message=error_message
        )
    
    def _run_radon_cc(self, file_path: str) -> Dict[str, Any]:
        """Run Radon cyclomatic complexity analysis."""
        try:
            result = subprocess.run(
                ["radon", "cc", "-j", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode in [0, 1]:  # 1 means some blocks are complex but still valid output
                output = result.stdout.strip()
                if output:
                    return json.loads(output)
            return {}
        except:
            return {}
    
    def _run_radon_mi(self, file_path: str) -> Dict[str, Any]:
        """Run Radon maintainability index analysis."""
        try:
            result = subprocess.run(
                ["radon", "mi", "-j", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    data = json.loads(output)
                    # Extract MI for our file
                    return data.get(file_path, {"mi": 0})
            return {"mi": 0}
        except:
            return {"mi": 0}
    
    def _run_radon_hal(self, file_path: str) -> Dict[str, Any]:
        """Run Radon Halstead metrics analysis."""
        try:
            result = subprocess.run(
                ["radon", "hal", "-j", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    return json.loads(output)
            return {}
        except:
            return {}
    
    def _run_radon_raw(self, file_path: str) -> Dict[str, Any]:
        """Run Radon raw metrics analysis."""
        try:
            result = subprocess.run(
                ["radon", "raw", "-j", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    data = json.loads(output)
                    # Extract metrics for our file
                    return data.get(file_path, {})
            return {}
        except:
            return {}
