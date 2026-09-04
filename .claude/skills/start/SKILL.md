---
name: start
description: Resume last session or recover full context from persisted files
---

# /start — Resume or Recover Session Context

When the user invokes this skill, try to get back to full working context as fast as possible.

## Step 1: Check if this IS a continued session

If the conversation already has prior messages about IRIS (i.e., this is `claude --continue`), just say:
"Session continued. We're at [current segment/step]. Ready to proceed?"
And skip everything else.

## Step 1b: If fresh session — suggest resume first

If this appears to be a FRESH session (no prior IRIS conversation context), immediately:

1. Read `.claude/last_session.json`
2. Tell the user:

```
⚠️  This is a fresh session. For full context continuity, exit and run:

    claude --continue

Or resume a specific session:

    claude --resume

Last session: <date> | ID: <session_id>
Segment: <segment> | Next: <next_task>
```

3. Then say: "If you want to stay in this fresh session, I'll recover from the context dump instead."
4. Proceed with Step 2 (file-based recovery) only if the user confirms they want to stay.

## Step 2: If fresh session — recover context

Read these files IN THIS ORDER to rebuild understanding:

1. `.claude/last_session.json` — START HERE. Contains: last date, context dump path, commit hash, current segment, next task. This is your fastest path to orientation.
2. Read the context dump file pointed to by `last_session.json` → `context_dump` field. This has the full mental model, decisions, and state.
3. `CLAUDE.md` — project constitution (should already be auto-loaded, but verify understanding)
4. `ARCHITECTURE.md` — current system state, diagrams, what's built
5. `git log --oneline -5` — see if anything was committed after the last dump

If `.claude/last_session.json` does NOT exist, fall back to:
- Find the LATEST file in `.claude/context_dumps/` (sort by name, pick last)
- Read it fully
- Then read CLAUDE.md and ARCHITECTURE.md

## Step 3: Report back

After reading, present a brief status:

```
═══ IRIS Session Recovered ═══════════════════════════

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
