# Status Skill

When invoked, explain KIM's current build state: what exists, what's next, and why.

## Instructions

1. **Read current state:**
   - Check `ARCHITECTURE.md` → "Current State" section shows completed segments
   - Check memory `project_segment0-progress.md` for step-level details
   - Scan project structure to verify what actually exists

2. **Present status in this format:**

   ```
   ## KIM Build Status — <Current Date>
   
   **Current Segment:** <Number and name>
   **Progress:** <What's complete> ✅ | <What's next> ⏳
   
   ### What Exists Now
   - <List actual implemented components>
   
   ### What's Next
   - <Next step with brief rationale>
   
   ### Why This Order
   <One paragraph explaining why the current step comes before later ones>
   
   ### Quick Context
   <2-3 sentences: What KIM is, what it will do when complete>
   ```

3. **Be specific:**
   - Don't just list segment numbers — explain what each means architecturally
   - If files exist but are stubs, say so
   - If a concept is planned but not built, mark it clearly

4. **Keep it concise:** The user wants orientation, not a full design doc review. 3-5 sentences per section.

## Example Output

```
## KIM Build Status — 2026-07-22

**Current Segment:** Segment 0 (Project Skeleton) — Complete ✅
**Next:** Segment 1 (LLM Abstraction Layer) ⏳

### What Exists Now
- CLAUDE.md hierarchy with learning modules
- Project skeleton: pyproject.toml, folder structure, config/settings.yaml
- Three hooks: preflight_explainer, architect_radar, progress_tracker
- ARCHITECTURE.md with scenario diagrams and data flow
- /status skill (this one!)

### What's Next
Segment 1 will build the LLM abstraction layer — a unified interface for both Ollama (local) and Claude Bedrock (cloud). This lets the router switch models without changing calling code.

### Why This Order
We need the abstraction layer before building agents because the Coordinator/Operator/Validator/Generator will all make LLM calls. Building it first means we write those agents once, not twice (once per provider).

### Quick Context
KIM is a multi-agent communication assistant for VW Group that learns user preferences through GATE onboarding and adapts over time. It orchestrates Ollama + Claude Bedrock with a four-agent pipeline (Coordinator → Operator → Validator → Generator) backed by three-tier memory (STM/Summary/LTM).
```

## When NOT to use this skill

Don't invoke `/status` when:
- The user is asking about a specific technical detail (answer directly)
- The user wants to change direction (discuss, don't report status)
- You're mid-implementation (finish the step first, then status makes sense)

Use it when:
- Conversation starts and you need to orient
- User explicitly asks "where are we"
- You've just completed a segment and want to summarize progress
