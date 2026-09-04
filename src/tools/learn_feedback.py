"""
Feedback Learning Tool
======================

Allows AI to learn from user feedback and update preferences dynamically.

Research basis:
- Westhaeusser et al. (arXiv 2510.07925): Continuous learning from implicit feedback
- Adaptive user modeling with urgency-based rollout

Urgency Scale:
- 5: Immediate (harsh feedback → change now)
- 4: Fast rollout (2-3 similar feedbacks)
- 3: Medium rollout (5 similar feedbacks)
- 2: Slow rollout (consistent pattern needed)
- 1: Very slow (10+ similar feedbacks)
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any
from mcp.types import Tool

from src.utils import get_user_id, iris_response


# ═══════════════════════════════════════════════════════════
# URGENCY ANALYSIS
# ═══════════════════════════════════════════════════════════

def analyze_urgency(feedback: str) -> int:
    """
    Analyze urgency from user feedback tone.

    Urgency scale:
    - 5: Harsh/immediate (expletives, "terrible", "awful", multiple exclamation marks)
    - 4: Strong (direct command, "keep it", "don't", no softeners)
    - 3: Clear (statement of fact, "is too X", no questions)
    - 2: Soft (suggestion, "could", "maybe", "a bit")
    - 1: Tentative (question, "not sure", "might")

    Args:
        feedback: User's feedback text

    Returns:
        Urgency score 1-5
    """
    feedback_lower = feedback.lower()

    # Urgency 5: Harsh/immediate
    harsh_markers = [
        "terrible", "awful", "horrible", "useless", "waste",
        "!!!", "stop", "never", "always", "constantly"
    ]
    if any(marker in feedback_lower for marker in harsh_markers):
        return 5

    # Urgency 4: Strong command
    strong_markers = [
        "keep it", "make it", "don't", "do not", "must", "need to"
    ]
    if any(marker in feedback_lower for marker in strong_markers):
        # But check if softened
        softeners = ["maybe", "could", "might", "perhaps", "possibly"]
        if not any(soft in feedback_lower for soft in softeners):
            return 4

    # Urgency 1: Tentative/question
    tentative_markers = [
        "not sure", "maybe", "perhaps", "might", "could be",
        "?", "wondering if", "thinking"
    ]
    if any(marker in feedback_lower for marker in tentative_markers):
        return 1

    # Urgency 2: Soft suggestion
    soft_markers = [
        "a bit", "a little", "somewhat", "slightly", "could", "would be nice"
    ]
    if any(marker in feedback_lower for marker in soft_markers):
        return 2

    # Urgency 3: Clear statement (default)
    return 3


# ═══════════════════════════════════════════════════════════
# FEEDBACK ANALYSIS
# ═══════════════════════════════════════════════════════════

def analyze_feedback(feedback: str, context: str) -> Dict[str, Any]:
    """
    Analyze user feedback to extract preference change.

    Args:
        feedback: What the user said
        context: What was the task/query

    Returns:
        {
            "preference_type": "response_length" | "technicality" | "format" | "tone",
            "direction": "increase" | "decrease",
            "target_value": str (what to change to),
            "urgency": int (1-5, determined by IRIS)
        }
    """
    # Simple keyword-based analysis (can be enhanced with LLM)
    feedback_lower = feedback.lower()

    # Analyze urgency first
    urgency = analyze_urgency(feedback)

    # Length feedback
    if any(word in feedback_lower for word in ["long", "short", "brief", "concise", "verbose"]):
        if any(word in feedback_lower for word in ["too long", "verbose", "rambling"]):
            return {
                "preference_type": "response_length",
                "direction": "decrease",
                "target_value": "shorter",
                "urgency": urgency
            }
        elif any(word in feedback_lower for word in ["too short", "more detail", "elaborate"]):
            return {
                "preference_type": "response_length",
                "direction": "increase",
                "target_value": "longer",
                "urgency": urgency
            }

    # Technical depth feedback
    if any(word in feedback_lower for word in ["technical", "simple", "detail", "explain"]):
        if any(word in feedback_lower for word in ["too technical", "simpler", "plain language"]):
            return {
                "preference_type": "technicality",
                "direction": "decrease",
                "target_value": "less_technical",
                "urgency": urgency
            }
        elif any(word in feedback_lower for word in ["more technical", "details", "deeper"]):
            return {
                "preference_type": "technicality",
                "direction": "increase",
                "target_value": "more_technical",
                "urgency": urgency
            }

    # Format feedback
    if any(word in feedback_lower for word in ["bullet", "list", "steps", "format"]):
        return {
            "preference_type": "format",
            "direction": "set",
            "target_value": "step_by_step" if "step" in feedback_lower else "bullet_points",
            "urgency": urgency
        }

    # Tone feedback
    if any(word in feedback_lower for word in ["formal", "casual", "professional", "friendly"]):
        if "formal" in feedback_lower or "professional" in feedback_lower:
            return {
                "preference_type": "tone",
                "direction": "set",
                "target_value": "professional",
                "urgency": urgency
            }
        elif "casual" in feedback_lower or "friendly" in feedback_lower:
            return {
                "preference_type": "tone",
                "direction": "set",
                "target_value": "casual",
                "urgency": urgency
            }

    return {
        "preference_type": "unknown",
        "direction": "unknown",
        "target_value": feedback,  # Store raw feedback for later analysis
        "urgency": urgency
    }


# ═══════════════════════════════════════════════════════════
# FEEDBACK STORAGE
# ═══════════════════════════════════════════════════════════

def get_feedback_store_path(user_id: str) -> Path:
    """Get path to user's feedback history."""
    iris_root = Path.home() / ".iris"
    feedback_dir = iris_root / "data" / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    return feedback_dir / f"{user_id}_feedback.json"


