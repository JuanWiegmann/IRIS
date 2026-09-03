"""
Generate UserProfile from completed OnboardingSession

Transforms collected evidence into structured UserProfile.
"""

from uuid import UUID, uuid5, NAMESPACE_DNS

from src.onboarding.schema import OnboardingSession
from src.profile.schema import UserProfile, Tone, FormatPreference


def generate_profile_from_session(session: OnboardingSession) -> UserProfile:
    """
    Transform OnboardingSession evidence → UserProfile.

    Args:
        session: Completed onboarding session

    Returns:
        UserProfile with inferred preferences
    """
    # Generate deterministic UUID from user_id
    user_uuid = uuid5(NAMESPACE_DNS, f"iris.user.{session.user_id}")

    # Extract evidence
    language = _extract_language(session)
    tone = _extract_tone(session)
    format_pref = _extract_format_preference(session)
    boundaries = _extract_boundaries(session)
    projects = _extract_projects(session)

    # Calculate overall confidence
    confidence = session.get_core_satisfaction_rate()

    return UserProfile(
        id=user_uuid,
        language=language,
        tone=tone,
        format_preference=format_pref,
        boundaries=boundaries,
        confidence=confidence,
        current_projects=projects,
        recent_context=f"Profile type: {session.profile_type.value if session.profile_type else 'general'}"
    )


def _extract_language(session: OnboardingSession) -> str:
    """Extract language preference."""
    if "language" not in session.targets:
        return "en-US"

    target = session.targets["language"]
    if not target.evidence:
        return "en-US"

    chosen = target.evidence[0]["data"].get("chosen_option", "en")

    # Map to BCP 47
    mapping = {
        "de": "de-DE",
        "en": "en-US",
        "both": "en-US"  # Default to English, user will code-switch
    }

    return mapping.get(chosen, "en-US")


def _extract_tone(session: OnboardingSession) -> list[Tone]:
    """Extract tone preferences."""
    tones = [Tone.PROFESSIONAL]  # Default

    # Role influences tone
    if session.role and "engineer" in session.role.lower():
        tones = [Tone.TECHNICAL, Tone.PROFESSIONAL]

    return tones


def _extract_format_preference(session: OnboardingSession) -> FormatPreference:
    """Extract format preference from technical_depth target."""
    if "technical_depth" not in session.targets:
        return FormatPreference.CONCISE

    target = session.targets["technical_depth"]
    if not target.evidence:
        return FormatPreference.CONCISE

    evidence = target.evidence[0]["data"]
    chosen = evidence.get("chosen_option")
    custom_note = evidence.get("answer", "")

    # User specified custom structure: Problem → Solution → Where/How
    if "Problem" in custom_note and "Solution" in custom_note:
        return FormatPreference.STEP_BY_STEP

    # Map choices
    if chosen == "high_level":
        return FormatPreference.CONCISE
    elif chosen == "detailed":
        return FormatPreference.DETAILED

    return FormatPreference.CONCISE


def _extract_boundaries(session: OnboardingSession) -> dict[str, str]:
    """Extract boundaries from various targets."""
    boundaries = {}

    # Code documentation style
    if "code_documentation_style" in session.targets:
        target = session.targets["code_documentation_style"]
        if target.evidence:
            chosen = target.evidence[0]["data"].get("chosen_option")
            if chosen == "minimal":
                boundaries["code_style"] = "Self-documenting code preferred, minimal comments"

    # Technical depth custom instructions
    if "technical_depth" in session.targets:
        target = session.targets["technical_depth"]
        if target.evidence and "answer" in target.evidence[0]["data"]:
            custom = target.evidence[0]["data"]["answer"]
            if "Problem" in custom:
                boundaries["response_structure"] = "Follow structure: Problem → Solution → Where/How. No code examples unless needed. No time estimates."

    # Proactivity
    if "proactivity" in session.targets:
        target = session.targets["proactivity"]
        if target.evidence:
            answer = target.evidence[0]["data"].get("answer", "")
            if "conditional" in answer.lower() or "list" in answer.lower():
                boundaries["proactivity"] = "Flag logic-breaking issues proactively. List other issues for reference without auto-fixing (they may affect other parts)."

    # Error handling
    if "error_handling_approach" in session.targets:
        target = session.targets["error_handling_approach"]
        if target.evidence:
            answer = target.evidence[0]["data"].get("answer", "")
            if "logic chain" in answer.lower():
                boundaries["debugging"] = "Debug flow: 1) Trace logic chain, 2) Identify probable logic bug in leadup, 3) Check 'Potential issue Folder', 4) Research independently if needed."

    # Learning approach
    if "learning_approach" in session.targets:
        target = session.targets["learning_approach"]
        if target.evidence:
            answer = target.evidence[0]["data"].get("answer", "")
            if "adaptive" in answer.lower() or "familiar" in answer.lower():
                boundaries["explanation_style"] = "If user knows topic → just implementation. If new topic → short summary first, then implementation."

    # Privacy
    if "privacy" in session.targets:
        target = session.targets["privacy"]
        if target.evidence:
            chosen = target.evidence[0]["data"].get("chosen_option")
            if chosen == "store_all":
                boundaries["storage"] = "May store technical context (projects, tech stack) for future conversations"

    return boundaries


def _extract_projects(session: OnboardingSession) -> list[str]:
    """Extract current projects from current_focus target."""
    if "current_focus" not in session.targets:
        return []

    target = session.targets["current_focus"]
    if not target.evidence:
        return []

    answer = target.evidence[0]["data"].get("answer", "")

    # Simple extraction: look for project names
    projects = []
    if "Plantafel" in answer:
        projects.append("Plantafel visualizer (Werk Emden) - production + bug fixing")
    if "Ringline" in answer:
        projects.append("Ringline - car color room documentation")

    return projects
