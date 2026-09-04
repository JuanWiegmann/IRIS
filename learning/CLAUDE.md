# Learning Materials Conventions

## Structure Per Module

Each `learning/XX_topic/` folder contains:
- `README.md` — Concept explanation, architecture rationale, diagrams
- `exercises.md` — Hands-on challenges (extend, modify, break things)
- Optional: code snippets or minimal examples that isolate the pattern

## Writing Style

- Start with the "WHY" (what problem does this pattern solve?)
- Then the "WHAT" (the pattern itself, with a diagram)
- Then the "HOW" (pointer to the actual implementation in `src/`)
- End with "THINK ABOUT" (questions that deepen understanding)

## Certification Mapping

Every module maps to a Claude Certified Architect topic. State the mapping explicitly at the top:
```
Certification Topic: Agentic Loops & Tool Use
Relevant Exam Areas: Tool schemas, function calling, loop termination
```

## Language

Write in English. Code examples use the actual IRIS codebase (not synthetic examples).
