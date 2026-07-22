# KIM Onboarding Design — GATE Methodology Integration

**Based on:** Li, Tamkin, Goodman, Andreas (2023), *"Eliciting Human Preferences with Language Models"* (arXiv:2310.11589)

---

## Core Insight

**Don't ask:** "Wie ist dein Kommunikationsstil?"

**Instead ask:** "Hier sind zwei Versionen derselben Mail an deinen Teamlead. Welche würdest du abschicken?"

---

## Why Edge Cases Beat Open Questions

### Research Evidence

- **Forced choices improved performance** in 6/10 settings (absolute), 7/10 (AUC)
- **Open-ended questions actually decreased performance** in technical domains (email validation)
- **Users can't introspect preferences** — One participant said emails must end in ".com or .co.uk" but later accepted ".edu"
- **Reduced cognitive load** — Binary questions rated equally/less demanding than open prompts

### Four Reasons

1. **Tacit Knowledge Exposure** — Users don't know what they prefer until they see concrete examples
2. **Prevents Underspecification** — Open questions lead to vague answers missing technical nuances
3. **Lower Mental Effort** — Deciding between two examples is easier than articulating abstract principles
4. **Boundary Revelation** — Edge cases force confrontation with actual decision points

---

## Three Question Types (Strategic Mix)

### 1. Edge-Case Scenarios (Most Effective)

**When:** Communication preferences, priority conflicts, style choices

**Format:** Show 2-3 complete concrete examples, force choice

**Example — Communication Style:**
```
Hier sind zwei Versionen derselben Mail an deinen Teamlead. 
Welche würdest du abschicken?

┌─ Version A (direkt) ─────────────────────────────────┐
│ Betreff: Blocker im Skillfinder Projekt             │
│                                                       │
│ Hi Müller,                                           │
│ das Projekt ist blockiert weil die API-Keys fehlen. │
│ Brauche die bis morgen.                             │
│ Gruß, Juan                                           │
└───────────────────────────────────────────────────────┘

┌─ Version B (ausführlicher) ──────────────────────────┐
│ Betreff: Status Skillfinder – Blocker               │
│                                                       │
│ Hallo Müller,                                        │
│ kurzes Update zum Skillfinder MVP:                   │
│ Das Backend ist fertig, aber ich kann nicht weiter  │
│ testen weil mir die AWS API-Keys für die           │
│ Test-Umgebung fehlen. Könntest du die bis morgen    │
│ bereitstellen? Dann kann ich wie geplant           │
│ weitermachen.                                        │
│ Danke und Gruß, Juan                                 │
└───────────────────────────────────────────────────────┘

[Version A wählen] [Version B wählen]
```

**What This Reveals:** Preference for directness vs. context-setting, formality level, use of greetings

**Example — Time Boundaries:**
```
Es ist 23 Uhr und ein Kollege schreibt wegen Arbeit.
Was soll ich tun?

[Sofort antworten vorschlagen]
[Bis morgen warten]
[Abhängig vom Absender]
```

**What This Reveals:** Work-life boundaries, urgency thresholds, relationship priorities

**Example — Priority Conflicts:**
```
Du hast gleichzeitig:
• Team-Meeting über das neue Feature
• 1-on-1 mit deinem Manager

Welches soll ich priorisieren?

[Team-Meeting] [1-on-1] [Nachfragen]
```

**What This Reveals:** Value hierarchy (team vs. manager), decision autonomy preferences

### 2. Binary Yes/No Questions (Systematic Exploration)

**When:** Initial questions, systematic preference mapping, low-effort decisions

**Format:** Clear yes/no with specific scenario

**Examples:**
```
Soll ich dich an ungelesene Nachrichten erinnern, die älter als 3 Tage sind?
[Ja] [Nein]

Möchtest du Entwürfe für Dankesmails nach Meetings?
[Ja] [Nein]

Soll ich bei technischen Fragen ausführliche Erklärungen geben?
[Ja] [Nein]

Würdest du bevorzugen: Bullet Points oder Fließtext?
[Bullet Points] [Fließtext] [Je nach Thema]
```