def load_feedback_history(user_id: str) -> list:
    """Load user's feedback history."""
    path = get_feedback_store_path(user_id)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feedback_entry(user_id: str, entry: dict):
    """Append feedback entry to history."""
    history = load_feedback_history(user_id)
    history.append(entry)

    path = get_feedback_store_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


# ═══════════════════════════════════════════════════════════
# URGENCY-BASED PROFILE UPDATE
# ═══════════════════════════════════════════════════════════

def should_apply_change(user_id: str, preference_type: str, urgency: int) -> bool:
    """
    Determine if change should be applied based on urgency and feedback history.

    Args:
        user_id: User identifier
        preference_type: Type of preference (response_length, technicality, etc.)
        urgency: 1-5 scale

    Returns:
        True if change should be applied now
    """
    if urgency >= 5:
        # Immediate change for harsh feedback
        return True

    # Load history and count similar feedbacks
    history = load_feedback_history(user_id)
    recent_similar = [
        h for h in history[-20:]  # Last 20 feedbacks
        if h.get("analysis", {}).get("preference_type") == preference_type
    ]

    count = len(recent_similar)

    # Thresholds based on urgency
    thresholds = {
        4: 2,   # Fast rollout: 2 similar feedbacks
        3: 5,   # Medium rollout: 5 similar feedbacks
        2: 8,   # Slow rollout: 8 similar feedbacks
        1: 10   # Very slow: 10+ similar feedbacks
    }

    threshold = thresholds.get(urgency, 5)
    return count >= threshold


def apply_profile_update(user_id: str, preference_type: str, target_value: str):
    """
    Update user profile with new preference.

    Args:
        user_id: User identifier
        preference_type: Type of preference to update
        target_value: New value
    """
    from src.profile import get_or_create_profile
    import asyncio

    # Load profile
    profile = asyncio.run(get_or_create_profile(user_id))

    if not profile:
        return False

    # Update based on preference type
    if preference_type == "response_length":
        # Update boundaries
        if "response_structure" not in profile.boundaries:
            profile.boundaries["response_structure"] = ""

        if target_value == "shorter":
            profile.boundaries["response_structure"] += " Keep responses concise."
        elif target_value == "longer":
            profile.boundaries["response_structure"] += " Provide detailed explanations."

    elif preference_type == "technicality":
        if target_value == "more_technical":
            profile.tone = "technical"
        elif target_value == "less_technical":
            profile.tone = "casual"

    elif preference_type == "format":
        profile.format_preference = target_value

    elif preference_type == "tone":
        profile.tone = target_value

    # Save updated profile
    profile_path = Path.home() / ".iris" / "data" / "profiles" / f"{profile.id}.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)

    return True


