# Full Context Dump — Session 2026-07-22 (Complete State)

## The Core Understanding (between-the-lines knowledge)

### What KIM Actually IS (the mental model)

KIM is like a "personality card" that follows you across all LLMs. Imagine switching between Claude, Copilot, and ChatGPT — normally each starts blank. KIM means they all know you.

It's NOT an assistant. It's NOT a chatbot. It's the KNOWLEDGE about the user that makes any chatbot better.

Think of it like: a new colleague reads your "user manual" before talking to you. KIM IS that user manual — dynamically built, research-backed, always available via MCP.

### The Philosophical Design (how onboarding works)

Traditional approach: "What's your communication style?" → User gives vague answer → useless.

KIM's approach (GATE research):
- Define TARGETS: "I need to know if this user prefers concise or detailed answers"
- Each target has a BARRIER: "User must have explicitly chosen between two examples OR shown preference in 2+ interactions"
- The LLM sees the targets and FREELY decides how to reach them
- KIM never dictates questions — it only says "I still don't know X about this user"
- The LLM might ask an edge-case ("Version A or B?"), might ask directly, might observe behavior — it's free to choose strategy

This is key: KIM is a HARNESS with GOALS, not a script with fixed questions.

### The Self-Check Trick (why it's clever)

When the LLM writes an email draft and calls `check_draft`:
- The LLM thinks it's asking an external expert "is this good?"
- Actually, KIM just compares the draft against stored profile rules
- The LLM gets INDEPENDENT feedback it couldn't give itself (because you can't objectively judge your own work in the same context)
- This is deterministic — no LLM needed inside KIM for this

The LLM doesn't know it's checking itself. That's the whole trick.

### Why User OUTPUTS Matter More Than Inputs (Wu et al.)

This is counterintuitive. You'd think "what did the user ask?" matters. It doesn't much.

What matters: "What did the user WRITE/CHOOSE/APPROVE?"
- The email they actually sent (not the prompt "write me an email")
- The version they picked (A vs B)
- The correction they made ("nee, kürzer")
- The format they approved

KIM should store outputs and serve them ranked by relevance to the current query. Most relevant first (position in context matters — Wu et al. proved this).

### The Two Layers (practical difference)

**Layer 1 (any LLM with MCP):**
- LLM reads tool descriptions (the Anleitung = instructions embedded in tool schemas)
- LLM follows protocol: get_context → generate → check_draft → log_output
- Works today with Claude Desktop, Copilot, etc.
- The Anleitung IS the orchestration — no framework needed

**Layer 2 (Claude with sampling support):**
- KIM can REQUEST the LLM to do work (not just respond to tool calls)
- Each request gets a FRESH context (no bleed between steps)
- KIM controls the loop: "Now classify this. Now generate. Now validate."
- Same user LLM — but with context isolation between steps
- This is better because step 3 (validate) doesn't see step 2's reasoning

### What "Light Memory" Means

Not just profile. Also:
- "User is currently working on Project Skillfinder"
- "User decided to escalate the API-key issue to Teamlead last week"
- "User has been asking about Python async patterns recently"

This is CROSS-SESSION, CROSS-LLM context. Switch from Claude to Copilot? Both know you're working on Skillfinder. That's the value.

### The Tool Granularity Decision

Today's tools (`get_context`, `check_draft`, etc.) are HIGH-LEVEL placeholders.

Real implementation will split them. Example — `onboard` becomes:
- `get_targets()` — what's still unknown
- `get_next_target()` — suggested next (LLM can ignore)
- `store_insight(target, evidence, confidence)` — save what was learned
- `check_satisfied(target)` — does evidence meet the barrier?
- `get_onboarding_progress()` — percentage complete

We DON'T design all tools upfront. We build broad, then split when we see how the LLM actually uses them.

---

## Technical State

### Files That Exist