**Benefits:**
- Low cognitive load
- Systematic coverage
- Fast response time
- Clear preference boundaries

### 3. Example-Guided Open Questions (Minimal Use)

**When:** Binary/edge cases insufficient, need custom details

**Format:** Show 3 example answers, user can click or type custom

**Example:**
```
Was sind deine Hauptaufgaben?

Beispiele (klicken oder eigene Antwort):
• "API-Entwicklung, Infrastruktur, und Prototyping neuer Systeme"
• "Team Lead: Code Reviews, Architektur, Mentoring von Junior Devs"
• "Full-Stack Development mit Fokus auf Python/FastAPI Backend"

[  Eigene Antwort eingeben...  ]
```

---

## Section-Specific Strategies

| Section | Primary Type | Example Edge Case |
|---------|-------------|-------------------|
| **Rolle & Team** | Binary → Example | "Hier ist deine Rolle, wie ich sie verstehe: [generated]. Stimmt das?" |
| **Projekte** | Edge-case | "Projekt X ist blockiert, Projekt Y ist dringend. Worauf fokussieren?" |
| **Tools & Tech** | Binary | "Python Fehler aufgetreten. Was machst du: Debugger oder print statements?" |
| **Kommunikation** | **Edge-case (heavy)** | **"Zwei Mail-Versionen — welche würdest du schicken?"** |
| **Aufgaben** | Edge-case | "Du hast 3h frei. Tasks: [list]. Welche Reihenfolge?" |
| **Grenzen** | Binary → Edge | "Darf ich speichern: 'Juan hat heute Kopfschmerzen'?" |

---

## Adaptive Question Flow

```python
def select_question_type(section, previous_answers, remaining_goals):
    """
    Research-based question type selection
    """
    # Communication: heavily use edge cases
    if section == "communication" and len(previous_answers) < 3:
        return "edge_case"
    
    # Initial questions: binary for systematic exploration
    if len(previous_answers) < 2:
        return "binary"
    
    # Validation phase: edge cases
    if len(remaining_goals) <= 2:
        return "edge_case"
    
    # Default: binary (research shows best balance)
    return "binary"
```

---

## Time Budget: 5-7 Minutes

Research shows 5-minute interaction windows are optimal.

**KIM Target:**
- 6 sections × 3-5 questions = 18-30 questions total
- Adaptive: Detailed answers → fewer questions
- Average 15-20 seconds per question
- **Total: 5-10 minutes** (well within research-validated window)

---

## Example Onboarding Flow

### Section: Kommunikation (3 questions, ~2 minutes)

**Q1 (Edge-Case):**
```
Hier sind zwei Versionen derselben Statusmail. Welche würdest du schicken?

[Shows Version A: direkt, kurz]
[Shows Version B: ausführlich, höflich]

User clicks: Version A
→ Reveals: Prefers directness
```

**Q2 (Binary):**
```
Soll ich in Mails an deinen Teamlead immer einen Kontext mitliefern, 
oder kann ich direkt zur Sache kommen?

[Kontext mitliefern] [Direkt zur Sache]

User clicks: Direkt zur Sache
→ Confirms: Brevity valued with known contacts
```

**Q3 (Edge-Case):**
```
Es ist Freitag 17 Uhr. Ein Kollege fragt nach deiner Hilfe. 
Welche Antwort würdest du schicken?

Version A: "Kann ich dir Montag helfen?"
Version B: "Gerne, ich schau mir das gleich an"
Version C: "Kann ich in 10 Min kurz telefonieren?"

User clicks: Version C
→ Reveals: Willing to help but prefers synchronous resolution
```

**Profile Extract:**
```json
{
  "communication": {
    "language": "de",
    "answer_style": "direkt, kurz",
    "tone_with_manager": "professionell aber nicht förmlich",
    "boundary_time": "17:00 Freitag",
    "prefers_sync_for": "unklare Anfragen"
  }
}
```

