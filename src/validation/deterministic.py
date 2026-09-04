"""
Deterministic Validators
========================

Rule-based validation without LLM calls.

Fast, free, deterministic checks based on:
- User profile (tone, format, boundaries)
- Pattern matching (regex)
- Heuristics (word count, structure detection)
"""

import re
from uuid import UUID
from typing import Optional

from src.profile import get_or_create_profile, UserProfile, Tone, FormatPreference
from src.validation.models import ValidationIssue, Severity


# ═══════════════════════════════════════════════════════════
# MESSAGING VALIDATOR
# ═══════════════════════════════════════════════════════════

class MessagingValidator:
    """
    Deterministic validation for messaging (emails, documents).

    Checks:
    - Tone appropriateness (formal vs casual markers)
    - Format preferences (bullets vs paragraphs)
    - Boundary violations (jargon blacklist)
    - Length constraints
    """

    # Formality markers
    FORMAL_OPENINGS = [
        "dear sir", "dear madam", "to whom it may concern",
        "dear sir or madam", "dear mr", "dear ms", "dear dr"
    ]

    CASUAL_OPENINGS = [
        "hi", "hey", "hello", "hi there", "hey there"
    ]

    # Jargon keywords (common corporate jargon)
    COMMON_JARGON = [
        "synergize", "leverage", "paradigm", "circle back",
        "touch base", "move the needle", "low-hanging fruit",
        "think outside the box", "game changer", "disrupt"
    ]

    async def validate(self, draft: str, user_id: UUID) -> list[ValidationIssue]:
        """
        Validate messaging content.

        Args:
            draft: Draft content
            user_id: User UUID

        Returns:
            List of validation issues
        """
        issues = []

        # Load profile
        profile = await get_or_create_profile(user_id)

        # Block if no profile exists (onboarding required)
        if profile is None:
            return [ValidationIssue(
                severity="error",
                category="profile",
                message="ONBOARDING_REQUIRED: No profile found. Complete onboarding before using validation.",
                suggestion="Call start_onboarding() to create your profile."
            )]

        # Check tone
        issues.extend(self._check_tone(draft, profile))

        # Check format
        issues.extend(self._check_format(draft, profile))

        # Check boundaries (jargon)
        issues.extend(self._check_boundaries(draft, profile))

        # Check length
        issues.extend(self._check_length(draft, profile))

        return issues

    def _check_tone(self, draft: str, profile: UserProfile) -> list[ValidationIssue]:
        """Check if tone matches profile."""
        issues = []
        draft_lower = draft.lower()

        # Check for formal openings when user prefers casual
        has_casual_tone = Tone.CASUAL in profile.tone or Tone.FRIENDLY in profile.tone

        if has_casual_tone:
            for formal_opening in self.FORMAL_OPENINGS:
                if formal_opening in draft_lower:
                    issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        category="tone",
                        message=f"Too formal: starts with '{formal_opening}'",
                        rule=f"User prefers {', '.join([t.value for t in profile.tone])} tone",
                        suggestion=f"Use casual opening like 'Hi [Name]' instead"
                    ))
                    break

        # Check for overly casual when user prefers formal
        has_formal_tone = Tone.FORMAL in profile.tone or Tone.PROFESSIONAL in profile.tone

        if has_formal_tone and not has_casual_tone:
            for casual_opening in self.CASUAL_OPENINGS:
                if draft_lower.startswith(casual_opening):
                    issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="tone",
                        message=f"May be too casual: starts with '{casual_opening}'",
                        rule=f"User prefers {', '.join([t.value for t in profile.tone])} tone",
                        suggestion="Consider more formal greeting"
                    ))
                    break

        return issues

    def _check_format(self, draft: str, profile: UserProfile) -> list[ValidationIssue]:
        """Check if format matches profile preferences."""
        issues = []

        # Detect bullets
        has_bullets = bool(re.search(r'^[\s]*[•\-\*\d+\.]\s', draft, re.MULTILINE))

        # Detect long paragraphs
        paragraphs = [p.strip() for p in draft.split('\n\n') if p.strip()]
        long_paragraphs = [p for p in paragraphs if len(p) > 300]

        # Check format preference
        if profile.format_preference == FormatPreference.BULLET_POINTS:
            if not has_bullets and long_paragraphs:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="format",
                    message="User prefers bullet points but draft uses long paragraphs",
                    rule="format_preference: bullet_points",
                    suggestion="Convert key points to bullet list"
                ))

        elif profile.format_preference == FormatPreference.CONCISE:
            word_count = len(draft.split())
            if word_count > 200:
                issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category="length",
                    message=f"Draft is {word_count} words (user prefers concise <200)",
                    rule="format_preference: concise"
                ))

        return issues

    def _check_boundaries(self, draft: str, profile: UserProfile) -> list[ValidationIssue]:
        """Check for boundary violations (jargon, forbidden topics)."""
        issues = []
        draft_lower = draft.lower()

        # Check profile-specific boundaries
        if "jargon" in profile.boundaries:
            jargon_rule = profile.boundaries["jargon"]

            # Extract blacklist from rule (simple heuristic)
            # Example: "Avoid: synergize, leverage, paradigm"
            if "avoid:" in jargon_rule.lower():
                blacklist_text = jargon_rule.lower().split("avoid:")[1]
                blacklist = [w.strip() for w in blacklist_text.split(",")]
            else:
                blacklist = self.COMMON_JARGON

            # Check for jargon
            found_jargon = [w for w in blacklist if w in draft_lower]

            if found_jargon:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="jargon",
                    message=f"Contains jargon: {', '.join(found_jargon)}",
                    rule=jargon_rule,
                    suggestion="Use simpler language"
                ))

        return issues

    def _check_length(self, draft: str, profile: UserProfile) -> list[ValidationIssue]:
        """Check if length is appropriate."""
        issues = []
        word_count = len(draft.split())

        # Very short (< 10 words) might be incomplete
        if word_count < 10:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="length",
                message=f"Very short ({word_count} words) - may be incomplete"
            ))

        return issues


