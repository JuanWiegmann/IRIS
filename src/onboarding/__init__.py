"""
GATE Onboarding System

Adaptive preference elicitation using the GATE framework.
Research: Li, Tamkin, Goodman, Andreas (ICLR 2025)
"""

from src.onboarding.adaptive import (
    detect_profile_type,
    get_information_pool_after_answer,
    get_information_pool_before_question,
    initialize_session,
    select_questions_for_profile,
)
from src.onboarding.store import get_onboarding_store
from src.onboarding.schema import (
    OnboardingSession,
    ProfileType,
)
from src.onboarding.targets import get_all_targets

__all__ = [
    # Adaptive logic
    "detect_profile_type",
    "get_information_pool_after_answer",
    "get_information_pool_before_question",
    "get_onboarding_store",
    "initialize_session",
    "select_questions_for_profile",
    # Schema
    "OnboardingSession",
    "ProfileType",
    # Targets
    "get_all_targets",
]
