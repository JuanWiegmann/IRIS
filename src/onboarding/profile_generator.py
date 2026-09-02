"""
Profile Generation from Onboarding Evidence

Converts collected onboarding answers into UserProfile with confidence scores.

Research: Wu 2024 shows profile-driven personalization improves quality.
"""

from typing import Dict, List, Optional

from src.onboarding.schema import OnboardingSession
from src.profile.schema import (
    FormatPreference,
    ResponseBoundary,
    TonePreference,
    UserProfile,
)


def generate_profile_from_onboarding(session: OnboardingSession) -> UserProfile:
    """
    Generate UserProfile from completed onboarding session.

    Maps collected evidence to profile fields with confidence scores.

    Args:
        session: Completed OnboardingSession

    Returns:
        UserProfile with preferences and confidence scores
    """
    # Extract language
    language = _extract_language(session)

    # Extract tone preferences
    tone = _extract_tone(session)

    # Extract format preferences
    format_pref = _extract_format_preference(session)

    # Extract boundaries
    boundaries = _extract_boundaries(session)

    # Calculate overall confidence
    overall_confidence = session.get_core_satisfaction_rate()

    # Build profile
    profile = UserProfile(
        user_id=session.user_id,
        language=language,
        tone=tone,
        format_preference=format_pref,
        boundaries=boundaries,
        confidence=overall_confidence,
    )

    return profile


def _extract_language(session: OnboardingSession) -> str:
    """Extract language preference."""
    if "language" not in session.targets:
        return "en"  # Default

    target = session.targets["language"]
    if not target.evidence:
        return "en"

    # Get chosen option
    answer = target.evidence[-1]["data"]
    chosen = answer.get("chosen_option", "en")

    return chosen


def _extract_tone(session: OnboardingSession) -> TonePreference:
    """Extract tone preferences from communication_formality target."""
    # Default: professional but not formal
    tone = TonePreference.PROFESSIONAL

    # Check communication_formality target
    if "communication_formality" in session.targets:
        target = session.targets["communication_formality"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option", "contextual")

            if chosen == "direct":
                tone = TonePreference.DIRECT
            elif chosen == "contextual":
                tone = TonePreference.PROFESSIONAL
            elif chosen == "adaptive":
                tone = TonePreference.PROFESSIONAL  # Middle ground

    return tone


def _extract_format_preference(session: OnboardingSession) -> FormatPreference:
    """Extract format preferences from technical_depth and other targets."""
    # Default: balanced
    detail_level = "balanced"
    include_examples = True
    structure = "mixed"

    # Technical depth
    if "technical_depth" in session.targets:
        target = session.targets["technical_depth"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option")

            if chosen == "high_level":
                detail_level = "concise"
                structure = "bullets"
            elif chosen == "detailed":
                detail_level = "comprehensive"
                structure = "structured"
                include_examples = True
            elif chosen == "adaptive":
                detail_level = "balanced"

    # Code documentation style
    if "code_documentation_style" in session.targets:
        target = session.targets["code_documentation_style"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option")

            if chosen == "minimal":
                # User prefers clean code, minimal comments
                pass  # Already reflected in detail_level
            elif chosen == "documented":
                include_examples = True

    # Learning approach
    example_first = False
    if "learning_approach" in session.targets:
        target = session.targets["learning_approach"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option")
            example_first = chosen == "example_first"

    return FormatPreference(
        detail_level=detail_level,
        include_examples=include_examples,
        structure=structure,
        example_first=example_first,
    )


def _extract_boundaries(session: OnboardingSession) -> List[ResponseBoundary]:
    """Extract boundaries from privacy and proactivity targets."""
    boundaries = []

    # Privacy boundary
    if "privacy" in session.targets:
        target = session.targets["privacy"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option", "preferences_only")

            if chosen == "no_storage":
                boundaries.append(
                    ResponseBoundary(
                        type="privacy",
                        description="Do not store any personal or project information",
                    )
                )
            elif chosen == "preferences_only":
                boundaries.append(
                    ResponseBoundary(
                        type="privacy",
                        description="Store preferences only, no specific project details",
                    )
                )

    # Proactivity boundary
    if "proactivity" in session.targets:
        target = session.targets["proactivity"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option", "proactive")

            if chosen == "reactive":
                boundaries.append(
                    ResponseBoundary(
                        type="proactivity",
                        description="Only answer what's asked, no unsolicited suggestions",
                    )
                )

    return boundaries


def get_profile_context_from_session(session: OnboardingSession) -> Dict[str, str]:
    """
    Extract contextual information for immediate use (before profile generation).

    Returns key context that can be used right away in get_context() calls.

    Args:
        session: OnboardingSession (active or completed)

    Returns:
        Dict with current context: role, ai_usage, focus, etc.
    """
    context = {}

    # Role and AI usage (anchor questions)
    if session.role:
        context["role"] = session.role
    if session.ai_usage:
        context["ai_usage"] = session.ai_usage

    # Current focus
    if "current_focus" in session.targets:
        target = session.targets["current_focus"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            context["current_focus"] = answer.get("answer", "")

    # Profile type
    if session.profile_type:
        context["profile_type"] = session.profile_type.value

    return context