```
KIM/
├── .claude/
│   ├── settings.json              ← Hooks wired (3 hooks active)
│   ├── hooks/
│   │   ├── preflight_explainer.py ← PreToolUse: explains what's being built
│   │   ├── architect_radar.py     ← PostToolUse: detects cert topics
│   │   └── progress_tracker.py    ← PostToolUse: detects segment completion
│   ├── skills/
│   │   ├── status.md              ← /status skill
│   │   └── dump.md                ← /dump skill (context dump)
│   └── context_dumps/
│       ├── session_2026-07-22.md
│       └── session_2026-07-22_full.md (this file)
├── src/
│   ├── CLAUDE.md                  ← Code conventions (no LLM inside rule)
│   ├── __init__.py
│   ├── agents/__init__.py         ← EMPTY (might remove — no internal agents)
│   ├── api/__init__.py
│   ├── guardrails/__init__.py
│   ├── llm/__init__.py            ← EMPTY (might remove — no internal LLM)
│   ├── memory/__init__.py
│   ├── observability/__init__.py
│   ├── onboarding/__init__.py
│   ├── profile/__init__.py
│   ├── prompts/__init__.py
│   └── tools/__init__.py
├── learning/
│   ├── CLAUDE.md                  ← Learning format rules
│   └── 00_setup/README.md         ← Module 0: persistence architecture
├── tests/
│   ├── CLAUDE.md                  ← Test philosophy
│   ├── unit/__init__.py
│   └── integration/__init__.py
├── docs/
│   ├── diagrams/
│   │   ├── kim_system_logic.tex   ← Full LaTeX diagram (compiled)
│   │   ├── kim_logic_v5.pdf       ← Old version (still open, locked)
│   │   └── kim_logic_v6.pdf       ← Current version
│   └── onboarding_targets_checklist.md
├── config/
│   └── settings.yaml              ← Needs update for MCP-only architecture
├── CLAUDE.md                      ← Project constitution (updated)
├── ARCHITECTURE.md                ← Mermaid diagrams with build status colors
├── ONBOARDING_GATE_DESIGN.md      ← Original design doc (pre-dates current architecture)
├── pyproject.toml                 ← uv, Python 3.11+, pydantic, pytest, ruff
└── .gitignore
```

### Note on Folder Structure

Some folders from the OLD architecture still exist (src/agents/, src/llm/). These may need cleanup when we start Segment 1 — the new architecture doesn't have internal agents or LLM clients. The correct structure for new architecture:

```
src/
├── server.py              ← MCP server entry point (NEW)
├── tools/                 ← Exposed MCP tools
├── profile/               ← User profile (keep)
├── retrieval/             ← Retrieval engine (NEW)
├── validation/            ← Draft validation (NEW)
├── onboarding/            ← GATE system (keep)
├── anleitung/             ← Protocol instructions (NEW)
├── orchestration/         ← Layer 2 sampling (NEW)
├── data/                  ← Data layer (NEW)
└── observability/         ← Logging (keep)
```

### Config State

`config/settings.yaml` still references Ollama/Bedrock — needs rewrite for Segment 1.

### Git State

Git initialized but NO commits yet. All work is unstaged.

---

## Segment Progress

- [x] Segment 0: Complete (all 5 steps)
- [ ] Segment 1: MCP Server Foundation ← NEXT
- [ ] Segment 2: Profile & Data Layer
- [ ] Segment 3: Retrieval Engine
- [ ] Segment 4: Draft Validation
- [ ] Segment 5: GATE Onboarding
- [ ] Segment 6: Anleitung
- [ ] Segment 7: MCP Sampling (Layer 2)
- [ ] Segment 8: Output Logging & Continuous Learning
- [ ] Segment 9: Production Hardening

---

## User Preferences (how to work)

- Go SLOW. One concept at a time.
- Explain WHY before building WHAT.
- Never implement multiple concepts in one step.
- Frame everything as "when would I use this" and "why this over alternatives"
- The project is for learning — understanding matters more than shipping
- User wants to develop INTUITION for when to use tools (hooks, skills, agents, workflows)
- Show the decision points, not just the implementations

---

## What's Immediately Next

Segment 1: Build the MCP server foundation.
- Install/configure Python MCP SDK
- Create `src/server.py` as entry point
- Expose one tool (`get_context`) as a stub
- Verify it works with a real MCP client (Claude Desktop)
- Write `learning/01_mcp_tools/README.md`
