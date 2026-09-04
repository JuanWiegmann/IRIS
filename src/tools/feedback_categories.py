"""
Feedback Categories System
==========================

Provides LLM with categories and rules for handling user feedback.

Flow:
1. LLM auto-checks user message for feedback signals
2. LLM calls: get_feedback_categories()
3. IRIS returns: categories, detection patterns, update rules
4. LLM analyzes user sentiment using these categories
5. LLM decides if profile should change
6. LLM calls: apply_feedback_change(category, change_description)
7. LLM mentions change at start of response

Design: LLM does sentiment analysis (better than regex), IRIS provides structure.
"""

from typing import Dict, Any, List
from mcp.types import Tool, TextContent


# ═══════════════════════════════════════════════════════════
# FEEDBACK CATEGORIES
# ═══════════════════════════════════════════════════════════

FEEDBACK_CATEGORIES = {
    "response_length": {
        "description": "User wants responses to be longer or shorter",
        "detection_signals": [
            "User says: 'too long', 'too short', 'verbose', 'concise', 'brief'",
            "User complains about length multiple times",
            "User explicitly asks for shorter/longer responses"
        ],
        "change_types": {
            "make_shorter": {
                "threshold": "1-2 similar feedbacks",
                "action": "Add 'Keep responses concise' to boundaries",
                "reversible": True
            },
            "make_longer": {
                "threshold": "2-3 similar feedbacks",
                "action": "Add 'Provide detailed explanations' to boundaries",
                "reversible": True
            }
        },
        "decision_guide": "Check sentiment: harsh/strong = change immediately, soft = wait for pattern"
    },

    "technical_depth": {
        "description": "User wants more or less technical detail",
        "detection_signals": [
            "User says: 'too technical', 'simpler', 'more detail', 'explain like I'm 5'",
            "User asks for definitions of terms you used",
            "User says they already know something you explained"
        ],
        "change_types": {
            "less_technical": {
                "threshold": "1-2 similar feedbacks",
                "action": "Change tone to 'casual', add 'Avoid jargon' boundary",
                "reversible": True
            },
            "more_technical": {
                "threshold": "2-3 similar feedbacks",
                "action": "Change tone to 'technical', add 'Include technical details' boundary",
                "reversible": True
            }
        },
        "decision_guide": "User's technical knowledge changes over time - be conservative"
    },

    "format_preference": {
        "description": "User prefers different response format",
        "detection_signals": [
            "User says: 'bullet points', 'step by step', 'numbered list'",
            "User reformats your response in their follow-up",
            "User asks 'can you make that a list?'"
        ],
        "change_types": {
            "bullet_points": {
                "threshold": "1 explicit request",
                "action": "Set format_preference = 'bullet_points'",
                "reversible": True
            },
            "step_by_step": {
                "threshold": "1 explicit request",
                "action": "Set format_preference = 'step_by_step'",
                "reversible": True
            },
            "paragraphs": {
                "threshold": "1 explicit request",
                "action": "Set format_preference = 'paragraphs'",
                "reversible": True
            }
        },
        "decision_guide": "Format is explicit - if user asks for it, change immediately"
    },

    "tone": {
        "description": "User wants different communication tone",
        "detection_signals": [
            "User says: 'too formal', 'too casual', 'be professional', 'be friendly'",
            "User mirrors a specific tone in their messages",
            "User corrects your phrasing to be more/less formal"
        ],
        "change_types": {
            "professional": {
                "threshold": "1-2 similar feedbacks",
                "action": "Set tone = 'professional'",
                "reversible": True
            },
            "casual": {
                "threshold": "1-2 similar feedbacks",
                "action": "Set tone = 'casual'",
                "reversible": True
            },
            "technical": {
                "threshold": "2-3 similar feedbacks",
                "action": "Set tone = 'technical'",
                "reversible": True
            }
        },
        "decision_guide": "Tone affects entire interaction - be thoughtful about changes"
    },

    "proactivity": {
        "description": "User wants more or less proactive suggestions",
        "detection_signals": [
            "User says: 'just answer the question', 'stop suggesting', 'I'll ask if I need help'",
            "User says: 'what else should I consider?', 'any other ideas?'",
            "User ignores your suggestions consistently"
        ],
        "change_types": {
            "less_proactive": {
                "threshold": "2-3 similar feedbacks",
                "action": "Add 'Only answer what's asked' boundary",
                "reversible": True
            },
            "more_proactive": {
                "threshold": "3-5 similar requests",
                "action": "Add 'Offer suggestions proactively' boundary",
                "reversible": True
            }
        },
        "decision_guide": "Proactivity is polarizing - strong signal needed"
    },

    "explanation_style": {
        "description": "How much context/background to provide",
        "detection_signals": [
            "User says: 'I know that already', 'skip the background', 'just the answer'",
            "User says: 'why?', 'explain more', 'I don't understand'",
            "User's questions suggest missing context"
        ],
        "change_types": {
            "minimal_context": {
                "threshold": "2-3 similar feedbacks",
                "action": "Add 'Assume prior knowledge' boundary",
                "reversible": True
            },
            "full_context": {
                "threshold": "2-3 similar requests",
                "action": "Add 'Provide full context and background' boundary",
                "reversible": True
            }
        },
        "decision_guide": "Balance: too little context = confusion, too much = annoyance"
    }
}


# ═══════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════

