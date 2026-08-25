"""
User Profile Schema
===================

Pydantic models for user profiles.

Research basis:
- Wu et al. (2024): User outputs drive personalization (not inputs)
- GATE (Li et al., ICLR 2025): Target-based preference elicitation
- Westhaeusser et al. (2025): Dynamic profiles with confidence scores

The profile captures:
1. Communication preferences (tone, format, language)
2. Boundaries (topics to avoid, constraints)
3. Metadata (confidence, timestamps)
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════

class Tone(str, Enum):
    """
    User's preferred communication tone.

    Based on GATE research - these are dimensions users can reliably
    distinguish via forced choices (A vs B comparisons).
    """
    FORMAL = "formal"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    APPROACHABLE = "approachable"


class FormatPreference(str, Enum):
    """
    User's preferred response format.

    Based on Wu et al. (2024) - format is a primary personalization driver.
    """
    CONCISE = "concise"  # Short, to the point
    DETAILED = "detailed"  # Comprehensive explanations
    EXAMPLES_HEAVY = "examples_heavy"  # Learn by example
    STEP_BY_STEP = "step_by_step"  # Procedural breakdown
    BULLET_POINTS = "bullet_points"  # Structured lists


# ═══════════════════════════════════════════════════════════
# USER PROFILE
# ═══════════════════════════════════════════════════════════

class UserProfile(BaseModel):
    """
    Complete user profile for personalization.

    This is the primary data structure for KIM. It captures everything
    the LLM needs to know about how to communicate with this user.

    Confidence scores (0.0-1.0) track how much evidence supports each field.
    Low confidence = tentative/few interactions, High confidence = well-established.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)

    # Communication Preferences
    language: str = Field(
        default="en-US",
        description="Primary language (BCP 47 format: en-US, de-DE, etc.)"
    )

    tone: list[Tone] = Field(
        default_factory=lambda: [Tone.PROFESSIONAL],
        description="Preferred tone(s). Can have multiple (e.g., professional + approachable)"
    )

    format_preference: FormatPreference = Field(
        default=FormatPreference.CONCISE,
        description="How the user prefers to receive information"
    )

    # Boundaries
    boundaries: dict[str, str] = Field(
        default_factory=dict,
        description="Topics to avoid, constraints, special instructions. Key = category, Value = rule"
    )

    # Metadata
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall profile confidence (0.0 = new user, 1.0 = well-established)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Context
    current_projects: list[str] = Field(
        default_factory=list,
        description="Ongoing projects/topics (light memory, cross-session)"
    )

    recent_context: str = Field(
        default="",
        description="Brief summary of recent work (last session or two)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "language": "de-DE",
                "tone": ["professional", "approachable"],
                "format_preference": "bullet_points",
                "boundaries": {
                    "formality": "Avoid overly formal language",
                    "technical": "User has deep technical background"
                },
                "confidence": 0.75,
                "current_projects": ["KIM", "Claude Certified Architect"],
                "recent_context": "Working on MCP server implementation"
            }
        }


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def create_default_profile() -> UserProfile:
    """
    Create a default profile for new users.

    Returns a profile with sensible defaults. The onboarding process
    (Segment 5) will refine these based on GATE methodology.
    """
    return UserProfile(
        language="en-US",
        tone=[Tone.PROFESSIONAL],
        format_preference=FormatPreference.CONCISE,
        confidence=0.1  # Low confidence = needs onboarding
    )


def format_profile_for_llm(profile: UserProfile) -> str:
    """
    Format a profile as markdown for LLM consumption.

    This is what get_context() will return. Markdown is easier for LLMs
    to parse than raw JSON.

    Args:
        profile: The user profile to format

    Returns:
        Markdown-formatted profile description
    """
    tone_str = ", ".join([t.value for t in profile.tone])

    boundaries_str = "\n".join([
        f"  - **{key}:** {value}"
        for key, value in profile.boundaries.items()
    ]) if profile.boundaries else "  - None specified"

    projects_str = "\n".join([
        f"  - {project}"
        for project in profile.current_projects
    ]) if profile.current_projects else "  - None active"

    return f"""## User Profile
- **Language:** {profile.language}
- **Tone:** {tone_str}
- **Format Preference:** {profile.format_preference.value}
- **Profile Confidence:** {profile.confidence:.0%}

### Boundaries
{boundaries_str}

### Current Projects
{projects_str}

### Recent Context
{profile.recent_context or "No recent context"}

---
*Profile ID: {profile.id}*
*Last Updated: {profile.updated_at.strftime('%Y-%m-%d %H:%M UTC')}*
"""
