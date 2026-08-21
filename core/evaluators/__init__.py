"""
Base Evaluator Module

This module provides the base class for all evaluators.
New evaluators should inherit from BaseEvaluator.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class EvaluationResult:
    """Data class to store evaluation results."""
    file_path: str
    prompt_id: str
    model_name: str
    evaluator_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    timestamp: str
    error_message: str = ""


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.
    
    To create a new evaluator:
    1. Inherit from BaseEvaluator
    2. Implement the evaluate() method
    3. Return an EvaluationResult object
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate the given code and return results.
        
        Args:
            file_path: Path to the file being evaluated
            code_content: The actual code content as string
            metadata: Dictionary with metadata (prompt_id, model_name, etc.)
        
        Returns:
            EvaluationResult object with evaluation details
        """
        pass
    
    def get_name(self) -> str:
        """Return the name of this evaluator."""
        return self.name


# Import evaluators for easy access
from core.evaluators.syntax_evaluator import SyntaxEvaluator
from core.evaluators.security_evaluator import SecurityEvaluator
from core.evaluators.performance_evaluator import PerformanceEvaluator
from core.evaluators.radon_evaluator import RadonEvaluator
from core.evaluators.execution_evaluator import ExecutionEvaluator
from core.evaluators.functional_test_evaluator import FunctionalTestEvaluator
from core.evaluators.style_evaluator import StyleEvaluator
from core.evaluators.scalability_evaluator import ScalabilityEvaluator

__all__ = ['BaseEvaluator', 'EvaluationResult', 'SyntaxEvaluator', 'SecurityEvaluator', 'PerformanceEvaluator', 'RadonEvaluator', 'ExecutionEvaluator', 'FunctionalTestEvaluator', 'StyleEvaluator', 'ScalabilityEvaluator']
