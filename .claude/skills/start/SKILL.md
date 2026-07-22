---
name: start
description: Resume last session or recover full context from persisted files
---

# /start — Resume or Recover Session Context

When the user invokes this skill, try to get back to full working context as fast as possible.

## Step 1: Check if this IS a continued session

If the conversation already has prior messages (i.e., this is `claude --continue`), just say:
"Session continued. We're at [current segment/step]. Ready to proceed?"
And skip everything else.

## Step 2: If fresh session — recover context

Read these files IN THIS ORDER to rebuild understanding:

1. `CLAUDE.md` — project constitution (should already be auto-loaded, but verify understanding)
2. `ARCHITECTURE.md` — current system state, diagrams, what's built
3. Check memory files (auto-loaded) — preferences, scope, architecture decisions
4. Find the LATEST file in `.claude/context_dumps/` — read it fully for detailed session knowledge
5. `git log --oneline -10` — see what was committed recently

## Step 3: Report back

After reading, present a brief status:

```
═══ KIM Session Recovered ═══════════════════════════

Last session: <date from dump file>
Segment:      <current segment and step>
Last worked on: <what was built/discussed>
Next task:    <what's immediately next>

Context confidence: <high/medium/low>
  - <note any gaps or uncertainties>

════════════════════════════════════════════════════════
```

## Step 4: If context seems incomplete

If the dump file is old or missing, say:
"Context may be stale. Want me to scan the project files to rebuild understanding, or do you want to brief me?"

## Rules

- Never pretend to have context you don't have
- If uncertain about something, say so explicitly
- Don't ask the user to re-explain things that are in the dump file
- Be brief — the user wants to get back to work, not read a status report
