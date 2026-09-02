"""
Check Draft Implementation
==========================

Validation implementation for each use case.
Combines deterministic + MCP sampling validation.
"""

from uuid import UUID

from src.validation import UseCase
from src.validation.models import ValidationResult, ValidationMethod
from src.validation.deterministic import (
    get_messaging_validator,
    get_coding_validator,
    get_mendix_validator
)
from src.validation.mcp_sampling import get_mcp_sampling_validator, is_sampling_available


# ═══════════════════════════════════════════════════════════
# VALIDATION IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════

async def validate_messaging(draft: str, context: str, user_id: UUID) -> ValidationResult:
    """
    Complete messaging validation (deterministic + MCP sampling).

    Args:
        draft: Draft content
        context: Context description
        user_id: User UUID

    Returns:
        ValidationResult
    """
    issues = []

    # Stage 1: Deterministic checks
    messaging_validator = get_messaging_validator()
    deterministic_issues = await messaging_validator.validate(draft, user_id)
    issues.extend(deterministic_issues)

    # Stage 2: MCP sampling (if available)
    method = ValidationMethod.DETERMINISTIC_ONLY

    if await is_sampling_available():
        try:
            mcp_validator = get_mcp_sampling_validator()
            semantic_issues = await mcp_validator.validate_messaging(draft, context, user_id)
            issues.extend(semantic_issues)
            method = ValidationMethod.HYBRID
        except Exception:
            # Sampling failed, continue with deterministic only
            pass

    # Check if passed (no ERROR severity issues)
    passed = all(issue.severity != "error" for issue in issues)

    return ValidationResult(
        passed=passed,
        use_case=UseCase.MESSAGING,
        issues=issues,
        method=method
    )


async def validate_coding(draft: str, context: str, user_id: UUID) -> ValidationResult:
    """
    Complete coding validation (deterministic + MCP sampling with Ponytail awareness).

    Args:
        draft: Draft code
        context: Context description
        user_id: User UUID

    Returns:
        ValidationResult
    """
    issues = []

    # Stage 1: Deterministic checks
    coding_validator = get_coding_validator()
    deterministic_issues = await coding_validator.validate(draft, user_id)
    issues.extend(deterministic_issues)

    # Stage 2: MCP sampling (if available)
    # This is where Ponytail would be invoked (if installed)
    method = ValidationMethod.DETERMINISTIC_ONLY

    if await is_sampling_available():
        try:
            mcp_validator = get_mcp_sampling_validator()
            semantic_issues = await mcp_validator.validate_coding(draft, context, user_id)
            issues.extend(semantic_issues)
            method = ValidationMethod.HYBRID
        except Exception:
            pass

    # Check if passed
    passed = all(issue.severity != "error" for issue in issues)

    return ValidationResult(
        passed=passed,
        use_case=UseCase.CODING,
        issues=issues,
        method=method
    )


async def validate_mendix(draft: str, context: str, user_id: UUID) -> ValidationResult:
    """
    Complete Mendix validation (deterministic + MCP sampling).

    Args:
        draft: Draft Mendix content
        context: Context description
        user_id: User UUID

    Returns:
        ValidationResult
    """
    issues = []

    # Stage 1: Deterministic checks
    mendix_validator = get_mendix_validator()
    deterministic_issues = await mendix_validator.validate(draft, user_id)
    issues.extend(deterministic_issues)

    # Stage 2: MCP sampling (if available)
    method = ValidationMethod.DETERMINISTIC_ONLY

    if await is_sampling_available():
        try:
            mcp_validator = get_mcp_sampling_validator()
            semantic_issues = await mcp_validator.validate_mendix(draft, context, user_id)
            issues.extend(semantic_issues)
            method = ValidationMethod.HYBRID
        except Exception:
            pass

    # Check if passed
    passed = all(issue.severity != "error" for issue in issues)

    return ValidationResult(
        passed=passed,
        use_case=UseCase.MENDIX,
        issues=issues,
        method=method
    )
