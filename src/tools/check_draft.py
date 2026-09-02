"""
Check Draft Tool (Enhanced)
============================

MCP tool for validating drafts with use-case-aware routing.

Validation Strategy:
1. Detect use case (messaging/coding/Mendix)
2. Apply deterministic checks (per use case)
3. (Future) MCP sampling for semantic validation
4. Return combined feedback

Use Cases:
- MESSAGING: tone, format, boundaries
- CODING: syntax patterns, best practices (+ Ponytail if available)
- MENDIX: domain rules, XML structure (no CLI execution)
"""

from uuid import UUID
from mcp.types import Tool, TextContent

from src.validation import detect_use_case, UseCase


# ═══════════════════════════════════════════════════════════
# TOOL DEFINITION
# ═══════════════════════════════════════════════════════════

def get_check_draft_tool() -> Tool:
    """
    Get check_draft tool definition for MCP.

    Returns:
        MCP Tool specification
    """
    return Tool(
        name="check_draft",
        description=(
            "Validate a draft against the user's profile and use-case-specific rules. "
            "\n\n"
            "This performs two-stage validation:\n"
            "1. Deterministic checks (style, format, patterns)\n"
            "2. Semantic validation (via MCP sampling if available)\n"
            "\n"
            "Automatically detects use case:\n"
            "- MESSAGING: emails, documents (checks tone, format, boundaries)\n"
            "- CODING: code validation (syntax, best practices, Ponytail if available)\n"
            "- MENDIX: Mendix validation (domain rules, XML structure)\n"
            "\n"
            "Call this BEFORE showing a draft to the user to catch issues early."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "draft": {
                    "type": "string",
                    "description": "The draft content to validate"
                },
                "context": {
                    "type": "string",
                    "description": "Brief description of what this draft is (e.g., 'team email', 'Python function', 'Mendix entity')"
                }
            },
            "required": ["draft", "context"]
        }
    )


# ═══════════════════════════════════════════════════════════
# TOOL HANDLER
# ═══════════════════════════════════════════════════════════

async def handle_check_draft(arguments: dict, user_id: UUID) -> list[TextContent]:
    """
    Handle check_draft tool call.

    Args:
        arguments: {"draft": str, "context": str}
        user_id: User UUID

    Returns:
        List with one TextContent containing validation results
    """
    draft = arguments["draft"]
    context = arguments.get("context", "")

    if not draft or not draft.strip():
        return [
            TextContent(
                type="text",
                text="❌ Error: draft cannot be empty"
            )
        ]

    # ═══ STEP 1: Detect Use Case ═══
    use_case = detect_use_case(context, draft)

    # ═══ STEP 2: Route to Appropriate Validator ═══
    if use_case == UseCase.MESSAGING:
        result = await _validate_messaging(draft, context, user_id)
    elif use_case == UseCase.CODING:
        result = await _validate_coding(draft, context, user_id)
    elif use_case == UseCase.MENDIX:
        result = await _validate_mendix(draft, context, user_id)
    else:
        result = await _validate_messaging(draft, context, user_id)  # Fallback

    return [
        TextContent(
            type="text",
            text=result
        )
    ]


# ═══════════════════════════════════════════════════════════
# VALIDATION STRATEGIES (PER USE CASE)
# ═══════════════════════════════════════════════════════════

async def _validate_messaging(draft: str, context: str, user_id: UUID) -> str:
    """
    Validate messaging content (emails, documents).

    Checks:
    - Tone appropriateness
    - Format preferences
    - Boundary violations
    - Length constraints

    Args:
        draft: Draft content
        context: Context description
        user_id: User UUID

    Returns:
        Validation result as markdown
    """
    # TODO (Segment 4): Implement deterministic checks
    # - Load profile
    # - Check tone (casual vs formal markers)
    # - Check format (bullets vs paragraphs)
    # - Check boundaries (jargon blacklist)
    # - Check length

    # TODO (Segment 4): MCP sampling for semantic validation
    # - Ask: "Is this message appropriate for the context?"

    # Placeholder for now
    return f"""✅ Draft validated (MESSAGING)

**Use Case:** Messaging/Communication
**Context:** {context}
**Length:** {len(draft.split())} words

**Status:** Basic validation passed
⚠️ Full validation coming in Segment 4

*Note: Checks tone, format, and boundaries against user profile*
"""


async def _validate_coding(draft: str, context: str, user_id: UUID) -> str:
    """
    Validate code content.

    Checks:
    - Basic syntax patterns
    - Common anti-patterns
    - Best practices (simple heuristics)

    Enhanced (future):
    - Ponytail plugin quality checks (via MCP sampling)

    Args:
        draft: Draft code
        context: Context description
        user_id: User UUID

    Returns:
        Validation result as markdown
    """
    issues = []

    # Basic code quality checks (deterministic)
    if "TODO" in draft or "FIXME" in draft:
        issues.append("⚠️ Contains TODO/FIXME markers")

    if "print(" in draft and "logging" not in draft.lower():
        issues.append("💡 Consider using logging instead of print statements")

    # Check for bare except
    if "except:" in draft and "except " not in draft:
        issues.append("⚠️ Bare 'except:' clause - specify exception types")

    # TODO (Segment 4): MCP sampling with Ponytail awareness
    # - Ask: "Validate this code for quality and correctness"
    # - Claude Code (with Ponytail) performs deep analysis
    # - Returns detailed code quality feedback

    status = "✅ Looks good" if not issues else "⚠️ Suggestions found"

    issues_text = "\n".join(issues) if issues else "*No issues detected*"

    return f"""{status}

**Use Case:** Code Validation
**Context:** {context}
**Lines:** {len(draft.splitlines())}

**Code Quality Checks:**
{issues_text}

⚠️ **Note:** Enhanced validation with Ponytail coming in Segment 4
Future: Deep analysis (complexity, coverage, best practices)

*For now: Basic pattern checks only*
"""


async def _validate_mendix(draft: str, context: str, user_id: UUID) -> str:
    """
    Validate Mendix content.

    Checks:
    - XML structure (basic)
    - Entity naming conventions
    - Common Mendix patterns

    Does NOT:
    - Execute Mendix CLI (it's beta, unstable)
    - Deploy to Mendix Cloud
    - Validate against running app

    Args:
        draft: Draft Mendix content
        context: Context description
        user_id: User UUID

    Returns:
        Validation result as markdown
    """
    issues = []

    # Basic Mendix checks
    if "<entity" in draft and 'name=""' in draft:
        issues.append("❌ Entity has empty name attribute")

    if "microflow" in draft.lower() and not any(x in draft for x in ["<microflow", "microflow name"]):
        issues.append("💡 Microflow mentioned but not properly defined")

    # Check for plural entity names (anti-pattern)
    if "<entity name=" in draft:
        import re
        entities = re.findall(r'<entity name="(\w+)"', draft)
        plurals = [e for e in entities if e.endswith('s') and len(e) > 3]
        if plurals:
            issues.append(f"⚠️ Entity names should be singular: {', '.join(plurals)}")

    status = "✅ Looks good" if not issues else "⚠️ Issues found"

    issues_text = "\n".join(issues) if issues else "*No issues detected*"

    return f"""{status}

**Use Case:** Mendix Development
**Context:** {context}

**Mendix Pattern Checks:**
{issues_text}

⚠️ **Important:**
- Mendix CLI is in **BETA** — validation only, no execution
- Always verify in Mendix Studio before deployment
- Enhanced validation with MCP sampling coming in Segment 4

*For now: Basic XML pattern checks only*
"""
