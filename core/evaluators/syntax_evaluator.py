"""
Syntax Evaluator Module

Checks Python code for syntax correctness using AST parsing.
"""

import ast
from typing import Dict, Any
from datetime import datetime

from core.evaluators import BaseEvaluator, EvaluationResult


class SyntaxEvaluator(BaseEvaluator):
    """
    Evaluator that checks if Python code has valid syntax.
    Uses Python's built-in ast module to parse the code.
    """
    
    def __init__(self):
        super().__init__("SyntaxEvaluator")
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Check if the code has valid Python syntax.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult with syntax check results
        """
        passed = False
        score = 0.0
        details = {
            "syntax_valid": False,
            "ast_parsed": False,
            "line_count": len(code_content.splitlines()),
            "char_count": len(code_content)
        }
        error_message = ""
        
        try:
            # Check if content is empty or too short
            if not code_content or len(code_content.strip()) < 10:
                error_message = "Code content is empty or too short"
                details["syntax_valid"] = False
                score = 0.0
            else:
                # Try to parse the code using AST
                ast.parse(code_content)
                
                # If we get here, syntax is valid
                passed = True
                score = 1.0
                details["syntax_valid"] = True
                details["ast_parsed"] = True
                
        except SyntaxError as e:
            error_message = f"Syntax error on line {e.lineno}: {e.msg}"
            details["syntax_valid"] = False
            details["error_line"] = e.lineno
            details["error_offset"] = e.offset
            details["error_text"] = e.text
            score = 0.0
            
        except Exception as e:
            error_message = f"Unexpected error during syntax check: {str(e)}"
            details["syntax_valid"] = False
            score = 0.0
        
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
