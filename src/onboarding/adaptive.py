"""
Adaptive Question Selection Logic

Based on Q1 (role) and Q2 (AI usage), select the most relevant questions.
Research: Westhaeusser 2025 shows 5-7 strategic questions capture essentials.
"""

import re
from typing import List

from src.onboarding.schema import OnboardingSession, OnboardingTarget, ProfileType
from src.onboarding.targets import get_all_targets


def detect_profile_type(role: str, ai_usage: str) -> ProfileType:
    """
    Analyze role + AI usage to determine profile type.

    Args:
        role: User's professional role (Q1 answer)
        ai_usage: How they use AI (Q2 answer)

    Returns:
        ProfileType enum (code_heavy, communication_heavy, architecture, general)
    """
    # Handle None values (shouldn't happen, but be defensive)
    role_lower = (role or "").lower()
    usage_lower = (ai_usage or "").lower()

    # Code-heavy indicators
    code_keywords = [
        "develop", "code", "coding", "debug", "implement", "build",
        "programming", "software engineer", "backend", "frontend",
        "full-stack", "devops", "review"
    ]

    # Communication-heavy indicators
    comm_keywords = [
        "lead", "manager", "document", "documentation", "explain",
        "write", "email", "communication", "stakeholder", "team lead",
        "teaching", "training"
    ]

    # Architecture indicators
    arch_keywords = [
        "architect", "architecture", "design", "decision", "pattern",
        "system design", "solution architect", "technical lead",
        "strategy", "evaluate"
    ]

    # Count matches
    code_score = sum(1 for kw in code_keywords if kw in role_lower or kw in usage_lower)
    comm_score = sum(1 for kw in comm_keywords if kw in role_lower or kw in usage_lower)
    arch_score = sum(1 for kw in arch_keywords if kw in role_lower or kw in usage_lower)

    # Determine profile type (highest score wins)
    scores = [
        (code_score, ProfileType.CODE_HEAVY),
        (comm_score, ProfileType.COMMUNICATION_HEAVY),
        (arch_score, ProfileType.ARCHITECTURE),
    ]
    scores.sort(key=lambda x: x[0], reverse=True)

    # If no clear winner or all zeros, return general
    if scores[0][0] == 0:
        return ProfileType.GENERAL

    return scores[0][1]


def select_questions_for_profile(
    profile_type: ProfileType,
    all_targets: dict[str, OnboardingTarget],
) -> List[str]:
    """
    Select target IDs to ask about, given profile type.

    Returns target IDs in priority order (anchor questions first, then contextual, then universal).

    Research: 10 questions max (5 min), 80% effectiveness (Westhaeusser 2025)
    """
    selected = []

    # Phase 1: Anchor questions (already asked, but included for completeness)
    selected.extend(["role", "ai_usage"])

    # Phase 2: Profile-specific questions (based on detected type)
    profile_specific = {
        ProfileType.CODE_HEAVY: [
            "technical_depth",           # Priority 2 (core)
            "code_documentation_style",  # Priority 3 (core)
            "error_handling_approach",   # Priority 5 (nice to have)
        ],
        ProfileType.COMMUNICATION_HEAVY: [
            "communication_formality",  # Priority 2 (core)
            "explanation_depth",        # Priority 3 (core)
            "documentation_style",      # Priority 5 (nice to have)
        ],
        ProfileType.ARCHITECTURE: [
            "decision_support_style",  # Priority 2 (core)
            "technical_breadth",       # Priority 3 (core)
        ],
        ProfileType.GENERAL: [
            # No specific questions, just universal ones
        ],
    }

    selected.extend(profile_specific.get(profile_type, []))

    # Phase 3: Universal questions (asked to everyone)
    universal = [
        "language",          # Priority 1 (must)
        "current_focus",     # Priority 2 (core)
        "learning_approach", # Priority 4 (nice to have)
        "proactivity",       # Priority 4 (nice to have)
        "privacy",           # Priority 1 (must, legal)
    ]
    selected.extend(universal)

    # Ensure no duplicates and all exist in targets
    selected = list(dict.fromkeys(selected))  # Preserve order, remove dupes
    selected = [tid for tid in selected if tid in all_targets]

    # Limit to 10 questions max (research-backed)
    return selected[:10]


def initialize_session(
    user_id: str,
    session_id: str,
    role: str,
    ai_usage: str,
) -> OnboardingSession:
    """
    Initialize onboarding session after Q1 + Q2 answered.

    Args:
        user_id: User identifier
        session_id: Session identifier
        role: User's role (Q1 answer)
        ai_usage: How they use AI (Q2 answer)

    Returns:
        OnboardingSession with targets loaded and questions selected
    """
    # Detect profile type
    profile_type = detect_profile_type(role, ai_usage)

    # Get all possible targets
    all_targets = get_all_targets()

    # Select relevant questions
    selected_target_ids = select_questions_for_profile(profile_type, all_targets)

    # Create session
    session = OnboardingSession(
        user_id=user_id,
        session_id=session_id,
        role=role,
        ai_usage=ai_usage,
        profile_type=profile_type,
    )

    # Add selected targets to session
    for target_id in selected_target_ids:
        if target_id in all_targets:
            session.targets[target_id] = all_targets[target_id].model_copy(deep=True)

    # Set questions_remaining (skip anchor questions, they're already answered)
    session.questions_remaining = [
        tid for tid in selected_target_ids
        if tid not in ["role", "ai_usage"]
    ]

    # Mark anchor questions as satisfied
    if "role" in session.targets:
        session.targets["role"].add_evidence({"answer": role}, confidence_delta=1.0)
    if "ai_usage" in session.targets:
        session.targets["ai_usage"].add_evidence({"answer": ai_usage}, confidence_delta=1.0)

    session.questions_asked = 2  # Q1 + Q2 done

    return session


