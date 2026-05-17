"""
Style / Semantics Evaluator Module

Evaluates Python code for semantic errors and style issues using Ruff.
Only reports error-level findings (E, W, F categories) to catch real
issues like undefined variables, unused imports, and syntax-adjacent bugs
that AST parsing alone misses.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from core.evaluators import BaseEvaluator, EvaluationResult


class StyleEvaluator(BaseEvaluator):
    """
    Evaluator that checks Python code for semantic and style errors using Ruff.

    Configured to only flag error-level findings:
      - E: pycodestyle errors
      - W: pycodestyle warnings
      - F: Pyflakes (undefined names, unused imports, etc.)
    """

    def __init__(self):
        super().__init__("StyleEvaluator")
        self._check_ruff_installed()

    def _check_ruff_installed(self):
        """Check if Ruff is installed and available."""
        try:
            result = subprocess.run(
                ["python", "-m", "ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Ruff not properly installed")
        except FileNotFoundError:
            raise RuntimeError(
                "Ruff is not installed. Install it with: pip install ruff"
            )

    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Check the code for semantic/style errors using Ruff.

        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)

        Returns:
            EvaluationResult with style check results
        """
        passed = False
        score = 0.0
        details = {
            "total_errors": 0,
            "total_warnings": 0,
            "total_fixes": 0,
            "error_codes": [],
            "ruff_skipped": False
        }
        error_message = ""

        # Check if content is empty or too short
        if not code_content or len(code_content.strip()) < 10:
            error_message = "Code content is empty or too short for style analysis"
            score = 0.0
            passed = False
            details["ruff_skipped"] = True
        else:
            try:
                # Use the actual file path when available, otherwise fall back to temp file
                file_path_obj = Path(file_path)
                use_temp = not (file_path_obj.exists() and file_path_obj.suffix == '.py')

                if use_temp:
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
                    # Run Ruff with JSON output, selecting only error-level rules
                    result = subprocess.run(
                        [
                            "python", "-m", "ruff",
                            "check",
                            "--select", "E,W,F",
                            "--output-format", "json",
                            target_path
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    # Ruff returns 0 when no issues found, 1 when issues found
                    # Parse JSON output
                    try:
                        ruff_output = json.loads(result.stdout) if result.stdout.strip() else []
                    except json.JSONDecodeError:
                        ruff_output = []

                    # Categorize findings
                    errors = []
                    warnings = []
                    for finding in ruff_output:
                        code = finding.get("code", "")
                        # F-rules are semantic errors (undefined names, etc.)
                        # E-rules are pycodestyle errors
                        if code.startswith("F") or code.startswith("E9"):
                            errors.append(finding)
                        else:
                            warnings.append(finding)

                    details["total_errors"] = len(errors)
                    details["total_warnings"] = len(warnings)
                    details["error_codes"] = sorted(list(set(
                        f.get("code", "") for f in ruff_output
                    )))
                    details["used_temp_file"] = use_temp

                    total_issues = len(ruff_output)

                    if total_issues == 0:
                        score = 1.0
                        passed = True
                    else:
                        # Penalize errors more heavily than warnings
                        weighted_score = max(0.0, 1.0 - (len(errors) * 0.15) - (len(warnings) * 0.05))
                        score = round(weighted_score, 4)
                        # Pass only if no semantic errors (F-rules)
                        passed = len(errors) == 0

                finally:
                    if use_temp:
                        try:
                            os.unlink(target_path)
                        except Exception:
                            pass

            except subprocess.TimeoutExpired:
                error_message = "Ruff analysis timed out (30s)"
                score = 0.0
                passed = False
                details["ruff_skipped"] = True

            except Exception as e:
                error_message = f"Error during style analysis: {str(e)}"
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
