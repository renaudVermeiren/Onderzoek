"""
Security Evaluator Module

Evaluates Python code for security vulnerabilities using Bandit.
Based on ISO/IEC 5055:2021 security category as described in:
Krebs, R., & Mazumdar, S. (2025). Analyzing LLM-Generated Code According to 
Four ISO/IEC 5055:2021 Categories. IEEE Access, 13, 202482-202499.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult


class SecurityEvaluator(BaseEvaluator):
    """
    Evaluator that checks Python code for security vulnerabilities.
    Uses Bandit static analysis tool to detect security issues.
    
    Following ISO/IEC 5055:2021, this evaluator assesses:
    - Security violations (SVs): Critical security issues
    - Warnings: Potential security concerns
    - Errors: Security-related errors
    
    The composite security score is calculated as:
    S = 1/3(SVs + Warnings + Errors)
    """
    
    def __init__(self):
        super().__init__("SecurityEvaluator")
        self._check_bandit_installed()
    
    def _check_bandit_installed(self):
        """Check if Bandit is installed and available."""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Bandit not properly installed")
        except FileNotFoundError:
            raise RuntimeError(
                "Bandit is not installed. Install it with: pip install bandit"
            )
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Check the code for security vulnerabilities using Bandit.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult with security check results
        """
        passed = False
        score = 0.0
        details = {
            "security_violations": 0,
            "warnings": 0,
            "errors": 0,
            "low_severity": 0,
            "medium_severity": 0,
            "high_severity": 0,
            "bandit_skipped": False
        }
        error_message = ""
        
        # Check if content is empty or too short
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short for security analysis"
            score = 0.0
            passed = False
            details["bandit_skipped"] = True
        else:
            try:
                # Use the actual file path when available, otherwise fall back to temp file
                file_path_obj = Path(file_path)
                use_temp = not (file_path_obj.exists() and file_path_obj.suffix == '.py')
                
                if use_temp:
                    # Write code to temporary file
                    with tempfile.NamedTemporaryFile(
                        mode='w', 
                        suffix='.py', 
                        delete=False,
                        encoding='utf-8'
                    ) as tmp_file:
                        tmp_file.write(code_content)
                        target_path = tmp_file.name
                else:
                    target_path = str(file_path_obj)
                
                try:
                    # Run Bandit with JSON output
                    result = subprocess.run(
                        [
                            "bandit",
                            "-f", "json",
                            "-r", target_path,
                            "--skip", "B101"  # Skip assert_used warnings
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    # Parse Bandit output
                    bandit_output = json.loads(result.stdout)
                    
                    # Extract security metrics
                    results = bandit_output.get("results", [])
                    
                    # Categorize by severity
                    details["low_severity"] = sum(1 for r in results if r.get("issue_severity") == "LOW")
                    details["medium_severity"] = sum(1 for r in results if r.get("issue_severity") == "MEDIUM")
                    details["high_severity"] = sum(1 for r in results if r.get("issue_severity") == "HIGH")
                    
                    # Categorize by issue type for ISO 5055
                    for issue in results:
                        severity = issue.get("issue_severity", "LOW")
                        issue_text = issue.get("issue_text", "")
                        
                        # Count as security violation if high severity
                        if severity == "HIGH":
                            details["security_violations"] += 1
                        # Count as warning if medium severity
                        elif severity == "MEDIUM":
                            details["warnings"] += 1
                        # Count as low-level concern
                        else:
                            details["errors"] += 1
                    
                    # Calculate composite score following ISO 5055
                    # S = 1/3(SVs + Warnings + Errors), inverted so higher is better
                    total_issues = (
                        details["security_violations"] + 
                        details["warnings"] + 
                        details["errors"]
                    )
                    
                    if total_issues == 0:
                        score = 1.0
                    else:
                        # Normalize: fewer issues = higher score
                        # Using exponential decay for scoring
                        score = max(0.0, 1.0 - (total_issues * 0.1))
                    
                    # Pass if no high severity issues
                    passed = details["high_severity"] == 0
                    
                    details["total_issues_found"] = total_issues
                    details["bandit_exit_code"] = result.returncode
                    details["used_temp_file"] = use_temp
                    
                finally:
                    # Clean up temporary file only if we created one
                    if use_temp:
                        try:
                            os.unlink(target_path)
                        except:
                            pass
                        
            except subprocess.TimeoutExpired:
                error_message = "Bandit analysis timed out (30s)"
                score = 0.0
                passed = False
                details["bandit_skipped"] = True
                
            except json.JSONDecodeError:
                error_message = "Failed to parse Bandit output"
                score = 0.0
                passed = False
                
            except Exception as e:
                error_message = f"Error during security analysis: {str(e)}"
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
