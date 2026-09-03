---
name: startKim
description: Start KIM onboarding to create user profile for personalized interactions
---

# /startKim — KIM Onboarding

Starts the KIM onboarding flow to create a user profile for personalized LLM interactions.

## What This Does

KIM (Knowledge & Interaction Manager) personalizes your LLM interactions by learning:
- Communication style preferences
- Tone and format preferences
- Professional boundaries
- Work context

This takes ~5 minutes (10 questions).

## Flow

1. Load the onboarding MCP tools (if not already available)
2. Call `start_onboarding(user_id='demo_user')`
3. Present the first question conversationally
4. After each answer:
   - Call `store_answer(answer_text)`
   - Call `get_next_question()`
   - Present next question
5. When questions complete, call `complete_onboarding()`
6. Confirm profile created

## Example Interaction

```
User: /startKim

You: Let's set up your KIM profile! This takes about 5 minutes.

First question: When you ask me to write an email, what tone do you prefer?
- Professional and formal
- Friendly but professional
- Casual and conversational
- Varies by recipient

User: Friendly but professional

You: [stores answer, gets next question...]
```

## Tools Required

Load these MCP tools via ToolSearch:
- `mcp__kim__start_onboarding`
- `mcp__kim__store_answer`
- `mcp__kim__get_next_question`
- `mcp__kim__complete_onboarding`
- `mcp__kim__get_context` (to verify profile after)

## If Profile Already Exists

If onboarding was already completed:
```
Your KIM profile already exists!

To update preferences, you can:
- Use /resetKim to start fresh
- Manually edit: ~/.kim/profiles/demo_user.json
```

## Notes

- User ID is currently hardcoded to 'demo_user'
- Profile stored at: `~/.kim/profiles/demo_user.json`
- Onboarding state persisted between questions
- Can resume if interrupted
