---
name: dump
description: Dump full session context to a file so nothing is lost between conversations
---

# /dump — Session Context Dump

When the user invokes this skill, create a comprehensive context dump file at `.claude/context_dumps/session_<date>.md` (use today's date in YYYY-MM-DD format). If a file for today already exists, append a counter (e.g., `session_2026-07-23_2.md`).

## What to Include

### 1. The Mental Model (between-the-lines understanding)
- How you CURRENTLY understand the project's purpose and philosophy
- The reasoning chain that led to the current architecture (not just the conclusion)
- Any corrections the user made to your understanding — capture the CORRECTED version
- Analogies or mental models that clarify the design ("KIM is like X")
- Subtle distinctions the user emphasized (e.g., "KIM KNOWS things, doesn't DO things")

### 2. Decisions Made This Session
- Architecture decisions, scope changes, design choices
- Include WHY (the reasoning), not just WHAT was decided
- Include what was REJECTED and why (alternatives considered but not chosen)
- The evolution of thinking (if understanding shifted during the session, trace how)

### 3. What Was Built
- Files created or modified (list with one-line description each)
- Current segment and step
- What still needs cleanup from previous approaches

### 4. Key Concepts & Research
- Technical concepts, patterns, or research findings discussed
- For papers: include the actual findings that matter for KIM, not just citations
- For patterns: explain the mechanism (how it works), not just the name
- Design tricks or clever solutions (e.g., the self-check pattern — explain WHY it works)

### 5. Current State
- What segment/step we're on
- What's working vs. what's still a stub
- What files exist vs. what the plan says should exist
- Any discrepancies (old files that need removal, configs that need updating)

### 6. What's Next
- The immediate next task
- Any context needed to pick it up
- Approach agreed upon (so the next session doesn't re-derive it)

### 7. Open Questions
- Unresolved decisions
- Things that need research
- Future scope items mentioned but deferred

### 8. User Preferences (how to work)
- Communication style the user wants
- Pacing preferences
- What to avoid doing
- What the user values in this collaboration

## Rules

- **Dump your actual context** — not a polished summary. Include the messy, implicit understanding.
- Write as if briefing yourself after memory loss — what would you need to be told?
- Include specific details (file paths, function names, data structures)
- If the user corrected you, capture the correction prominently
- If an understanding EVOLVED during the session (started wrong, got corrected), trace the evolution
- Don't organize for readability — organize for completeness
- If you're uncertain about something, say so ("I think X but user might have meant Y")
- Include the WHY behind decisions, not just the WHAT

## After Writing

Tell the user: "Context dumped to `.claude/context_dumps/<filename>`. In a new session, say 'Read .claude/context_dumps/<filename>' to recover full context."
