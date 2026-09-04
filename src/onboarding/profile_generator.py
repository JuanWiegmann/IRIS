"""
Profile Generation from Onboarding Evidence

Converts collected onboarding answers into UserProfile with confidence scores.

Research: Wu 2024 shows profile-driven personalization improves quality.
"""

from typing import Dict

from src.onboarding.schema import OnboardingSession
from src.profile.schema import FormatPreference, Tone, UserProfile


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

    # Extract projects
    projects = _extract_projects(session)

    # Extract recent context
    recent_context = _extract_recent_context(session)

    # Calculate overall confidence
    overall_confidence = session.get_core_satisfaction_rate()

    # Build profile
    profile = UserProfile(
        language=language,
        tone=tone,
        format_preference=format_pref,
        boundaries=boundaries,
        current_projects=projects,
        recent_context=recent_context,
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


def _extract_tone(session: OnboardingSession) -> list[Tone]:
    """Extract tone preferences."""
    # Default: professional
    return [Tone.PROFESSIONAL]


def _extract_format_preference(session: OnboardingSession) -> FormatPreference:
    """Extract format preferences from technical_depth."""
    # Check technical_depth target
    if "technical_depth" in session.targets:
        target = session.targets["technical_depth"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option")

            if chosen == "high_level":
                return FormatPreference.CONCISE
            elif chosen == "detailed":
                return FormatPreference.DETAILED

    # Default: concise
    return FormatPreference.CONCISE


def _extract_boundaries(session: OnboardingSession) -> dict[str, str]:
    """Extract boundaries from onboarding targets."""
    boundaries = {}

    # Privacy boundary
    if "privacy" in session.targets:
        target = session.targets["privacy"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            chosen = answer.get("chosen_option", "preferences_only")

            if chosen == "no_storage":
                boundaries["privacy"] = "Do not store any personal or project information"
            elif chosen == "preferences_only":
                boundaries["privacy"] = "Store preferences only, no specific project details"

    # Proactivity boundary
    if "proactivity" in session.targets:
        target = session.targets["proactivity"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            answer_text = answer.get("answer", "")

            # User gave custom answer, use that
            if answer_text:
                boundaries["proactivity"] = answer_text
            else:
                chosen = answer.get("chosen_option", "proactive")
                if chosen == "reactive":
                    boundaries["proactivity"] = "Only answer what's asked, no unsolicited suggestions"

    # Error handling boundary
    if "error_handling_approach" in session.targets:
        target = session.targets["error_handling_approach"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            answer_text = answer.get("answer", "")
            if answer_text:
                boundaries["error_handling"] = answer_text

    return boundaries


def _extract_projects(session: OnboardingSession) -> list[str]:
    """Extract current projects from current_focus target."""
    projects = []

    if "current_focus" in session.targets:
        target = session.targets["current_focus"]
        if target.evidence:
            answer = target.evidence[-1]["data"]
            focus_text = answer.get("answer", "")
            if focus_text:
                # Simple extraction: split on common delimiters
                # User wrote: "Working on 2 projects: (1) X, (2) Y"
                projects.append(focus_text)

    return projects


def _extract_recent_context(session: OnboardingSession) -> str:
    """Extract recent context from role and ai_usage."""
    parts = []

    if session.role:
        parts.append(f"Role: {session.role}")

    if session.ai_usage:
        parts.append(f"AI Usage: {session.ai_usage}")

    return " | ".join(parts)


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