def get_information_pool_before_question(
    session: OnboardingSession,
) -> dict:
    """
    Generate information pool to provide to LLM before asking next question.

    Research: Transparent progress + research-backed guidance (GATE methodology).
    """
    next_target = session.get_next_target()

    if not next_target:
        return {
            "session_progress": {
                "questions_asked": session.questions_asked,
                "core_satisfaction_rate": session.get_core_satisfaction_rate(),
                "satisfied_dimensions": session.get_satisfied_dimensions(),
                "can_complete": session.can_complete(),
            },
            "should_continue": False,
            "completion_reason": "All priority questions answered",
        }

    # Build guidance
    return {
        "session_progress": {
            "questions_asked": session.questions_asked,
            "questions_remaining": len(session.questions_remaining),
            "core_satisfaction_rate": session.get_core_satisfaction_rate(),
            "satisfied_dimensions": session.get_satisfied_dimensions(),
            "profile_type": session.profile_type.value if session.profile_type else "unknown",
        },
        "next_target": {
            "id": next_target.id,
            "dimension": next_target.dimension,
            "research_basis": next_target.research_basis,
            "priority": next_target.priority,
            "question_template": next_target.question_template.model_dump(),
        },
        "recommended_strategy": _get_strategy_guidance(next_target),
        "should_continue": True,
    }


def get_information_pool_after_answer(
    session: OnboardingSession,
    target_id: str,
) -> dict:
    """
    Generate information pool to provide to LLM after user answers.

    Shows validation result and next steps.
    """
    if target_id not in session.targets:
        return {
            "error": f"Unknown target: {target_id}",
            "should_continue": True,
        }

    target = session.targets[target_id]

    # Check if barrier met
    barrier_met = target.satisfied

    # Infer preferences from evidence
    inferred = _infer_preferences(target)

    # Determine if should continue
    should_continue = (
        len(session.questions_remaining) > 0
        and not session.can_complete()
        and session.questions_asked < 10
    )

    return {
        "validation_result": {
            "dimension": target.dimension,
            "barrier_met": barrier_met,
            "confidence": target.confidence,
            "evidence_count": len(target.evidence),
            "inferred_preferences": inferred,
        },
        "should_continue": should_continue,
        "next_recommendation": (
            "Continue with next question"
            if should_continue
            else "Core profile complete, can finish"
        ),
        "session_progress": {
            "questions_asked": session.questions_asked,
            "questions_remaining": len(session.questions_remaining),
            "core_satisfaction_rate": session.get_core_satisfaction_rate(),
        },
    }


def _get_strategy_guidance(target: OnboardingTarget) -> str:
    """Generate research-backed guidance for asking this question."""
    if target.question_template.question_type == QuestionType.EDGE_CASE:
        return (
            f"GATE research: Edge-case questions outperform open questions in 60% of settings. "
            f"Show concrete examples and force choice between them. "
            f"This reveals tacit preferences users can't articulate. "
            f"Expected time: 30-40 seconds."
        )
    elif target.question_template.question_type == QuestionType.BINARY:
        return (
            f"GATE research: Binary questions have equal/lower cognitive load than open questions. "
            f"Clear yes/no or A/B choice. "
            f"Expected time: 15-20 seconds."
        )
    elif target.question_template.question_type == QuestionType.OPEN:
        return (
            f"Open question for factual information. "
            f"Provide examples to reduce ambiguity. "
            f"Expected time: 30-40 seconds."
        )
    else:  # EXAMPLE_GUIDED
        return (
            f"Example-guided open question. "
            f"Show 3 examples to reduce cognitive load and prevent underspecification. "
            f"Expected time: 30-40 seconds."
        )


def _infer_preferences(target: OnboardingTarget) -> dict:
    """Infer preferences from collected evidence."""
    if not target.evidence:
        return {}

    # Get most recent evidence
    latest = target.evidence[-1]
    answer_data = latest.get("data", {})

    # Basic inference based on target type
    inferences = {
        "target_id": target.id,
        "dimension": target.dimension,
    }

    # Add answer details
    if "chosen_option" in answer_data:
        inferences["chosen_option"] = answer_data["chosen_option"]
    if "answer" in answer_data:
        inferences["answer"] = answer_data["answer"]

    return inferences


# Import needed for type checking
from src.onboarding.schema import QuestionType
