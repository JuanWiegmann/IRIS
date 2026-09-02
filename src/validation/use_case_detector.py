"""
Use Case Detection
==================

Detects what type of task the user is performing to route to appropriate validation.

Use Cases:
1. MESSAGING — emails, documents, simple text
2. CODING — Python, JavaScript, general programming
3. MENDIX — Mendix low-code development (domain XML, microflows)

Each use case has different validation needs:
- Messaging: tone, formality, boundaries
- Coding: syntax, semantic correctness, Ponytail plugin
- Mendix: Mendix-specific patterns + Ponytail for quality
"""

from enum import Enum
from typing import Optional
import re


# ═══════════════════════════════════════════════════════════
# USE CASE TYPES
# ═══════════════════════════════════════════════════════════

class UseCase(str, Enum):
    """User task use cases."""
    MESSAGING = "messaging"  # Emails, documents, simple text
    CODING = "coding"        # General programming (Python, JS, etc.)
    MENDIX = "mendix"        # Mendix low-code development
    UNKNOWN = "unknown"      # Fallback


# ═══════════════════════════════════════════════════════════
# DETECTION LOGIC
# ═══════════════════════════════════════════════════════════

class UseCaseDetector:
    """
    Detects use case from context and draft content.

    Uses heuristics:
    - Mendix: domain XML, microflow references, Mendix keywords
    - Coding: code blocks, programming keywords, file extensions
    - Messaging: natural language, formatting, common patterns
    """

    # Mendix indicators
    MENDIX_KEYWORDS = {
        "microflow", "nanoflow", "domain model", "entity",
        "mendix", "widget", "page", "snippet", "layout",
        ".mpk", "module", "association", "attribute"
    }

    MENDIX_XML_PATTERNS = [
        r'<entity\s+name=',
        r'<microflow\s+',
        r'<page\s+',
        r'xmlns.*mendix',
    ]

    # Coding indicators
    CODE_PATTERNS = [
        r'```\w+',              # Code blocks with language
        r'def\s+\w+\(',         # Python function
        r'function\s+\w+\(',    # JavaScript function
        r'class\s+\w+',         # Class definition
        r'import\s+',           # Import statement
        r'from\s+\w+\s+import', # Python import
        r'const\s+\w+\s*=',     # JavaScript const
        r'let\s+\w+\s*=',       # JavaScript let
        r'async\s+',            # Async functions
        r'\{[\s\n]*".*":\s*',   # JSON structure
    ]

    CODE_FILE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
        ".rs", ".cpp", ".c", ".cs", ".rb", ".php", ".sql"
    }

    def detect(self, query: str, draft: str) -> UseCase:
        """
        Detect use case from query and draft.

        Args:
            query: Original user query/request
            draft: Generated draft to validate

        Returns:
            Detected UseCase enum
        """
        combined = f"{query}\n{draft}".lower()

        # Check Mendix first (most specific)
        if self._is_mendix(combined, draft):
            return UseCase.MENDIX

        # Check coding
        if self._is_coding(combined, draft):
            return UseCase.CODING

        # Default to messaging
        return UseCase.MESSAGING

    def _is_mendix(self, text: str, draft: str) -> bool:
        """Check if content is Mendix-related."""
        # Keyword check
        keyword_count = sum(1 for kw in self.MENDIX_KEYWORDS if kw in text)
        if keyword_count >= 2:
            return True

        # XML pattern check
        for pattern in self.MENDIX_XML_PATTERNS:
            if re.search(pattern, draft, re.IGNORECASE):
                return True

        return False

    def _is_coding(self, text: str, draft: str) -> bool:
        """Check if content is code-related."""
        # Code pattern check
        code_pattern_count = sum(
            1 for pattern in self.CODE_PATTERNS
            if re.search(pattern, draft)
        )

        if code_pattern_count >= 2:
            return True

        # File extension check
        has_code_file = any(ext in text for ext in self.CODE_FILE_EXTENSIONS)
        if has_code_file:
            return True

        # Check for code block markers
        if "```" in draft and draft.count("```") >= 2:
            return True

        return False


# ═══════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════

_detector: Optional[UseCaseDetector] = None


def get_use_case_detector() -> UseCaseDetector:
    """Get singleton detector instance."""
    global _detector
    if _detector is None:
        _detector = UseCaseDetector()
    return _detector


def detect_use_case(query: str, draft: str) -> UseCase:
    """
    Convenience function for use case detection.

    Args:
        query: Original user query
        draft: Generated draft

    Returns:
        Detected UseCase

    Example:
        use_case = detect_use_case(
            query="Write a Python function to sort users",
            draft="def sort_users(users):\n    return sorted(users)"
        )
        # Returns: UseCase.CODING
    """
    detector = get_use_case_detector()
    return detector.detect(query, draft)
