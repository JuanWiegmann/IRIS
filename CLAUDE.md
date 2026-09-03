# IRIS — Project Constitution

## What This Is

IRIS is an **MCP middleware server** — a personalization layer that sits between the user and ANY LLM they use (Claude, Copilot, ChatGPT). IRIS provides context, validates drafts, manages user profiles, and runs onboarding — so every LLM interaction is personalized, regardless of which model the user talks to.

**IRIS does NOT generate responses.** The user's LLM does all reasoning and generation. IRIS is pure logic + data.

This project is also a **learning environment** for the Claude Certified Architect – Professional certification.

## Foundational Research

1. **GATE** (Li, Tamkin, Goodman, Andreas — ICLR 2025): LLM-driven interactive preference elicitation. The LLM interviews users via edge-cases, binary questions, and open-ended questions. Users can't articulate preferences abstractly — forced choices reveal tacit knowledge.

2. **Multi-Agent Personalization** (Westhaeusser, Minker, Zepf — arXiv 2510.07925): Persistent multi-tiered memory (STM/Summaries/LTM) and dynamically evolving user profiles. Six agentic patterns for personalization.

3. **User Profile Roles** (Wu, Shi, Rahmani, Ramineni, Yilmaz — arXiv 2406.17803): User outputs (not inputs) are the primary driver of personalization. Relevance-ranked, output-only, most-relevant-first ordering maximizes quality.

## Scope

IRIS provides **personalization + light memory** to any LLM the user works with.

**What IRIS provides:**
- User profile (communication style, tone, format preferences, boundaries)
- Relevant examples (past user outputs, ranked by relevance to current query)
- Work context (current projects, recent decisions, ongoing topics)
- Validation (checking if LLM output matches the user's known preferences)

**What IRIS does NOT do:**
- Generate responses (the user's LLM does this)
- Orchestrate tasks (no email sending, no calendar, no Workday)
- Replace tools (IRIS augments, not replaces)

**Future (not now):** Could expand to VW Workday orchestration, task management, tool integration. Current scope is purely: make every LLM interaction personalized and context-aware.

## Architecture

IRIS is an MCP server with two layers:

**Layer 1 (any LLM):** Exposes tools + an Anleitung (protocol). The LLM follows instructions, calls tools deterministically:
- `get_context(query)` → profile + relevant examples (ranked by relevance)
- `check_draft(draft)` → two-stage validation (deterministic + semantic)
- `onboard tools` → target-based preference elicitation
- `log_output(text)` → store + embed for future retrieval

**Layer 2 (advanced clients):** If MCP sampling is supported, IRIS uses it for semantic validation — requesting the user's LLM to validate in a fresh context (no generation bias).

**Core Loop (The Agentic Validation Pattern):**
1. LLM calls `get_context()` → receives profile + ranked past outputs
2. LLM generates draft
3. LLM calls `check_draft(draft)` → IRIS validates (deterministic + MCP sampling)
4. If validation fails → LLM revises, back to step 3
5. If validation passes → LLM shows to user
6. LLM calls `log_output()` → IRIS stores + embeds for future retrieval

**Key trick:** `check_draft` acts as a blind validator. When using MCP sampling, IRIS requests validation in a FRESH context (no generation history) — the LLM can't judge its own work objectively, but a fresh instance can.

See `ARCHITECTURE.md` for visual diagrams. See `docs/diagrams/iris_system_logic.tex` for the full LaTeX version.

## Design Principles

1. **Segment by segment** — Build one concept at a time. Fully understand before moving on.
2. **IRIS never generates, only validates** — The user's LLM generates all responses. IRIS provides context and validation.
3. **Adaptive validation** — Deterministic checks first (free), then MCP sampling if available (uses user's LLM), fallback to deterministic only.
4. **LLM-agnostic** — Works with any MCP-capable LLM. No vendor lock-in.
5. **Research-backed targets** — Every onboarding dimension must cite scientific evidence.
6. **Tools grow from usage** — Start broad, split into finer tools as patterns emerge.
7. **The Anleitung IS the orchestration** — No agent framework needed, just well-designed instructions.
8. **Modern tooling** — Use Claude Code's full toolkit (hooks, skills, agents, workflows) where each genuinely fits.

## How To Work On This Project

- **PRE-INFO on every action** — Before EVERY tool call, write one visible line: `**PRE-INFO:** <what> — <why in IRIS's context>`. This is mandatory, never skip it.
- **Always check `ARCHITECTURE.md`** for current state and what's next
- **Use `/status`** for on-demand orientation
- **One segment at a time** — see the plan for segment order
- **Ask "why" freely** — understanding > speed
- **Architect Radar hook** fires after edits and surfaces certification-relevant learning links

## Using IRIS Tools (Meta-Rule for Claude Code)

When the user asks about their profile or preferences, **ALWAYS call IRIS tools first** (never check local memory or files):

**Auto-trigger `mcp__iris__get_context()` for:**
- "What do you know about me?"
- "What's my profile?"
- "What are my preferences?"
- "Tell me about my [style/tone/preferences]"

**Auto-trigger `/startIris` skill for:**
- "Set up my profile"
- "Run onboarding"
- "I want to personalize IRIS"

IRIS is the source of truth for user profiles — use it, don't reinvent it.

## Build Segments (Current Progress)

- [x] Segment 0: Project Skeleton + Context Architecture
- [x] Segment 1: MCP Server Foundation
- [x] Segment 2: Profile & Data Layer
- [ ] Segment 3: Retrieval Engine (BM25 + vector, log_output tool)
- [ ] Segment 4: Draft Validation (deterministic + MCP sampling)
- [ ] Segment 5: GATE Onboarding System (target-based elicitation)
- [ ] Segment 6: The Anleitung (Protocol Instructions)
- [ ] Segment 7: Layer 2 — MCP Sampling Orchestration
- [ ] Segment 8: Output Logging & Continuous Learning
- [ ] Segment 9: Production Hardening

## Tech Stack

- **Language:** Python 3.11+
- **Package manager:** uv
- **Server:** MCP SDK (Python)
- **Data:** Pydantic models + file-based persistence (vector store TBD)
- **No local LLM required** — user's LLM provides all compute
- **Diagrams:** LaTeX/TikZ (compiled with MiKTeX)

## What NOT To Do

- Don't implement multiple concepts in one step
- Don't add a local LLM dependency — IRIS must work without one
- Don't generate final responses inside IRIS — only provide context/validation
- Don't skip the learning module when introducing a new pattern
- Don't create monolithic tools — split by distinct actions the LLM needs independently
- Don't invent onboarding targets without research backing
