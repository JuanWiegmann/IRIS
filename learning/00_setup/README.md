# Module 00: Project Setup & Context Persistence

**Certification Topic:** Development Environment, Tooling, Project Architecture
**Relevant Exam Areas:** Claude Code hooks, skills, CLAUDE.md, MCP basics

---

## WHY — What Problem Does This Solve?

AI-assisted development suffers from **context amnesia** — every new conversation starts blank. Design decisions, architectural principles, and coding conventions get lost between sessions.

This module covers the persistence architecture that ensures:
- No conversation ever forgets what KIM is or how to work on it
- Code changes automatically trigger learning opportunities
- Progress is visually tracked without manual effort

---

## WHAT — The Persistence Architecture

### Three Layers of Automatic Context

| Layer | Mechanism | Loads When |
|-------|-----------|------------|
| **CLAUDE.md hierarchy** | Files at project root + subfolders | Every conversation, automatically |
| **Memory files** | `.claude/projects/.../memory/` | Every conversation, index always loaded |
| **Hooks** | `.claude/settings.json` | Fire on events (Edit, Write), no user action |

### CLAUDE.md Hierarchy

```
CLAUDE.md          → "What is this project?" (constitution)
src/CLAUDE.md      → "How do we write code here?" (conventions)
learning/CLAUDE.md → "How do we write learning materials?" (format)
tests/CLAUDE.md    → "How do we test?" (philosophy)
```

Each file is scoped — `src/CLAUDE.md` only loads when working in `src/`.

### Hooks (Automatic Behavior)

Three hooks fire without user action:

1. **Pre-flight Explainer** (`PreToolUse` on Edit|Write)
   - Fires BEFORE code is written
   - Explains what's about to be built and its role in the system
   - Uses file path + content patterns to determine context

2. **Architect Radar** (`PostToolUse` on Edit|Write)
   - Fires AFTER code is written
   - Detects certification-relevant patterns (regex-based)
   - Surfaces links to relevant learning modules

3. **Progress Tracker** (`PostToolUse` on Edit|Write to CLAUDE.md)
   - Fires when segment checkboxes change
   - Reminds to update ARCHITECTURE.md

### Skills (On-Demand)

- `/status` — Shows current build state, what exists, what's next

---

## HOW — Implementation Details

### Hook Configuration (`.claude/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Edit|Write", "hooks": [...]}],
    "PostToolUse": [{"matcher": "Edit|Write", "hooks": [...]}]
  }
}
```

Hooks receive JSON on stdin with:
- `tool_name` — which tool was called
- `tool_input.file_path` — what file is being modified
- `tool_input.content` / `tool_input.new_string` — the content

Hooks output JSON to stdout:
- `continue: true` — don't block the operation
- `hookSpecificOutput.additionalContext` — message injected into session

### Pattern Detection (Architect Radar)

The radar uses regex patterns mapped to certification topics:

```python
TOPIC_RULES = [
    {"patterns": [r"class.*Agent", r"def invoke"],
     "topic": "Agentic Loops", "module": "learning/01_..."},
    ...
]
```

This is intentionally simple — regex, not AST analysis. It catches ~80% of relevant changes with near-zero latency.

---

## THINK ABOUT

1. **Why regex instead of AST parsing for the Architect Radar?**
   - Speed (must complete in <10s timeout)
   - Good enough for pattern detection (we're flagging topics, not analyzing code)
   - AST would break on incomplete code during editing

2. **Why separate CLAUDE.md files per folder instead of one big file?**
   - Scoping: test conventions don't pollute code editing context
   - Maintenance: each team/concern owns their own rules
   - Token efficiency: only relevant rules load

3. **Could the hooks become too noisy?**
   - Yes — the Architect Radar skips learning/ and config files
   - The Pre-flight only fires on project source files
   - If noise becomes a problem: add frequency limiting

4. **What's the difference between CLAUDE.md and Memory?**
   - CLAUDE.md = stable project truth (changes rarely)
   - Memory = evolving understanding of user + project state
   - Both load automatically, but serve different purposes

---

## Files Created in This Module

```
.claude/settings.json           — Hook configuration
.claude/hooks/preflight_explainer.py  — Pre-flight explanation
.claude/hooks/architect_radar.py      — Learning detection
.claude/hooks/progress_tracker.py     — Progress tracking
.claude/skills/status.md              — /status skill
CLAUDE.md                             — Project constitution
src/CLAUDE.md                         — Code conventions
learning/CLAUDE.md                    — Learning format rules
tests/CLAUDE.md                       — Test philosophy
ARCHITECTURE.md                       — Living visual diagrams
```
