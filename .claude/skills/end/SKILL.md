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

## Step 3: Confirm

Tell the user:
```
═══ Session Ended ═══════════════════════════════

Context: .claude/context_dumps/<filename>
Commit:  <short hash> — <message summary>
Files:   <count> files committed

To resume: claude --continue
To recover: /start

═══════════════════════════════════════════════════
```

## Rules

- ALWAYS dump context BEFORE committing (so the dump is included in the commit)
- Never push to remote — local commit only
- If there are no changes to commit, skip the commit and say so
- If git is not initialized, skip commit and warn
- Include the context dump file in the commit
