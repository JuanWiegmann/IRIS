"""
Memory System
=============

Multi-tiered memory based on Westhaeusser et al. (2024).

Three tiers:
1. STM (Short-Term Memory) - Recent conversation context
2. Summaries - Compressed conversation history
3. LTM (Long-Term Memory) - Project memory (reuses project_context)

Architecture:
- STM: Last N messages (configurable, default 10)
- Summaries: Rolling summaries of past conversations
- LTM: Project updates and milestones (already built in project_context)
"""

from src.memory.stm import (
    store_message,
    get_recent_messages,
    clear_stm,
    format_stm_for_llm
)
from src.memory.summaries import (
    create_summary,
    get_summaries,
    compress_old_messages,
    format_summaries_for_llm
)
from src.memory.ltm import (
    get_ltm_context,
    format_ltm_for_llm
)

__all__ = [
    "store_message",
    "get_recent_messages",
    "clear_stm",
    "format_stm_for_llm",
    "create_summary",
    "get_summaries",
    "compress_old_messages",
    "format_summaries_for_llm",
    "get_ltm_context",
    "format_ltm_for_llm"
]
