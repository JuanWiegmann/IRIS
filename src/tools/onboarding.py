"""
MCP Tools for GATE Onboarding

Tools exposed to the LLM for conducting preference elicitation.

Flow:
1. LLM calls start_onboarding() → gets Q1 template
2. User answers Q1 (role)
3. LLM calls store_answer("role", answer) → gets Q2 template
4. User answers Q2 (AI usage)
5. LLM calls store_answer("ai_usage", answer) → profile type detected, questions selected
6. For each remaining question:
   - LLM calls get_next_question() → gets question template + research guidance
   - User answers
   - LLM calls store_answer(target_id, answer) → validation + next question
7. LLM calls complete_onboarding() → profile generated
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from src.onboarding import (
    get_information_pool_after_answer,
    get_information_pool_before_question,
    get_onboarding_store,
    initialize_session,
)
from src.onboarding.profile_generation import generate_profile_from_session
from src.onboarding.schema import OnboardingSession
from src.onboarding.targets import get_all_targets
from src.profile.store import get_default_store


def start_onboarding(user_id: str) -> Dict[str, Any]:
    """
    Start onboarding flow.

    Returns first question (Q1: role) and guidance.

    Args:
        user_id: User identifier

    Returns:
        {
            "session_id": str,
            "question": {...},
            "guidance": str
        }
    """
    store = get_onboarding_store()

    # Check if already has active session
    existing = store.get_active_session(user_id)
    if existing and not existing.is_completed:
        # Resume existing session
        return {
            "session_id": existing.session_id,
            "status": "resumed",
            "message": "Resuming existing onboarding session",
            "next_question": get_next_question(user_id),
        }

    # Create new session
    session_id = f"onb_{uuid.uuid4().hex[:12]}"

    # Get Q1 template (role)
    all_targets = get_all_targets()
    q1_target = all_targets["role"]

    # Create minimal session (will be initialized after Q1+Q2)
    session = OnboardingSession(
        user_id=user_id,
        session_id=session_id,
        targets={"role": q1_target, "ai_usage": all_targets["ai_usage"]},
        questions_remaining=["role", "ai_usage"],
    )

    # Save
    store.save_session(session)

    return {
        "session_id": session_id,
        "status": "started",
        "message": "Onboarding started. This takes ~5 minutes and helps personalize your AI experience.",
        "question": {
            "target_id": "role",
            "dimension": q1_target.dimension,
            "question_text": q1_target.question_template.question_text,
            "question_type": q1_target.question_template.question_type.value,
            "example_prompt": q1_target.question_template.example_prompt,
            "research_basis": q1_target.research_basis,
        },
        "guidance": (
            "This is Q1 of 2 anchor questions. "
            "Your answer will help select the most relevant follow-up questions. "
            "Expected time: 30 seconds."
        ),
    }


def store_answer(
    user_id: str, target_id: str, answer: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store user's answer to a question.

    Args:
        user_id: User identifier
        target_id: Target dimension ID (e.g., "role", "technical_depth")
        answer: User's answer. Format depends on question type:
            - Binary/edge-case: {"chosen_option": "value"}
            - Open: {"answer": "text"}

    Returns:
        {
            "status": "recorded",
            "barrier_met": bool,
            "confidence": float,
            "next_question": {...} or None,
            "session_progress": {...}
        }
    """
    store = get_onboarding_store()

    # Load session
    session = store.get_active_session(user_id)
    if not session:
        return {"error": "No active onboarding session. Call start_onboarding() first."}

    # Validate target exists
    if target_id not in session.targets:
        return {"error": f"Unknown target: {target_id}"}

    # Record answer
    confidence_delta = 0.3 if target_id in ["role", "ai_usage"] else 0.5
    session.add_answer(target_id, answer, confidence_delta=confidence_delta)

    # Special handling for Q1 + Q2 (anchor questions)
    if target_id == "role" and session.questions_asked == 1:
        # Just answered Q1, need Q2 next
        store.save_session(session)

        q2_target = session.targets["ai_usage"]
        return {
            "status": "recorded",
            "message": "Role recorded. Now let's understand how you use AI.",
            "barrier_met": True,
            "next_question": {
                "target_id": "ai_usage",
                "dimension": q2_target.dimension,
                "question_text": q2_target.question_template.question_text,
                "question_type": q2_target.question_template.question_type.value,
                "example_prompt": q2_target.question_template.example_prompt,
            },
            "guidance": (
                "This is Q2 of 2 anchor questions. "
                "After this, I'll select the most relevant questions for your role. "
                "Expected time: 30 seconds."
            ),
        }

    elif target_id == "ai_usage" and session.questions_asked == 2:
        # Just answered Q2, now initialize full session with adaptive questions
        # Extract from session fields (populated by add_answer) or from evidence (fallback)
        role = session.role
        ai_usage = session.ai_usage

        # Fallback: extract from target evidence if fields not populated
        if not role and "role" in session.targets:
            role_evidence = session.targets["role"].evidence
            if role_evidence:
                role = role_evidence[0]["data"].get("answer") or role_evidence[0]["data"].get("chosen_option")

        if not ai_usage and "ai_usage" in session.targets:
            ai_usage_evidence = session.targets["ai_usage"].evidence
            if ai_usage_evidence:
                ai_usage = ai_usage_evidence[0]["data"].get("answer") or ai_usage_evidence[0]["data"].get("chosen_option")

        # Re-initialize session with adaptive question selection
        session = initialize_session(
            user_id=user_id,
            session_id=session.session_id,
            role=role,
            ai_usage=ai_usage,
        )

        store.save_session(session)

        # Get information pool for next question
        info_pool = get_information_pool_before_question(session)

        return {
            "status": "profile_type_detected",
            "message": f"Profile type: {session.profile_type.value}. Selected {len(session.questions_remaining)} relevant questions.",
            "profile_type": session.profile_type.value,
            "questions_selected": len(session.questions_remaining),
            "next_question": _format_next_question(info_pool) if info_pool.get("should_continue") else None,
            "session_progress": info_pool.get("session_progress"),
        }

    # Regular question answered
    info_pool_after = get_information_pool_after_answer(session, target_id)

    # Save session
    store.save_session(session)

    # Get next question if should continue
    next_q = None
    if info_pool_after.get("should_continue"):
        info_pool_before = get_information_pool_before_question(session)
        next_q = _format_next_question(info_pool_before) if info_pool_before.get("should_continue") else None

    return {
        "status": "recorded",
        "validation_result": info_pool_after.get("validation_result"),
        "should_continue": info_pool_after.get("should_continue"),
        "next_question": next_q,
        "session_progress": info_pool_after.get("session_progress"),
    }


