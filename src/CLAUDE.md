# Source Code Conventions

## Architecture

IRIS is an MCP server. There are no internal LLM calls — all logic is deterministic.

- `server.py` is the entry point (MCP server lifecycle)
- `tools/` contains exposed MCP tools (each file = one tool or tool group)
- `profile/`, `data/`, `retrieval/` are internal — tools call into them
- `validation/` contains rule-based checkers (no LLM, purely deterministic)
- `onboarding/` contains the GATE state machine and target definitions
- `anleitung/` generates protocol instructions for external LLMs
- `orchestration/` handles Layer 2 (MCP sampling flows)

## Style

- Type hints on all public functions
- Pydantic models for all data structures
- Async where MCP SDK requires it
- No print statements — use `src/observability/` logging

## Key Rule

**No LLM calls inside IRIS.** All intelligence comes from the user's external LLM. IRIS is pure logic + data + retrieval.

Exception: Layer 2 (`orchestration/`) uses MCP sampling — but that's requesting compute from the USER's LLM, not running one internally.

## Inline Learning Links

When introducing a pattern that maps to a certification topic, add a single comment:
```python
# Learning: learning/01_mcp_tools/README.md#tool-registration
```

One line. The learning module has the full explanation.
