# Context Dump — Session 2026-07-22 (Final)

## 1. Mental Model

### What KIM IS
KIM is an MCP middleware server — a "personality card" that follows the user across ALL LLMs (Claude, Copilot, ChatGPT). It's invisible. It doesn't DO anything for the user. It only KNOWS things about the user and provides that knowledge to whatever LLM the user is talking to.

The user's LLM calls KIM via MCP to get context ("how should I talk to this person?"), validates its own drafts blindly via `check_draft`, and logs final outputs for future retrieval. KIM is pure logic + data. No LLM runs inside KIM.

### How Understanding Evolved This Session
1. Started: "Build a multi-agent system with Ollama + Bedrock Claude"
2. Shifted: "Wait, the user's LLM is powerful enough — KIM doesn't need its own LLM"
3. Landed: "KIM is a pure MCP server. Logic + data. The user's LLM does ALL reasoning."
4. Refined: "KIM is personalization + light memory ONLY. Not a task executor."

### The Self-Check Trick
`check_draft` makes the LLM call KIM thinking it's an external validator. KIM compares the draft against stored profile rules deterministically. The LLM gets independent feedback it couldn't give itself — because you can't judge your own output in the same context. No LLM needed inside KIM for this.

### Onboarding Philosophy (Target-Based GATE)
KIM defines research-backed TARGETS (what must be known about the user). Each target has a BARRIER (minimum evidence to count as "satisfied"). The LLM sees open targets and FREELY chooses strategy — edge-case questions, binary, direct ask, observation. KIM never dictates HOW to ask. Only WHAT needs to be known.

### Why User Outputs > Inputs (Wu et al. 2024)
What the user WROTE/CHOSE/APPROVED drives personalization (not what they asked). Store past emails sent, versions picked, corrections made. Serve them ranked by relevance. Most relevant first — position in context matters.

### Two Layers
- Layer 1: Any MCP client. Tools + Anleitung. LLM follows protocol deterministically.
- Layer 2: Advanced clients (Claude). MCP sampling — KIM orchestrates with fresh context per step.

### Scope
Personalization + light cross-session memory. NOT task execution. NOT workflow orchestration. KIM answers "how should I talk to this person" — never "do this task."

## 2. Decisions Made This Session

| Decision | Why | Rejected |
|----------|-----|----------|
| KIM = MCP server, no internal LLM | User's LLM is powerful enough, zero install | Multi-agent with Ollama |
| User's LLM does ALL reasoning | Best quality from main model | KIM generates responses |
| check_draft as blind validator | Independent feedback | LLM self-validates |
| Research-based onboarding targets | Scientific backing | Arbitrary questions |
| Tools start broad, split later | Can't predict patterns upfront | Design all tools upfront |
| Two layers (tools vs sampling) | Max compatibility + advanced option | One approach only |
| Personalization + memory scope ONLY | Clear boundary | Full Workday orchestrator |
| PRE-INFO on every action | User wants full transparency | Silent operations |
| /start, /end, /dump skills | Session persistence | Manual context mgmt |
| Session ID in last_session.json | Enables claude --resume | No session tracking |

## 3. What Was Built (Segment 0 — COMPLETE)

```
.claude/settings.json              — Hooks: preflight (.*), post (Edit|Write)
.claude/hooks/preflight_explainer.py — PRE-INFO on ALL tool actions
.claude/hooks/architect_radar.py   — Cert topic detection after edits
.claude/hooks/progress_tracker.py  — Segment completion detection
.claude/skills/start/SKILL.md      — /start (resume or recover)
.claude/skills/end/SKILL.md        — /end (dump + commit)
.claude/skills/dump/SKILL.md       — /dump (context dump only)
.claude/skills/status/SKILL.md     — /status (build state)
.claude/last_session.json          — Session pointer for /start
.claude/context_dumps/             — Session knowledge dumps

CLAUDE.md                          — Constitution (MCP arch + scope + PRE-INFO rule)
ARCHITECTURE.md                    — Mermaid diagrams, color-coded build status
src/CLAUDE.md                      — Code conventions (no LLM inside)
learning/CLAUDE.md                 — Learning format (WHY→WHAT→HOW→THINK)
tests/CLAUDE.md                    — Test philosophy
learning/00_setup/README.md        — Module 0: persistence architecture

pyproject.toml                     — uv, Python 3.11+, pydantic, pytest, ruff
config/settings.yaml               — NEEDS UPDATE for MCP-only architecture
docs/diagrams/kim_system_logic.tex — LaTeX system diagram
docs/diagrams/kim_logic_v6.pdf     — Compiled current version
docs/onboarding_targets_checklist.md — Research TODOs + targets
tests/unit/test_example.py         — Placeholder
```

### Needs Cleanup in Segment 1:
- `src/agents/` — empty, old architecture
- `src/llm/` — empty, old architecture
- `src/api/` — might repurpose or remove
- `config/settings.yaml` — still references Ollama/Bedrock

## 4. Key Research

### GATE (ICLR 2025) — Preference Elicitation
- Forced choices reveal tacit knowledge users can't articulate
- 5-min window optimal, 18-30 questions across 6 sections
- Open-ended questions DECREASE performance in technical domains
- Works with open-source models

### Wu et al. 2024 — User Profile Roles
- User OUTPUTS are primary driver (not inputs)
- Output-only fits 2-5x more in context
- Most-relevant-first ordering critical
- Non-user semantic content HURTS performance
- Correct pairing NOT necessary

### Westhaeusser et al. 2025 — Multi-Agent Personalization
- Coordinator → Operator → Validator → Generator
- STM/Summaries/LTM memory tiers
- 96% retrieval accuracy with full system
- User profile removal = -5.6% accuracy

## 5. Current State

- Segment 0: ✅ COMPLETE
- Segment 1: ⏳ NEXT (MCP Server Foundation)
- Git: 3 commits on master
- Session ID: 3b9dbe0b-1953-45c5-9c0e-e4c7c3adcf2f

## 6. What's Next

**Segment 1: MCP Server Foundation**
1. Install Python MCP SDK via uv
2. Create `src/server.py` — MCP server entry point
3. Expose `get_context()` as first tool (stub, returns mock profile)
4. Test with Claude Desktop MCP config
5. Clean up old folders (agents/, llm/)
6. Write `learning/01_mcp_tools/README.md`

## 7. Open Questions
- Vector store choice for PoC
- Which onboarding targets are research-validated
- How to test MCP tools (mock client?)
- Distribution model (later)

## 8. User Preferences
- Go SLOW, one concept per step
- PRE-INFO before every action (mandatory)
- Explain WHY before HOW
- Never multiple concepts at once
- Learning > speed
- Worried about context loss — dump everything
- German-speaking, VW Group, technical background
