# IRIS — Architecture

## System Architecture (with Build Status)

```mermaid
graph TB
    %% ═══ EXTERNAL ═══
    User([👤 User])
    LLM[User's LLM<br>Claude / Copilot / ChatGPT]

    User -->|writes message| LLM

    %% ═══ MCP CONNECTION ═══
    LLM <-->|MCP protocol| MCP

    %% ═══ IRIS MCP SERVER ═══
    subgraph IRIS["IRIS — MCP Middleware (no LLM inside)"]

        MCP[MCP Interface]

        subgraph ToolLayer["MCP Tools (exposed to LLM)"]
            T_ctx[get_context<br>query → profile + examples]
            T_chk[check_draft<br>draft → validation feedback]
            T_onb[onboard tools<br>targets, store_insight, ...]
            T_log[log_output<br>text → store for retrieval]
        end

        subgraph LogicLayer["Internal Logic (deterministic, no LLM)"]
            L_ret[Retrieval Engine<br>BM25 + vector similarity]
            L_chk[Profile Checker<br>rules + pattern matching]
            L_gate[GATE State Machine<br>targets + barriers + progress]
            L_log[Output Logger<br>index + embed]
        end

        subgraph DataLayer["Persistent Data"]
            D_prof[(User Profile<br>tone, style, boundaries)]
            D_out[(User Outputs<br>past writing samples)]
            D_mem[(Memory<br>STM / summaries)]
            D_vec[(Vector Index<br>embeddings)]
        end

        Anleitung[Anleitung<br>Protocol that guides the LLM]
    end

    %% ═══ CONNECTIONS ═══
    Anleitung -.->|instructions| LLM

    MCP --> T_ctx
    MCP --> T_chk
    MCP --> T_onb
    MCP --> T_log

    T_ctx --> L_ret
    T_chk --> L_chk
    T_onb --> L_gate
    T_log --> L_log

    L_ret --> D_prof
    L_ret --> D_out
    L_ret --> D_vec
    L_chk --> D_prof
    L_gate --> D_prof
    L_log --> D_out
    L_log --> D_vec
    L_log --> D_mem

    %% ═══ STYLES: Build Status ═══
    %% Green = built, Yellow = current segment, Gray = planned

    %% External (always exists)
    style User fill:#E3F2FD,stroke:#1565C0
    style LLM fill:#E3F2FD,stroke:#1565C0

    %% MCP Interface — Segment 1 (built)
    style MCP fill:#C8E6C9,stroke:#2E7D32

    %% Tools — ALL BUILT
    style T_ctx fill:#C8E6C9,stroke:#2E7D32
    style T_chk fill:#C8E6C9,stroke:#2E7D32
    style T_onb fill:#C8E6C9,stroke:#2E7D32
    style T_log fill:#C8E6C9,stroke:#2E7D32

    %% Logic — ALL BUILT
    style L_ret fill:#C8E6C9,stroke:#2E7D32
    style L_chk fill:#C8E6C9,stroke:#2E7D32
    style L_gate fill:#C8E6C9,stroke:#2E7D32
    style L_log fill:#C8E6C9,stroke:#2E7D32

    %% Data — ALL BUILT
    style D_prof fill:#C8E6C9,stroke:#2E7D32
    style D_out fill:#C8E6C9,stroke:#2E7D32
    style D_mem fill:#f9f9f9,stroke:#ccc
    style D_vec fill:#C8E6C9,stroke:#2E7D32

    %% Anleitung — BUILT
    style Anleitung fill:#C8E6C9,stroke:#2E7D32
```

### Legend

