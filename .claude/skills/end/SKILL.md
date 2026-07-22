---
name: end
description: End session — dump context and commit all work to local git
---

# /end — End Session (Dump + Commit)

When the user invokes this skill, perform these steps in order:

## Step 1: Context Dump

Create a comprehensive context dump following the /dump skill rules. Write to `.claude/context_dumps/session_<date>.md` (append counter if exists).

Include ALL sections:
1. Mental model (between-the-lines understanding)
2. Decisions made this session
3. What was built
4. Key concepts & research
5. Current state
6. What's next
7. Open questions
8. User preferences

## Step 2: Git Commit

After the dump is written:

1. Run `git status` to see what's changed
2. Run `git add` for all relevant project files (NOT .env, NOT secrets)
3. Create a commit with a message summarizing the session's work:

Format:
```
segment X: <what was accomplished>

- <bullet points of key changes>
- <files added/modified>

Session: <date>

```

## Step 3: Write Session Pointer

After committing, write the current session info to `.claude/last_session.json`:

```json
{
  "date": "<today's date>",
  "session_id": "<get from env var CLAUDE_CODE_SESSION_ID via Bash: echo $CLAUDE_CODE_SESSION_ID>",
  "context_dump": ".claude/context_dumps/<filename>",
  "commit_hash": "<short hash>",
  "commit_message": "<message summary>",
  "segment": "<current segment number and name>",
  "next_task": "<what's immediately next>"
}
```

To get the session ID, run: `echo $CLAUDE_CODE_SESSION_ID`

This file lets `/start` know exactly where to pick up AND which session to try `--resume` with. Include this file in the commit (run a quick `git add` + `git commit --amend` to include it, or add it before the main commit).

## Step 4: Confirm

Tell the user:
```
═══ Session Ended ═══════════════════════════════

Context: .claude/context_dumps/<filename>
Commit:  <short hash> — <message summary>
Files:   <count> files committed
Session pointer: .claude/last_session.json

To resume: claude --continue
To recover: /start

═══════════════════════════════════════════════════
```

## Rules

- ALWAYS dump context BEFORE committing (so the dump is included in the commit)
- ALWAYS write last_session.json (so /start can find the latest context)
- Never push to remote — local commit only
- If there are no changes to commit, skip the commit and say so
- If git is not initialized, skip commit and warn
- Include the context dump file AND last_session.json in the commit