# ═══════════════════════════════════════════════════════════
# CODING VALIDATOR
# ═══════════════════════════════════════════════════════════

class CodingValidator:
    """
    Deterministic validation for code.

    Checks:
    - Common anti-patterns
    - Security issues (basic)
    - Best practice violations
    """

    async def validate(self, draft: str, user_id: UUID) -> list[ValidationIssue]:
        """
        Validate code content.

        Args:
            draft: Draft code
            user_id: User UUID

        Returns:
            List of validation issues
        """
        issues = []

        # Check for TODO/FIXME
        if "TODO" in draft or "FIXME" in draft:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category="completeness",
                message="Contains TODO/FIXME markers",
                suggestion="Address before committing"
            ))

        # Check for print statements (should use logging)
        if re.search(r'\bprint\s*\(', draft) and "logging" not in draft.lower():
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="best_practice",
                message="Uses print() instead of logging",
                suggestion="Consider using logging module for production code"
            ))

        # Check for bare except
        if re.search(r'except\s*:', draft):
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="error_handling",
                message="Bare 'except:' clause catches all exceptions",
                suggestion="Specify exception types (e.g., 'except ValueError:')"
            ))

        # Check for hardcoded credentials (basic)
        if re.search(r'(password|api_key|secret)\s*=\s*["\'][\w\d]+["\']', draft, re.IGNORECASE):
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="security",
                message="Possible hardcoded credentials",
                suggestion="Use environment variables or config files"
            ))

        # Check for SQL injection risk (basic)
        if re.search(r'(execute|query).*%s|f".*SELECT', draft):
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="security",
                message="Possible SQL injection risk",
                suggestion="Use parameterized queries"
            ))

        return issues


# ═══════════════════════════════════════════════════════════
# MENDIX VALIDATOR
# ═══════════════════════════════════════════════════════════

class MendixValidator:
    """
    Deterministic validation for Mendix content.

    Checks:
    - Entity naming conventions
    - XML structure basics
    - Common Mendix patterns
    """

    async def validate(self, draft: str, user_id: UUID) -> list[ValidationIssue]:
        """
        Validate Mendix content.

        Args:
            draft: Draft Mendix content
            user_id: User UUID

        Returns:
            List of validation issues
        """
        issues = []

        # Check for empty entity names
        if re.search(r'<entity\s+name=""', draft):
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="mendix_syntax",
                message="Entity has empty name attribute"
            ))

        # Check for plural entity names (anti-pattern)
        entity_names = re.findall(r'<entity\s+name="(\w+)"', draft)
        plurals = [name for name in entity_names if name.endswith('s') and len(name) > 3]

        if plurals:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="mendix_convention",
                message=f"Entity names should be singular: {', '.join(plurals)}",
                rule="Mendix best practice: use singular nouns for entities",
                suggestion=f"Rename to: {', '.join([p[:-1] for p in plurals])}"
            ))

        # Check for microflow without proper definition
        if "microflow" in draft.lower() and not any(x in draft for x in ["<microflow", "microflow name"]):
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category="mendix_structure",
                message="Microflow mentioned but not properly defined",
                suggestion="Define microflow with proper XML structure"
            ))

        return issues


# ═══════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════

def get_messaging_validator() -> MessagingValidator:
    """Get messaging validator instance."""
    return MessagingValidator()


def get_coding_validator() -> CodingValidator:
    """Get coding validator instance."""
    return CodingValidator()


def get_mendix_validator() -> MendixValidator:
    """Get Mendix validator instance."""
    return MendixValidator()