def get_feedback_categories_tool() -> Tool:
    """Get the feedback categories reference."""
    return Tool(
        name="get_feedback_categories",
        description=(
            "Get categories and rules for detecting and handling user feedback. "
            "\n\n"
            "IMPORTANT: Call this AUTOMATICALLY when starting to analyze any user message. "
            "Check every user response for feedback signals - don't wait for explicit feedback. "
            "\n\n"
            "Returns: Categories with detection signals, thresholds, and update rules. "
            "You analyze the user's sentiment, IRIS provides the structure."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )


def get_apply_feedback_change_tool() -> Tool:
    """Tool for applying a feedback-driven profile change."""
    return Tool(
        name="apply_feedback_change",
        description=(
            "Apply a profile change based on detected user feedback. "
            "\n\n"
            "Use AFTER you've analyzed user feedback using feedback categories "
            "and decided a change is warranted. "
            "\n\n"
            "After calling this, mention the change at the start of your response: "
            "'I've updated your profile to prefer shorter responses based on your feedback.'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category name (e.g., 'response_length', 'technical_depth')",
                    "enum": list(FEEDBACK_CATEGORIES.keys())
                },
                "change_type": {
                    "type": "string",
                    "description": "Specific change (e.g., 'make_shorter', 'less_technical')"
                },
                "user_feedback": {
                    "type": "string",
                    "description": "What the user said that triggered this change"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why you decided this change is needed (for logging)"
                }
            },
            "required": ["category", "change_type", "user_feedback", "reasoning"]
        }
    )


# ═══════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════

async def handle_get_feedback_categories(arguments: dict) -> list[TextContent]:
    """Return feedback categories and rules."""
    import json
    from src.utils import iris_response

    response = {
        "categories": FEEDBACK_CATEGORIES,
        "workflow": {
            "step_1": "Check if user message contains feedback signals",
            "step_2": "Analyze user sentiment (harsh/strong/soft/tentative)",
            "step_3": "Check feedback history - is this a pattern?",
            "step_4": "Decide if threshold met for this category",
            "step_5": "If yes → call apply_feedback_change()",
            "step_6": "Mention change at start of response"
        },
        "auto_check": "Call get_feedback_categories() at start of EVERY user interaction to check for implicit feedback"
    }

    return [TextContent(
        type="text",
        text=iris_response(json.dumps(response, indent=2))
    )]


async def handle_apply_feedback_change(arguments: dict, user_id: str) -> list[TextContent]:
    """Apply a feedback-driven profile change."""
    from pathlib import Path
    import json
    from datetime import datetime
    from src.utils import iris_response
    from src.profile import get_or_create_profile

    category = arguments.get("category")
    change_type = arguments.get("change_type")
    user_feedback = arguments.get("user_feedback")
    reasoning = arguments.get("reasoning")

    # Load profile
    profile = await get_or_create_profile(user_id)
    if not profile:
        return [TextContent(
            type="text",
            text=iris_response("ERROR: No profile found. Run onboarding first.")
        )]

    # Get change spec
    category_spec = FEEDBACK_CATEGORIES.get(category, {})
    change_spec = category_spec.get("change_types", {}).get(change_type, {})

    if not change_spec:
        return [TextContent(
            type="text",
            text=iris_response(f"ERROR: Unknown change type '{change_type}' for category '{category}'")
        )]

    # Apply change based on category
    changed = False

    if category == "response_length":
        if change_type == "make_shorter":
            profile.boundaries["response_structure"] = profile.boundaries.get("response_structure", "") + " Keep responses concise."
            changed = True
        elif change_type == "make_longer":
            profile.boundaries["response_structure"] = profile.boundaries.get("response_structure", "") + " Provide detailed explanations."
            changed = True

    elif category == "technical_depth":
        if change_type == "less_technical":
            profile.tone = "casual"
            profile.boundaries["explanation_style"] = "Avoid jargon, explain terms"
            changed = True
        elif change_type == "more_technical":
            profile.tone = "technical"
            profile.boundaries["explanation_style"] = "Include technical details"
            changed = True

    elif category == "format_preference":
        profile.format_preference = change_type  # e.g., "bullet_points"
        changed = True

    elif category == "tone":
        profile.tone = change_type  # e.g., "professional"
        changed = True

    elif category == "proactivity":
        if change_type == "less_proactive":
            profile.boundaries["proactivity"] = "Only answer what's asked"
            changed = True
        elif change_type == "more_proactive":
            profile.boundaries["proactivity"] = "Offer suggestions proactively"
            changed = True

    elif category == "explanation_style":
        if change_type == "minimal_context":
            profile.boundaries["explanation_style"] = "Assume prior knowledge"
            changed = True
        elif change_type == "full_context":
            profile.boundaries["explanation_style"] = "Provide full context"
            changed = True

    if changed:
        # Save updated profile
        profile_path = Path.home() / ".iris" / "data" / "profiles" / f"{profile.id}.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(), f, indent=2)

        # Log feedback
        feedback_log = Path.home() / ".iris" / "data" / "feedback" / f"{user_id}_changes.json"
        feedback_log.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category,
            "change_type": change_type,
            "user_feedback": user_feedback,
            "reasoning": reasoning,
            "action": change_spec.get("action")
        }

        if feedback_log.exists():
            with open(feedback_log, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        history.append(log_entry)

        with open(feedback_log, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        response = f"""**Profile updated**

Category: {category}
Change: {change_type}
Action: {change_spec.get('action')}

User feedback: "{user_feedback}"
Reasoning: {reasoning}

This change will apply to all future responses.
"""
    else:
        response = f"ERROR: Could not apply change for category '{category}'"

    return [TextContent(
        type="text",
        text=iris_response(response)
    )]