| Color | Meaning |
|-------|---------|
| 🟢 Green | Built and working |
| 🟡 Yellow | Current segment (building now) |
| ⚪ Gray | Planned (not yet implemented) |
| 🔵 Blue | External system (user's LLM) |

---

## Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant LLM as User's LLM
    participant IRIS as IRIS (MCP)
    participant Data as Data Store

    U->>LLM: Message (e.g. "Schreib eine Mail")
    LLM->>IRIS: get_context(query)
    IRIS->>Data: Retrieve profile + relevant outputs
    Data-->>IRIS: Profile + ranked examples (most relevant first)
    IRIS-->>LLM: Context + style rules + boundaries

    Note over LLM: Generates draft using IRIS's context

    LLM->>IRIS: check_draft(draft)
    Note over IRIS: Deterministic validation<br>(tone, format, boundaries)
    IRIS-->>LLM: "zu förmlich" or "OK"

    Note over LLM: Revises if needed

    LLM->>U: Final personalized response
    LLM->>IRIS: log_output(final_text)
    IRIS->>Data: Store + embed for future retrieval
```

---

## Onboarding Flow (GATE)

```mermaid
sequenceDiagram
    participant U as User
    participant LLM as User's LLM
    participant IRIS as IRIS (MCP)

    U->>LLM: "Lass uns an meinem Profil arbeiten"
    LLM->>IRIS: get_targets()
    IRIS-->>LLM: Open targets + research basis + barriers

    Note over LLM: Freely decides strategy<br>(edge-case / binary / open question)

    LLM->>U: Question based on chosen strategy
    U->>LLM: Answer
    LLM->>IRIS: store_insight(target, evidence)
    IRIS-->>LLM: Barrier met? (satisfied / needs more)

    Note over LLM,IRIS: Loop until minimum viable profile

    LLM->>IRIS: get_targets()
    IRIS-->>LLM: Fewer open targets remaining
```

> IRIS defines WHAT to learn (research-backed targets with barriers).
> The LLM decides HOW to ask (strategy, order, phrasing).

---

## The Self-Check Pattern

```mermaid
graph LR
    A[LLM generates<br>draft] --> B[calls check_draft]
    B --> C{IRIS validates<br>against profile}
    C -->|OK| D[Shows to user]
    C -->|Mismatch| E[Returns feedback:<br>specific issue]
    E --> F[LLM revises] --> B
```

> **Why this works:** The LLM thinks `check_draft` is an external service.
> IRIS validates with fresh eyes — profile rules only, no generation context.
> Result: unbiased feedback the LLM couldn't give itself.

---

## Layer 2: MCP Sampling (Advanced Clients Only)

```mermaid
graph LR
    subgraph Layer2["IRIS orchestrates via sampling"]
        direction TB
        K[IRIS] -->|"sampling: classify"| S1[Fresh LLM context 1]
        S1 -->|result| K
        K -->|"sampling: generate"| S2[Fresh LLM context 2]
        S2 -->|result| K
        K -->|"sampling: validate"| S3[Fresh LLM context 3]
        S3 -->|result| K
    end
```

> Each step = isolated context (no bleed between roles).
> Same user LLM, but IRIS controls the orchestration.
> Falls back to Layer 1 (tools + Anleitung) for basic clients.

---

## Data Model

```mermaid
erDiagram
    USER_PROFILE {
        string id
        string language
        string tone
        string format_preference
        json boundaries
        float confidence
        datetime updated_at
    }

    USER_OUTPUT {
        string id
        string content
        string context
        datetime created_at
        vector embedding
    }

    MEMORY {
        string id
        string type
        string summary
        datetime created_at
    }

    ONBOARDING_TARGET {
        string id
        string dimension
        string research_basis
        string barrier_type
        bool satisfied
        float confidence
        json evidence
    }

    USER_PROFILE ||--o{ USER_OUTPUT : "generates"
    USER_PROFILE ||--o{ MEMORY : "accumulates"
    USER_PROFILE ||--o{ ONBOARDING_TARGET : "built from"
```

---

## Segment Progress

```mermaid
graph LR
    S0[✓ Skeleton<br>+ Hooks]
    S1[✓ MCP<br>Server]
    S2[✓ Data<br>Layer]
    S3[Retrieval]
    S4[Validation]
    S5[Onboarding]
    S6[Anleitung]
    S7[Sampling]
    S8[Learning]
    S9[Production]

    S0 --> S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9

    style S0 fill:#C8E6C9,stroke:#2E7D32
    style S1 fill:#C8E6C9,stroke:#2E7D32
    style S2 fill:#C8E6C9,stroke:#2E7D32
    style S3 fill:#FFF9C4,stroke:#F57F17
    style S4 fill:#f5f5f5,stroke:#bbb
    style S5 fill:#f5f5f5,stroke:#bbb
    style S6 fill:#f5f5f5,stroke:#bbb
    style S7 fill:#f5f5f5,stroke:#bbb
    style S8 fill:#f5f5f5,stroke:#bbb
    style S9 fill:#f5f5f5,stroke:#bbb
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| IRIS never generates, only validates | User's LLM generates; IRIS provides context + validation |
| Two-stage validation | Deterministic (free, fast) → MCP sampling (semantic, unbiased) |
| MCP sampling for validation | Use user's LLM in fresh context (no generation bias) |
| Adaptive validation strategy | Try MCP sampling → fallback deterministic only (no forced dependencies) |
| `check_draft` as blind validator | LLM can't judge its own work; fresh context check is unbiased |
| Research-based targets | Every onboarding dimension must cite evidence (GATE, Wu et al.) |
| Two layers | Layer 1 works with any MCP client; Layer 2 uses sampling for validation |
| User outputs > inputs | Wu 2024: past writing drives personalization, not past questions |
| Most-relevant-first | Wu 2024: position in context matters — best examples go first |
| Tools split over time | Start broad, refine into granular tools as patterns emerge |

---

*This document updates after each segment (progress tracker hook). Components turn green as they are built.*