# ═══════════════════════════════════════════════════════════
# TOOL DEFINITION
# ═══════════════════════════════════════════════════════════

def get_learn_feedback_tool() -> Tool:
    """Get the learn_from_feedback tool definition."""
    return Tool(
        name="learn_from_feedback",
        description=(
            "Learn from user feedback and update preferences dynamically. "
            "\n\n"
            "Use when the user gives feedback about your responses "
            "(e.g., 'too long', 'more technical', 'simpler please'). "
            "\n\n"
            "IRIS automatically analyzes urgency from the feedback tone:\n"
            "- Harsh/immediate (expletives, '!!!', 'terrible') → Change now\n"
            "- Strong command ('keep it', 'don't', 'must') → Fast rollout\n"
            "- Clear statement ('is too X') → Medium rollout\n"
            "- Soft suggestion ('maybe', 'a bit') → Slow rollout\n"
            "- Tentative ('not sure', '?') → Very slow rollout\n"
            "\n\n"
            "You don't need to assess urgency — just pass the feedback as-is."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "feedback": {
                    "type": "string",
                    "description": "Exact user feedback (e.g., 'This is way too long!', 'Could be a bit shorter')"
                },
                "context": {
                    "type": "string",
                    "description": "What was the task/query that prompted this feedback"
                }
            },
            "required": ["feedback", "context"]
        }
    )


# ═══════════════════════════════════════════════════════════
# TOOL HANDLER
# ═══════════════════════════════════════════════════════════

async def handle_learn_feedback(arguments: dict, user_id: str) -> list:
    """
    Handle learn_from_feedback tool call.

    Args:
        arguments: {feedback, context}
        user_id: User identifier

    Returns:
        List with one TextContent block
    """
    from mcp.types import TextContent

    feedback = arguments.get("feedback", "")
    context = arguments.get("context", "")

    # Analyze feedback (IRIS determines urgency from tone)
    analysis = analyze_feedback(feedback, context)
    urgency = analysis.get("urgency", 3)

    # Store feedback entry
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "feedback": feedback,
        "context": context,
        "urgency": urgency,
        "analysis": analysis
    }
    save_feedback_entry(user_id, entry)

    # Check if change should be applied
    preference_type = analysis.get("preference_type")
    target_value = analysis.get("target_value")

    if preference_type == "unknown":
        response = f"""**Feedback logged** (urgency: {urgency}/5)

I've recorded your feedback: "{feedback}"

However, I couldn't automatically extract a preference change.
Your feedback is stored and will help improve personalization over time.

If you want immediate change, please rephrase more explicitly (e.g., "Keep responses shorter" or "Be more technical").
"""
    else:
        should_apply = should_apply_change(user_id, preference_type, urgency)

        if should_apply:
            # Apply change now
            success = apply_profile_update(user_id, preference_type, target_value)

            if success:
                response = f"""**Profile updated** (urgency: {urgency}/5)

Feedback: "{feedback}"
Change applied: {preference_type} → {target_value}

Your profile has been updated immediately. Future responses will reflect this change.
"""
            else:
                response = f"""**Update failed** (urgency: {urgency}/5)

Could not update profile. Check logs at ~/.iris/logs/iris_server.log
"""
        else:
            # Track for gradual rollout
            history = load_feedback_history(user_id)
            recent_similar = [
                h for h in history[-20:]
                if h.get("analysis", {}).get("preference_type") == preference_type
            ]
            count = len(recent_similar)

            thresholds = {4: 2, 3: 5, 2: 8, 1: 10}
            threshold = thresholds.get(urgency, 5)

            response = f"""**Feedback logged** (urgency: {urgency}/5)

Feedback: "{feedback}"
Detected change: {preference_type} → {target_value}

Status: Tracked for gradual rollout ({count}/{threshold} similar feedbacks)

Your profile will be updated after {threshold - count} more similar feedback(s).
This ensures the change reflects your true preference, not a one-off comment.
"""

    return [TextContent(type="text", text=iris_response(response))]
