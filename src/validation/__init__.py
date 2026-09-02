"""
Validation Module
=================

Multi-strategy validation for different use cases.

Use Cases:
- MESSAGING: tone, format, boundaries (standard validation)
- CODING: syntax, semantics, Ponytail plugin quality check
- MENDIX: domain rules + Ponytail for Mendix code quality

Validation Flow:
1. Detect use case (messaging vs coding vs Mendix)
2. Route to appropriate validator
3. Combine results from all applicable checks
"""

from src.validation.use_case_detector import (
    UseCase,
    UseCaseDetector,
    detect_use_case,
    get_use_case_detector,
)

__all__ = [
    "UseCase",
    "UseCaseDetector",
    "detect_use_case",
    "get_use_case_detector",
]
