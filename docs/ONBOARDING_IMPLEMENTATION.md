# KIM Onboarding Implementation Guide

**Status:** ✅ Implemented (Segment 5)  
**Research Basis:** GATE (Li et al. 2023), Wu et al. 2024, Westhaeusser et al. 2025

---

## Overview

KIM uses **adaptive preference elicitation** to learn user preferences with minimal questions (8-10 instead of 25-30). The onboarding is conducted entirely by the user's LLM — KIM provides research-backed guidance and validates barriers.

### Key Research Findings

- **GATE (Li et al. 2023):** Edge-case questions outperform open questions in 60% of settings
- **Wu et al. 2024:** User outputs (not inputs) are primary personalization driver
- **Westhaeusser et al. 2025:** 5-7 strategic questions capture essentials; learned preferences have 18-22% higher alignment than stated

---

## Adaptive Question Flow

### Phase 1: Anchor Questions (Determine Context)

**Q1: Role** — "What do you do for work?"
- **Purpose:** Establishes professional domain
- **Time:** ~30 seconds
- **Output:** Used to detect profile type

**Q2: AI Usage** — "What do you use AI for?"
- **Purpose:** Establishes intent (coding, communication, architecture)
- **Time:** ~30 seconds
- **Output:** Triggers adaptive question selection

### Phase 2: Profile Detection

Based on Q1 + Q2 answers, KIM detects one of four profile types:

| Profile Type | Triggers When | Question Path |
|--------------|--------------|---------------|
| **CODE_HEAVY** | Role: developer, Usage: code/debug | Technical depth, code style, error handling |
| **COMMUNICATION_HEAVY** | Role: lead/manager, Usage: docs/emails | Communication formality, explanation depth, doc style |
| **ARCHITECTURE** | Role: architect, Usage: design decisions | Decision support, technical breadth |
| **GENERAL** | None of above | Universal questions only |

### Phase 3: Contextual Questions (5-8 questions)

Selected based on profile type. Examples:

**For Code-Heavy:**
- Technical detail level (edge-case: high-level vs. detailed)
- Code documentation style (edge-case: minimal vs. documented)
- Error handling approach (binary: solution-first vs. debug-process)

**For Communication-Heavy:**
- Communication formality (edge-case: direct vs. contextual)
- Explanation depth (edge-case: business-focused vs. technical)
- Documentation style (binary: concise vs. comprehensive)

**For Architecture:**
- Decision support (binary: recommendation vs. options)
- Technical breadth (edge-case: focused vs. comprehensive)

### Phase 4: Universal Questions (Always Asked)

- **Language** (binary: de/en/both)
- **Current focus** (open: projects/topics)
- **Learning approach** (binary: example-first vs. concept-first)
- **Proactivity** (binary: suggest vs. ask-only)
- **Privacy** (binary: store context vs. preferences-only vs. none)

**Total Questions:** 8-10 (varies by profile type)  
**Total Time:** 4-6 minutes

---

## MCP Tools for Onboarding

### 1. `start_onboarding(user_id)`

Starts onboarding flow and returns Q1.

**Request:**
```json
{
  "user_id": "demo_user"
}
```

**Response:**
```json
{
  "session_id": "onb_abc123",
  "status": "started",
  "message": "Onboarding started. This takes ~5 minutes...",
  "question": {
    "target_id": "role",
    "dimension": "Professional Role & Responsibilities",
    "question_text": "What do you do for work?",
    "question_type": "open",
    "example_prompt": "Examples: 'Backend Developer', 'Team Lead', 'Solution Architect'"
  },
  "guidance": "This is Q1 of 2 anchor questions..."
}
```

---

### 2. `store_answer(user_id, target_id, answer)`

Stores user's answer and returns next question.

**Request (for Q1 - role):**
```json
{
  "user_id": "demo_user",
  "target_id": "role",
  "answer": {
    "answer": "Backend Developer"
  }
}
```

**Response:**
```json
{
  "status": "recorded",
  "message": "Role recorded. Now let's understand how you use AI.",
  "barrier_met": true,
  "next_question": {
    "target_id": "ai_usage",
    "dimension": "AI Usage Context",
    "question_text": "What do you use AI for?",
    "question_type": "example_guided",
    "example_prompt": "Examples: 'Writing code', 'Explaining concepts'..."
  }
}
```

**Request (for Q2 - ai_usage):**
```json
{
  "user_id": "demo_user",
  "target_id": "ai_usage",
  "answer": {
    "answer": "Writing and reviewing code, debugging issues"
  }
}
```

