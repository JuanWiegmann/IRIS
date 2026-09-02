"""
Validation Models
=================

Pydantic models for validation results.

Consistent structure across all validators (messaging, coding, Mendix).
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from src.validation.use_case_detector import UseCase


# ═══════════════════════════════════════════════════════════
# SEVERITY LEVELS
# ═══════════════════════════════════════════════════════════

class Severity(str, Enum):
    """Issue severity levels."""
    ERROR = "error"      # Blocks approval (must fix)
    WARNING = "warning"  # Should fix (not blocking)
    INFO = "info"        # Nice to know (optional)


# ═══════════════════════════════════════════════════════════
# VALIDATION ISSUE
# ═══════════════════════════════════════════════════════════

class ValidationIssue(BaseModel):
    """A single validation issue found in a draft."""

    severity: Severity
    category: str = Field(..., description="Issue category (e.g., 'tone', 'format', 'syntax')")
    message: str = Field(..., description="Human-readable issue description")
    rule: Optional[str] = Field(None, description="The profile rule or guideline violated")
    suggestion: Optional[str] = Field(None, description="Suggested fix")

    class Config:
        json_schema_extra = {
            "example": {
                "severity": "error",
                "category": "formality",
                "message": "Draft starts with 'Dear Sir/Madam' but user prefers casual tone",
                "rule": "Avoid 'Dear Sir/Madam', use 'Hi [Name]'",
                "suggestion": "Start with 'Hi [Name],' instead"
            }
        }


# ═══════════════════════════════════════════════════════════
# VALIDATION METHOD
# ═══════════════════════════════════════════════════════════

class ValidationMethod(str, Enum):
    """Validation method used."""
    DETERMINISTIC_ONLY = "deterministic_only"  # Pattern matching only
    MCP_SAMPLING = "mcp_sampling"              # MCP sampling used
    HYBRID = "hybrid"                          # Both methods combined


# ═══════════════════════════════════════════════════════════
# VALIDATION RESULT
# ═══════════════════════════════════════════════════════════

class ValidationResult(BaseModel):
    """Complete validation result for a draft."""

    passed: bool = Field(..., description="True if no blocking issues (no ERROR severity)")
    use_case: UseCase = Field(..., description="Detected use case")
    issues: list[ValidationIssue] = Field(default_factory=list, description="List of issues found")
    method: ValidationMethod = Field(..., description="Validation method used")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Validation confidence score")

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only ERROR severity issues."""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only WARNING severity issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def info(self) -> list[ValidationIssue]:
        """Get only INFO severity issues."""
        return [i for i in self.issues if i.severity == Severity.INFO]

    def format_for_llm(self) -> str:
        """
        Format validation result as markdown for LLM.

        Returns:
            Markdown-formatted validation feedback
        """
        if self.passed and not self.issues:
            return f"""✅ **Validation Passed**

**Use Case:** {self.use_case.value}
**Method:** {self.method.value}

No issues found. Draft is ready to show to user.
"""

        # Has issues
        status = "✅ Passed (suggestions)" if self.passed else "❌ Failed (blocking issues)"

        lines = [f"{status}\n"]
        lines.append(f"**Use Case:** {self.use_case.value}")
        lines.append(f"**Method:** {self.method.value}")
        lines.append("")

        # Group by severity
        if self.errors:
            lines.append("## ❌ Blocking Issues (must fix)")
            for issue in self.errors:
                lines.append(f"**{issue.category}:** {issue.message}")
                if issue.rule:
                    lines.append(f"  *Rule:* {issue.rule}")
                if issue.suggestion:
                    lines.append(f"  *Suggestion:* {issue.suggestion}")
                lines.append("")

        if self.warnings:
            lines.append("## ⚠️ Warnings (should fix)")
            for issue in self.warnings:
                lines.append(f"**{issue.category}:** {issue.message}")
                if issue.suggestion:
                    lines.append(f"  *Suggestion:* {issue.suggestion}")
                lines.append("")

        if self.info:
            lines.append("## 💡 Suggestions (optional)")
            for issue in self.info:
                lines.append(f"**{issue.category}:** {issue.message}")
                lines.append("")

        return "\n".join(lines)

    class Config:
        json_schema_extra = {
            "example": {
                "passed": False,
                "use_case": "messaging",
                "issues": [
                    {
                        "severity": "error",
                        "category": "tone",
                        "message": "Too formal for user's preference",
                        "rule": "User prefers casual tone",
                        "suggestion": "Use 'Hi' instead of 'Dear'"
                    }
                ],
                "method": "hybrid",
                "confidence": 0.85
            }
        }