def get_next_question(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get next question to ask.

    Args:
        user_id: User identifier

    Returns:
        Question details or None if onboarding complete
    """
    store = get_onboarding_store()

    session = store.get_active_session(user_id)
    if not session:
        return None

    info_pool = get_information_pool_before_question(session)

    if not info_pool.get("should_continue"):
        return None

    return _format_next_question(info_pool)


def complete_onboarding(user_id: str) -> Dict[str, Any]:
    """
    Complete onboarding and generate profile.

    Args:
        user_id: User identifier

    Returns:
        {
            "status": "completed",
            "profile_generated": bool,
            "questions_answered": int,
            "core_satisfaction_rate": float
        }
    """
    import asyncio

    store = get_onboarding_store()

    session = store.get_active_session(user_id)
    if not session:
        return {"error": "No active onboarding session"}

    # Check if can complete
    if not session.can_complete():
        return {
            "error": "Cannot complete yet",
            "core_satisfaction_rate": session.get_core_satisfaction_rate(),
            "message": "Need to answer more core questions (80% minimum)",
        }

    # Mark complete
    session.complete()

    # Generate UserProfile from evidence
    profile = generate_profile_from_session(session)

    # Save profile
    profile_store = get_default_store()
    try:
        asyncio.run(profile_store.save(profile))
        profile_generated = True
    except Exception as e:
        profile_generated = False
        # Still mark session complete but flag the error
        store.save_session(session)
        store.delete_active_session(user_id)
        return {
            "status": "completed_with_error",
            "error": f"Profile generation failed: {str(e)}",
            "session_id": session.session_id,
            "questions_answered": session.questions_asked,
        }

    # Save completed session
    store.save_session(session)

    # Delete active session
    store.delete_active_session(user_id)

    return {
        "status": "completed",
        "session_id": session.session_id,
        "profile_id": str(profile.id),
        "profile_generated": profile_generated,
        "questions_answered": session.questions_asked,
        "core_satisfaction_rate": session.get_core_satisfaction_rate(),
        "satisfied_dimensions": session.get_satisfied_dimensions(),
        "profile_type": session.profile_type.value if session.profile_type else None,
        "message": "Onboarding complete! Your profile will be used to personalize responses.",
    }


def _format_next_question(info_pool: Dict[str, Any]) -> Dict[str, Any]:
    """Format next question from information pool."""
    next_target = info_pool.get("next_target")
    if not next_target:
        return None

    return {
        "target_id": next_target["id"],
        "dimension": next_target["dimension"],
        "priority": next_target["priority"],
        "question_text": next_target["question_template"]["question_text"],
        "question_type": next_target["question_template"]["question_type"],
        "options": next_target["question_template"].get("options"),
        "example_prompt": next_target["question_template"].get("example_prompt"),
        "research_basis": next_target["research_basis"],
        "guidance": info_pool.get("recommended_strategy"),
        "session_progress": info_pool.get("session_progress"),
    }