**Coverage:** 3 questions captured:
- Formality level (edge case)
- Context preference (binary)
- Time boundaries (edge case)
- Communication modality (edge case)

---

## Implementation: Bedrock Prompt

```python
EDGE_CASE_GENERATION_PROMPT = """You are conducting preference elicitation for section: {section}

Section goals: {section_goals}
Previous answers: {previous_answers}

Generate ONE edge-case scenario that will reveal the most about user preferences.

REQUIREMENTS:
1. Present a concrete, specific situation (not abstract)
2. Show 2-3 complete examples (e.g., two email versions)
3. Force a decision that reveals tacit preferences
4. Target boundary conditions or conflicts
5. Make it realistic to user's actual work context
6. Use German for questions

EDGE CASES THAT WORK:
- Time boundary: "Es ist 23 Uhr und..."
- Conflict: "Du hast zwei gleichzeitige Meetings..."
- Format choice: "Hier sind zwei Versionen — welche würdest du schicken..."
- Priority: "Projekt X ist blockiert, Projekt Y ist dringend. Worauf fokussieren?"

AVOID:
- Abstract: "Was ist dein Kommunikationsstil?"
- Self-reporting: "Bevorzugst du direkte Kommunikation?"
- Hypotheticals without specifics: "Wie würdest du Konflikte handhaben?"

Return JSON:
{
  "question": "Concrete scenario in German",
  "question_type": "edge_case",
  "options": [
    {
      "label": "Option A",
      "value": "option_a",
      "example_content": "Full example text (email, message, code, etc.)"
    },
    {
      "label": "Option B",
      "value": "option_b",
      "example_content": "Full example text"
    }
  ],
  "rationale": "What preference this reveals",
  "remaining_goals": ["uncovered goal 1", "uncovered goal 2"]
}
"""
```

---

## Success Metrics

### Onboarding Quality

Track whether users:
1. **Contradict earlier statements** (evidence of preference discovery)
2. **Express surprise** at their own choices
3. **Change answers** when seeing concrete examples
4. **Report learning** something about themselves

### Preference Accuracy

Measure via held-out scenarios:
- Generate 5 edge cases NOT shown in onboarding
- Predict user's choice based on extracted profile
- Compare prediction to actual user choice
- Target: ≥80% accuracy (research baseline: ~75%)

### User Experience

- Onboarding completion rate
- Time to complete (target: 5-7 min)
- Mental effort rating (target: ≤3/5)
- User reported value ("Did this help capture your preferences?")

---

## Key Takeaways for KIM Implementation

1. **Communication section is critical** — Use edge cases heavily here
2. **Show complete examples** — Two full email versions, not abstractions
3. **Time-box to 5-7 minutes** — Research-validated optimal window
4. **Mix question types** — Edge cases for validation, binary for exploration
5. **Expect contradictions** — Users discovering preferences is the goal
6. **Validate with held-out cases** — Test profile accuracy on unseen scenarios

---

## Future Enhancements

### Continuous Preference Learning

After onboarding, continue refining profile:
- When user edits AI-generated text, ask: "Soll ich das merken für nächstes Mal?"
- Weekly edge-case check: "Hier ist eine neue Situation — wie würdest du handeln?"
- Track actual behavior vs. stated preferences, prompt for clarification on divergence

### Preference Uncertainty

Some preferences are contextual. Profile should capture:
```json
{
  "communication": {
    "with_manager": "direkt aber höflich",
    "with_peers": "sehr direkt",
    "with_external": "förmlich",
    "uncertainty": ["response_time_boundaries"]
  }
}
```

### A/B Testing

Run internal test:
- Group A: Traditional open questions
- Group B: GATE methodology (edge cases + binary)
- Measure: profile accuracy, user satisfaction, time to complete

Expected: Group B profiles predict user preferences more accurately with equal/less time.

---

**Status:** Design complete, ready for implementation in backend/agentic_loop.py
