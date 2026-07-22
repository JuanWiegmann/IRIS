# Full Context Dump — Session 2026-07-22 (End of Session)

## 1. Mental Model

### What KIM IS
KIM is a "personality card" that follows you across all LLMs. It's invisible middleware — an MCP server that any LLM connects to. It doesn't DO anything for the user. It only KNOWS things about the user and shares that knowledge with whatever LLM the user is talking to.

When the user asks Claude to write an email, Claude calls KIM: "How should I present this to this user?" KIM responds with profile + relevant examples + style rules. Claude then generates the email using that context. KIM never touches the email itself.

### The Architecture (evolved during this session)
Started as: "multi-agent system with local Ollama + Bedrock Claude"
Evolved to: "pure MCP server, no LLM inside, user's LLM does everything"

The shift happened because:
- Why run a local LLM when the user's LLM is right there and more powerful?
- Why build internal agents when the user's LLM can follow instructions (Anleitung)?
- KIM should be zero-install: just connect MCP, done.

### The Self-Check Trick
`check_draft` is the clever pattern. When the LLM writes an email and calls `check_draft`, it THINKS it's asking an external expert. But KIM just compares the draft against stored profile rules. The LLM gets independent feedback it couldn't give itself (because you can't judge your own work in the same context window). Deterministic, no LLM needed inside KIM.

### The Onboarding Philosophy
KIM defines research-backed TARGETS (what to learn). Each target has a BARRIER (minimum evidence). The LLM sees open targets and FREELY decides strategy (edge-case question, binary, direct ask, observation). KIM never dictates HOW to ask — only WHAT needs to be known.

Example target: "response_format" — barrier: "user must have explicitly chosen between concise vs detailed in at least one interaction"

### Why User Outputs > Inputs (Wu et al. 2024)
Counterintuitive but proven: what the user WROTE/CHOSE/APPROVED drives personalization. Not what they asked. Store past emails sent, versions picked, corrections made. Serve them ranked by relevance to current query. Most relevant first (position matters).

### Two Layers
- Layer 1: Any MCP client. Tools + Anleitung (instructions in tool descriptions). LLM follows protocol.
- Layer 2: Advanced clients (Claude). MCP sampling — KIM orchestrates with fresh context per step. Better isolation.

### Scope
Personalization + light cross-session memory. NOT task execution, NOT workflow orchestration, NOT tool integration. KIM answers "how should I talk to this person" — never "do this for the person."

Light memory = "user works on Skillfinder project, recently escalated API-key issue" (cross-LLM, cross-session context).

## 2. Decisions Made This Session

| Decision | Why | Rejected Alternative |
|----------|-----|---------------------|
| KIM = MCP server, no internal LLM | User's LLM is more powerful, zero install | Multi-agent with Ollama |
| User's LLM does ALL reasoning | Best quality comes from the main model | KIM generates responses internally |
| check_draft as blind validator | Independent feedback LLM can't give itself | LLM self-validates (unreliable) |
| Research-based onboarding targets | Scientific backing for what to collect | Arbitrary preference questions |
| Tools start broad, split later | Can't predict usage patterns upfront | Design all tools upfront |
| Two layers (tools vs sampling) | Maximum compatibility + advanced option | One approach only |
| Personalization + memory scope ONLY | Clear boundary prevents scope creep | Full Workday orchestrator |
| PRE-INFO on every action | User wants full transparency on operations | Silent tool calls |
| /start, /end, /dump skills | Session persistence and recovery | Manual context management |
| LaTeX diagrams for architecture | High quality, version controlled | Mermaid only |
| Mermaid in ARCHITECTURE.md | In-repo, auto-renders in VS Code | LaTeX only (needs compiler) |

## 3. What Was Built

### Segment 0 (COMPLETE):

```
CLAUDE.md                          — Project constitution (updated to MCP architecture + scope + PRE-INFO rule)
src/CLAUDE.md                      — Code conventions (no LLM inside rule)
learning/CLAUDE.md                 — Learning format rules (WHY→WHAT→HOW→THINK ABOUT)
tests/CLAUDE.md                    — Test philosophy (behavior not implementation)
pyproject.toml                     — uv, Python 3.11+, pydantic, pytest, ruff
config/settings.yaml               — LLM endpoints (NEEDS UPDATE for MCP-only arch)
.gitignore                         — Standard Python + .env + .claude/settings.local.json
ARCHITECTURE.md                    — Mermaid diagrams with color-coded build status
ONBOARDING_GATE_DESIGN.md          — Original design doc (pre-dates current architecture)

.claude/settings.json              — Hook config (preflight on .*, postToolUse on Edit|Write)
.claude/hooks/preflight_explainer.py — PRE-INFO hook, fires on ALL tools
.claude/hooks/architect_radar.py   — PostToolUse, detects certification topics
.claude/hooks/progress_tracker.py  — PostToolUse, detects segment completion
.claude/skills/start/SKILL.md      — /start skill (resume or recover)
.claude/skills/end/SKILL.md        — /end skill (dump + commit)
.claude/skills/dump/SKILL.md       — /dump skill (context dump only)
.claude/skills/status/SKILL.md     — /status skill (show build state)

learning/00_setup/README.md        — Module 0: persistence architecture explained
docs/diagrams/kim_system_logic.tex — Full LaTeX system diagram
docs/diagrams/kim_logic_v6.pdf     — Compiled PDF (current version)
docs/onboarding_targets_checklist.md — Research TODOs + preliminary targets

tests/unit/test_example.py         — Placeholder test
```

### What Needs Cleanup
- `src/agents/` — empty, from old architecture (can remove in Segment 1)
- `src/llm/` — empty, from old architecture (can remove in Segment 1)
- `src/api/` — might keep for later, or replace with MCP server
- `src/guardrails/` — keep, still relevant for validation
- `config/settings.yaml` — still references Ollama/Bedrock, needs MCP-only rewrite

## 4. Key Research Findings

### GATE (Li et al., ICLR 2025)
- LLM interviews users via edge-cases, binary, open questions
- Forced choices reveal tacit knowledge users can't articulate
- 5-minute window is optimal
- Open-ended questions actually DECREASED performance in technical domains
- Works with open-source models (Mixtral matched GPT-4)

### Wu et al. 2024 (arXiv 2406.17803)
- User OUTPUTS are primary personalization driver (not inputs)
- Output-only format fits 2-5x more examples in context
- Most-relevant-first ordering significantly improves quality
- Semantic similarity from NON-user sources HURTS performance
- Correct input-output pairing is NOT necessary (surprising)
- Random sampling is worst strategy
- Profile position matters: earlier = more influence

### Westhaeusser et al. 2025 (arXiv 2510.07925)
- Four-agent pipeline: Coordinator → Operator → Validator → Generator
- Multi-tiered memory: STM (recent), Summaries (compressed), LTM (embeddings)
- Dynamic user profile built implicitly from interactions
- 96% retrieval accuracy vs 87% RAG baseline
- Removing user profile reduced accuracy by 5.6%
- MCP protocol for tool/resource access

## 5. Current State

- **Segment 0:** COMPLETE
- **Segment 1:** NOT STARTED (MCP Server Foundation)
- **Git:** Initialized, NO commits yet
- **MiKTeX:** Installed (for LaTeX diagram compilation)
- **Python/uv:** Not yet verified (need to check in Segment 1)
- **Hooks:** All 3 working (preflight, radar, progress tracker)
- **Skills:** Restructured to correct format (subdirectory/SKILL.md)

## 6. What's Next (Segment 1: MCP Server Foundation)

Build the actual MCP server:
1. Install Python MCP SDK via uv
2. Create `src/server.py` — MCP server entry point
3. Define and expose `get_context()` as first tool (stub returning mock profile)
4. Test with a real MCP client (Claude Desktop config)
5. Write `learning/01_mcp_tools/README.md`
6. Clean up old folders (src/agents/, src/llm/)

Approach: Start minimal — one tool, verify the full MCP round-trip works, then add tools.

## 7. Open Questions

- Vector store choice (ChromaDB vs simpler for PoC)
- Which exact onboarding targets are research-validated (needs per-paper deep-dive)
- How to handle profile conflicts (user said X but behaves Y)
- Distribution model (PyPI, Docker, internal)
- Data portability (export/import profiles)
- How to test MCP tools without a full client (mock client? test harness?)

## 8. User Preferences

- Go SLOW. One concept per step. Explain before building.
- PRE-INFO on every action (mandatory, visible in text output)
- Show WHY before HOW. Frame as decision points.
- Never implement multiple concepts at once
- The project is for learning — understanding > shipping speed
- User wants to develop INTUITION for when to use modern tools (hooks, skills, agents, workflows)
- User is concerned about context loss between sessions — dump everything
- German-speaking user, technical background, works at VW Group
