"""
Log Output Tool
===============

MCP tool for storing user outputs (emails, documents, code, etc.).

Flow:
1. User's LLM calls log_output(content, context, output_type)
2. IRIS stores output as JSON file
3. IRIS generates embedding via OpenAI
4. IRIS saves embedding to vector store
5. BM25 index is invalidated (rebuilt on next search)

This is how IRIS learns from user outputs (Wu et al. 2024).
"""

from uuid import UUID
from mcp.types import Tool, TextContent

from src.retrieval.embeddings import embed_text
from src.storage.file_store import get_output_store
from src.storage.embedding_store import get_embedding_store
from src.retrieval.bm25_search import invalidate_bm25
from src.profile import profile_exists
from src.utils import iris_response


# ═══════════════════════════════════════════════════════════
# TOOL DEFINITION
# ═══════════════════════════════════════════════════════════

def get_log_output_tool() -> Tool:
    """
    Get log_output tool definition for MCP.

    Returns:
        MCP Tool specification
    """
    return Tool(
        name="log_output",
        description=(
            "Store user output for future retrieval and personalization. "
            "\n\n"
            "Call this after the user approves the final version of something you generated "
            "(email, document, code, etc.). IRIS stores it and learns from the user's "
            "preferred style and patterns."
            "\n\n"
            "Research basis: Wu et al. (2024) — user OUTPUTS (not inputs) are the primary "
            "driver of personalization. What the user wrote/chose/approved matters more than "
            "what they asked for."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The final output content (email body, document text, code, etc.)"
                },
                "context": {
                    "type": "string",
                    "description": "Brief description of what this is (e.g., 'team status email', 'bug fix code')"
                },
                "output_type": {
                    "type": "string",
                    "description": "Type of output: 'email', 'document', 'code', 'message', etc.",
                    "enum": ["email", "document", "code", "message", "notes", "other"]
                }
            },
            "required": ["content", "context"]
        }
    )


# ═══════════════════════════════════════════════════════════
# TOOL HANDLER
# ═══════════════════════════════════════════════════════════

async def handle_log_output(arguments: dict, user_id: UUID) -> list[TextContent]:
    """
    Handle log_output tool call.

    Args:
        arguments: {"content": str, "context": str, "output_type": str}
        user_id: User UUID

    Returns:
        List with one TextContent confirming storage
    """
    # ═══ GATE CHECK: Profile must exist ═══
    # Learning: learning/07_user_profiles/README.md#onboarding-gates
    if not profile_exists(user_id):
        return [
            TextContent(
                type="text",
                text=iris_response(
                    "ONBOARDING_REQUIRED\n\n"
                    "No profile found. You must complete onboarding before using log_output.\n\n"
                    "Call start_onboarding() to begin."
                )
            )
        ]

    content = arguments["content"]
    context = arguments["context"]
    output_type = arguments.get("output_type", "other")

    # Validate
    if not content or not content.strip():
        return [
            TextContent(
                type="text",
                text=iris_response("❌ Error: content cannot be empty")
            )
        ]

    if not context or not context.strip():
        return [
            TextContent(
                type="text",
                text=iris_response("❌ Error: context cannot be empty")
            )
        ]

    try:
        # ═══ STEP 1: Store output as JSON ═══
        output_store = get_output_store()
        output = await output_store.create(
            user_id=user_id,
            content=content,
            context=context,
            output_type=output_type,
            metadata={
                "word_count": len(content.split()),
                "char_count": len(content)
            }
        )

        output_id = output["id"]

        # ═══ STEP 2: Generate embedding ═══
        try:
            embedding = await embed_text(content)

            # ═══ STEP 3: Save embedding ═══
            embedding_store = get_embedding_store()
            await embedding_store.append(
                user_id=user_id,
                embedding=embedding,
                output_id=output_id
            )

            embedding_status = "✓ Embedded"

        except Exception as e:
            # Embedding failed (no API key, network error, etc.)
            # Store output anyway, just skip embedding
            embedding_status = f"⚠️ Embedding failed: {str(e)}"

        # ═══ STEP 4: Invalidate BM25 cache ═══
        invalidate_bm25(user_id)

        # ═══ SUCCESS ═══
        word_count = output["metadata"]["word_count"]

        response = f"""✅ Output logged successfully

**ID:** {output_id}
**Context:** {context}
**Type:** {output_type}
**Size:** {word_count} words
**Status:** {embedding_status}

This output will be used for future personalization and retrieval.
"""

        return [
            TextContent(
                type="text",
                text=iris_response(response)
            )
        ]

    except Exception as e:
        # Unexpected error
        return [
            TextContent(
                type="text",
                text=f"❌ Error storing output: {str(e)}"
            )
        ]