**Response (profile type detected):**
```json
{
  "status": "profile_type_detected",
  "message": "Profile type: code_heavy. Selected 8 relevant questions.",
  "profile_type": "code_heavy",
  "questions_selected": 8,
  "next_question": {
    "target_id": "technical_depth",
    "dimension": "Technical Detail Level",
    "question_text": "Your colleague asks: 'How should we implement caching?' Which response helps you more?",
    "question_type": "edge_case",
    "options": [
      {
        "label": "Version A (Executive Summary)",
        "value": "high_level",
        "example_content": "Use Redis with 1h TTL. Reduces DB load by ~70%. Implementation: 2-3 days."
      },
      {
        "label": "Version B (Technical Deep-Dive)",
        "value": "detailed",
        "example_content": "**Recommended Approach:**\nRedis-based caching layer...\n[full detailed response]"
      }
    ],
    "research_basis": "Wu 2024: Response format is primary driver of quality",
    "guidance": "GATE research: Edge-case questions outperform open questions in 60% of settings..."
  }
}
```

**Request (edge-case question):**
```json
{
  "user_id": "demo_user",
  "target_id": "technical_depth",
  "answer": {
    "chosen_option": "detailed"
  }
}
```

**Response:**
```json
{
  "status": "recorded",
  "validation_result": {
    "dimension": "Technical Detail Level",
    "barrier_met": true,
    "confidence": 0.5,
    "evidence_count": 1,
    "inferred_preferences": {
      "detail_level": "comprehensive",
      "structure": "structured",
      "examples": true
    }
  },
  "should_continue": true,
  "next_question": { ... },
  "session_progress": {
    "questions_asked": 3,
    "questions_remaining": 6,
    "core_satisfaction_rate": 0.33
  }
}
```

---

### 3. `get_next_question(user_id)`

Gets next question without storing an answer (useful for resume).

**Request:**
```json
{
  "user_id": "demo_user"
}
```

**Response:**
```json
{
  "target_id": "code_documentation_style",
  "dimension": "Code Documentation Preference",
  "question_text": "When I show code examples, which style fits your workflow?",
  ...
}
```

---

### 4. `complete_onboarding(user_id)`

Completes onboarding and generates profile.

**Request:**
```json
{
  "user_id": "demo_user"
}
```

**Response:**
```json
{
  "status": "completed",
  "session_id": "onb_abc123",
  "questions_answered": 8,
  "core_satisfaction_rate": 1.0,
  "satisfied_dimensions": [
    "Professional Role & Responsibilities",
    "Technical Detail Level",
    "Code Documentation Preference",
    "Response Language",
    "Current Projects/Focus Areas",
    "Learning/Explanation Approach",
    "Proactivity Preference",
    "Privacy & Storage Boundaries"
  ],
  "profile_type": "code_heavy",
  "message": "Onboarding complete! Your profile will be used to personalize responses."
}
```

---

## How LLMs Should Use These Tools

### Step-by-Step Flow

1. **Start:** Call `start_onboarding(user_id)`
2. **Q1 (role):** Present question to user, get answer
3. **Store Q1:** Call `store_answer(user_id, "role", {answer: "..."})`
4. **Q2 (ai_usage):** Present returned question, get answer
5. **Store Q2:** Call `store_answer(user_id, "ai_usage", {answer: "..."})`
   - KIM detects profile type and selects questions
6. **Loop for remaining questions:**
   - Present `next_question` from response
   - Get user's answer
   - Call `store_answer(user_id, target_id, {chosen_option: "..."})` or `{answer: "..."}`
   - Check `should_continue` in response
7. **Complete:** Call `complete_onboarding(user_id)` when done

### Example Conversation

```
LLM: Let's set up your profile to personalize my responses. This takes about 5 minutes. 
     What do you do for work?

User: I'm a backend developer working with Python and FastAPI.

[LLM calls store_answer("user123", "role", {answer: "Backend developer - Python/FastAPI"})]

LLM: Great! And what do you use AI for?

User: Mainly for writing code and debugging issues.

[LLM calls store_answer("user123", "ai_usage", {answer: "Writing code and debugging"})]
[KIM detects: CODE_HEAVY profile, selects technical questions]

LLM: Perfect! I've selected 8 questions relevant to developers. Here's the first:
     
     Your colleague asks "How should we implement caching?" Which response helps you more?
     
     A) Use Redis with 1h TTL. Reduces DB load by ~70%. Implementation: 2-3 days.
     
     B) [Shows detailed technical response with architecture, code examples, etc.]

User: B

[LLM calls store_answer("user123", "technical_depth", {chosen_option: "detailed"})]

[... continues for 6 more questions ...]

LLM: All done! I've learned your preferences. From now on, I'll provide detailed technical 
     responses with code examples, matching your work style.
```

---

## Information Pool Structure

KIM provides rich context to guide the LLM:

### Before Each Question

