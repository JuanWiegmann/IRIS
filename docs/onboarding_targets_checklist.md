# Onboarding Targets — Research Checklist

## Purpose

This checklist defines the **minimum research-backed targets** KIM must satisfy during onboarding to be effective as a personalization middleware. Each target has a scientific basis, a barrier (what counts as "satisfied"), and a usage description (how it improves LLM responses later).

**Design principle:** KIM provides targets + validation. The LLM freely decides HOW to reach each target. KIM only checks if the barrier is met.

---

## TODO: Research & Design Phase

- [ ] Deep-dive Wu et al. 2024 — extract exact dimensions that drive personalization quality
- [ ] Deep-dive GATE (Li et al. 2025) — which question types satisfy which target types best
- [ ] Deep-dive Westhaeusser et al. 2025 — what profile fields had measurable impact
- [ ] Define minimum viable profile (fewest targets that still meaningfully improve responses)
- [ ] Define barrier types (binary declaration, observed behavior, forced-choice, minimum evidence count)
- [ ] Define confidence thresholds (when is a target "satisfied enough" to use)
- [ ] Design target schema (YAML/JSON structure per target)
- [ ] Map targets to research papers (every target must cite why it exists)

---

## TODO: Implementation Phase

- [ ] Implement target store (list of targets + satisfaction status)
- [ ] Implement `get_targets()` MCP tool — returns open/unsatisfied targets to LLM
- [ ] Implement `check_satisfied(target, evidence)` — validates if barrier is met
- [ ] Implement `store_insight(target, value, confidence)` — saves learned info
- [ ] Implement progress tracking (% of minimum viable profile complete)
- [ ] Implement target priority logic (which target to pursue next, given what's known)
- [ ] Design the Anleitung section that teaches the LLM how to use these tools

---

## Preliminary Target Dimensions (to be validated by research)

| # | Target | Research Basis | Barrier Type | Usage in get_context() |
|---|--------|---------------|--------------|----------------------|
| 1 | Response format | Wu 2024: output style is primary personalization driver | Binary: short vs. detailed vs. reasoned | "User wants: [format]" |
| 2 | Tone/formality | GATE: forced-choice reveals tacit tone preference | Observed: 2+ examples or 1 explicit | "Respond in tone: [tone]" |
| 3 | Language | Basic requirement | Explicit declaration | "Respond in: [language]" |
| 4 | Domain context | Wu 2024: relevance retrieval needs domain knowledge | Minimum: role + 1 active project | "User works on: [context]" |
| 5 | Communication boundaries | Westhaeusser: time/channel preferences measurably impact UX | At least 1 explicit boundary | "Do not: [boundary]" |
| 6 | Decision style | GATE: edge-cases reveal priority hierarchies | 1 observed conflict resolution | "User prioritizes: [value]" |
| 7 | Proactivity preference | Westhaeusser: user control over AI initiative | Binary: suggest vs. ask first | "Proactivity level: [level]" |
| 8 | Correction style | Wu 2024: past corrections are high-value personalization data | First natural correction captured | Feed into check_draft logic |

---

## Target Schema (draft — to be finalized during implementation)

```yaml
target:
  id: "response_format"
  dimension: "How the user wants to receive information"
  research_basis:
    paper: "Wu et al. 2024"
    finding: "User output style is the dominant driver of personalization quality"
  barrier:
    type: "binary"  # binary | observed | threshold
    condition: "User has explicitly stated format preference OR chosen between 2+ examples"
    minimum_evidence: 1
  satisfied: false
  confidence: 0.0
  evidence: []
  usage:
    context_injection: "User wants responses in: {value}"
    check_draft_rule: "Response length should match: {value}"
```

---

## Open Questions (for later)

- How many targets is enough? (minimum viable vs. comprehensive)
- Should targets have priorities? (some more important than others)
- How to handle conflicting evidence? (user said X but behaves like Y)
- Should targets evolve over time? (re-validate periodically)
- How to handle context-dependent targets? (formal with boss, casual with peers)