```json
{
  "session_progress": {
    "questions_asked": 3,
    "questions_remaining": 5,
    "core_satisfaction_rate": 0.66,
    "satisfied_dimensions": ["role", "ai_usage", "technical_depth"],
    "profile_type": "code_heavy"
  },
  "next_target": {
    "id": "code_documentation_style",
    "dimension": "Code Documentation Preference",
    "research_basis": "GATE: Concrete examples reveal preferences users can't articulate",
    "priority": 3,
    "question_template": { ... }
  },
  "recommended_strategy": "GATE research: Edge-case questions outperform open questions...",
  "should_continue": true
}
```

### After Each Answer

```json
{
  "validation_result": {
    "dimension": "Technical Detail Level",
    "barrier_met": true,
    "confidence": 0.5,
    "inferred_preferences": {
      "detail_level": "comprehensive",
      "structure": "structured"
    }
  },
  "should_continue": true,
  "session_progress": { ... }
}
```

---

## Barriers & Satisfaction

Each target has a **barrier** that defines when it's "satisfied":

| Barrier Type | Criteria | Example |
|--------------|----------|---------|
| **EDGE_CASE_CHOICE** | User chose between concrete examples | Technical depth: chose "detailed" |
| **BINARY_ANSWER** | User answered yes/no or A/B | Proactivity: chose "proactive" |
| **EXPLICIT_STATEMENT** | User directly stated something | Role: "Backend Developer" |
| **MINIMUM_EVIDENCE** | N pieces of evidence collected | (Future: multi-step validation) |
| **CONFIDENCE_THRESHOLD** | Confidence score >= X | (Future: learned from behavior) |

**Core Questions** (priority 1-3) must reach 80% satisfaction before completing.

---

## Storage

Sessions stored in: `~/.kim/onboarding/{user_id}/`

- **`active_session.json`** — Current in-progress session
- **`{session_id}.json`** — Completed sessions (history)
- **`latest.json`** — Most recent session

Structure:
```json
{
  "user_id": "demo_user",
  "session_id": "onb_abc123",
  "started_at": "2026-09-02T10:00:00Z",
  "completed_at": null,
  "role": "Backend Developer",
  "ai_usage": "Writing code and debugging",
  "profile_type": "code_heavy",
  "targets": {
    "technical_depth": {
      "satisfied": true,
      "confidence": 0.5,
      "evidence": [...]
    }
  },
  "questions_asked": 5,
  "questions_remaining": ["language", "proactivity", "privacy"]
}
```

---

## Profile Generation

After `complete_onboarding()`, KIM generates a `UserProfile`:

```json
{
  "user_id": "demo_user",
  "language": "en",
  "tone": "professional",
  "format_preference": {
    "detail_level": "comprehensive",
    "include_examples": true,
    "structure": "structured",
    "example_first": true
  },
  "boundaries": [
    {
      "type": "privacy",
      "description": "Store preferences only, no project details"
    },
    {
      "type": "proactivity",
      "description": "Proactive suggestions welcome"
    }
  ],
  "confidence": 0.85
}
```

This profile is then used by `get_context()` to personalize all future responses.

---

## Testing Onboarding

### Manual Test (MCP Inspector)

1. Start server: `uv run python -m src.server`
2. Connect MCP inspector
3. Call tools in sequence:

```javascript
// 1. Start
start_onboarding({user_id: "test_user"})

// 2. Answer Q1
store_answer({
  user_id: "test_user",
  target_id: "role",
  answer: {answer: "Backend Developer"}
})

// 3. Answer Q2
store_answer({
  user_id: "test_user",
  target_id: "ai_usage",
  answer: {answer: "Writing code"}
})

// 4. Continue with remaining questions...

// 5. Complete
complete_onboarding({user_id: "test_user"})
```

### Inspect Session State

```bash
cat ~/.kim/onboarding/test_user/active_session.json | jq
```

---

## Research Citations

1. **Li, B., Tamkin, A., Goodman, N., Andreas, J. (2023)**  
   "Eliciting Human Preferences with Language Models" (arXiv:2310.11589)  
   *GATE methodology: Edge-case questions reveal tacit preferences*

2. **Wu, T., Shi, Y., Rahmani, H., Ramineni, K., Yilmaz, E. (2024)**  
   "The Role of User Profiles in Personalized Language Model Responses" (arXiv:2406.17803)  
   *User outputs are primary driver of personalization quality*

3. **Westhaeusser, A., Minker, S., Zepf, M. (2025)**  
   "Multi-Agent Personalization with Persistent Memory" (arXiv:2510.07925)  
   *5-7 strategic questions capture essentials; learned > stated preferences*

---

**Implementation Status:** ✅ Complete  
**Next Steps:** Test with real LLM, measure question efficiency, track user satisfaction
