# KIM System Architecture — Professional Diagram

**Version:** 1.0  
**Date:** 2026-08-25  
**Status:** Segment 0 Complete

---

## System Overview

```mermaid
graph TB
    %% Title
    title[<b>KIM System Architecture</b><br/>MCP Middleware for LLM Personalization]
    
    %% External Layer
    User([👤 User])
    LLM[<b>User's LLM</b><br/>Claude • Copilot • ChatGPT]
    
    User -->|Query| LLM
    
    %% MCP Connection
    LLM <-->|MCP Protocol<br/>JSON-RPC 2.0| MCP_Interface
    
    %% KIM System Box
    subgraph KIM["🔷 KIM Middleware Server (No Internal LLM)"]
        direction TB
        
        %% Interface Layer
        subgraph Interface["📡 Interface Layer"]
            MCP_Interface[MCP Server<br/>Tool Registry]
        end
        
        %% Tools Layer
        subgraph Tools["🛠️ Tools Layer (Exposed via MCP)"]
            T_Context[get_context<br/>Profile + Examples]
            T_Check[check_draft<br/>Validation]
            T_Onboard[onboard_*<br/>GATE Targets]
            T_Log[log_output<br/>Store Output]
        end
        
        %% Logic Layer
        subgraph Logic["⚙️ Business Logic Layer"]
            L_Retrieval[Retrieval Engine<br/>BM25 + Vector]
            L_Checker[Profile Checker<br/>Rules]
            L_GATE[GATE State Machine<br/>Barriers]
            L_Logger[Output Logger<br/>Embed + Index]
        end
        
        %% Data Layer
        subgraph Data["💾 Data Layer"]
            D_Profile[(Profile<br/>Tone, Style)]
            D_Outputs[(Outputs<br/>Past Writing)]
            D_Memory[(Memory<br/>STM/LTM)]
            D_Vectors[(Vectors<br/>Embeddings)]
        end
        
        %% Internal Connections
        MCP_Interface --> T_Context
        MCP_Interface --> T_Check
        MCP_Interface --> T_Onboard
        MCP_Interface --> T_Log
        
        T_Context --> L_Retrieval
        T_Check --> L_Checker
        T_Onboard --> L_GATE
        T_Log --> L_Logger
        
        L_Retrieval --> D_Profile
        L_Retrieval --> D_Outputs
        L_Retrieval --> D_Vectors
        
        L_Checker --> D_Profile
        L_GATE --> D_Profile
        
        L_Logger --> D_Outputs
        L_Logger --> D_Memory
        L_Logger --> D_Vectors
    end
    
    %% Anleitung
    Anleitung[📋 Anleitung<br/>Protocol Instructions]
    Anleitung -.->|Guides LLM| LLM
    
    %% Styling
    classDef external fill:#E3F2FD,stroke:#1565C0,stroke-width:3px
    classDef interface fill:#FFF9C4,stroke:#F57F17,stroke-width:2px
    classDef tool fill:#FFE0B2,stroke:#E65100,stroke-width:2px
    classDef logic fill:#F3E5F5,stroke:#4A148C,stroke-width:2px
    classDef data fill:#E8F5E9,stroke:#1B5E20,stroke-width:2px
    classDef protocol fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    
    class User,LLM external
    class MCP_Interface interface
    class T_Context,T_Check,T_Onboard,T_Log tool
    class L_Retrieval,L_Checker,L_GATE,L_Logger logic
    class D_Profile,D_Outputs,D_Memory,D_Vectors data
    class Anleitung protocol
```

---

## Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant LLM as User's LLM
    participant KIM as KIM Server
    participant Data as Data Store

    User->>LLM: "Write an email"
    
    Note over LLM: Needs context
    LLM->>KIM: get_context(query)
    KIM->>Data: Load profile
    Data-->>KIM: User profile
    KIM->>Data: Search relevant outputs
    Data-->>KIM: Past emails (ranked)
    KIM-->>LLM: {profile, outputs, memory}
    
    Note over LLM: Generates draft<br/>using context
    
    LLM->>KIM: check_draft(draft)
    KIM->>Data: Load profile rules
    Data-->>KIM: Tone, format, boundaries
    Note over KIM: Deterministic validation<br/>(no LLM needed)
    KIM-->>LLM: {is_valid, issues[]}
    
    Note over LLM: Revises if needed
    
    LLM->>User: Final personalized email
    
    Note over User: Approves
    
    LLM->>KIM: log_output(final_text)
    KIM->>Data: Store text
    KIM->>Data: Generate embedding (async)
    KIM->>Data: Update vector index
    KIM-->>LLM: Success
```

---

## Onboarding Flow (GATE)

```mermaid
sequenceDiagram
    participant User
    participant LLM as User's LLM
    participant KIM as KIM Server
    participant GATE as GATE State

    User->>LLM: "Let's set up my profile"
    
    LLM->>KIM: get_targets()
    KIM->>GATE: Load all targets
    GATE-->>KIM: Open targets + barriers
    KIM-->>LLM: Target list<br/>{dimension, research, barrier}
    
    Note over LLM: Freely decides strategy:<br/>edge-case question
    
    LLM->>User: "Would you prefer A or B?"
    User->>LLM: "Option A"
    
    LLM->>KIM: store_insight(target_id, evidence)
    KIM->>GATE: Record evidence
    GATE->>GATE: Check barrier
    GATE-->>KIM: Barrier status
    KIM-->>LLM: {satisfied: false, needs_more}
    
    Note over LLM: Asks follow-up
    
    LLM->>User: "In what situations...?"
    User->>LLM: Answer
    
    LLM->>KIM: store_insight(target_id, evidence)
    KIM->>GATE: Record evidence
    GATE->>GATE: Check barrier
    GATE-->>KIM: Barrier status
    KIM-->>LLM: {satisfied: true}
    
    Note over LLM: Move to next target
    
    LLM->>KIM: get_targets()
    KIM-->>LLM: Fewer open targets
    
    Note over LLM,KIM: Loop until<br/>minimum viable profile
```

---

## Data Model

```mermaid
erDiagram
    USER_PROFILE ||--o{ USER_OUTPUT : generates
    USER_PROFILE ||--o{ MEMORY : accumulates
    USER_PROFILE ||--o{ ONBOARDING_TARGET : "built from"
    
    USER_PROFILE {
        uuid id PK
        string language
        enum tone
        enum format_preference
        json boundaries
        float confidence
        timestamp updated_at
    }
    
    USER_OUTPUT {
        uuid id PK
        uuid profile_id FK
        text content
        string context
        enum output_type
        timestamp created_at
        vector embedding
        json metadata
    }
    
    MEMORY {
        uuid id PK
        uuid profile_id FK
        enum type
        text content
        float importance
        timestamp created_at
        timestamp expires_at
    }
    
    ONBOARDING_TARGET {
        uuid id PK
        uuid profile_id FK
        string dimension
        string research_basis
        enum barrier_type
        json barrier_threshold
        bool satisfied
        float confidence
        json evidence
        timestamp satisfied_at
    }
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph Client["💻 Client Machine"]
        direction TB
        
        LLM_App[LLM Client Application<br/>Claude Desktop / VSCode / etc.]
        
        subgraph KIM_Process["🐍 KIM Server Process"]
            Server[Python 3.11+<br/>MCP SDK<br/>Port: stdio or :8080]
        end
        
        subgraph Storage["💾 File System"]
            Profiles[~/.kim/data/profiles/]
            Outputs[~/.kim/data/outputs/]
            Memory[~/.kim/data/memory/]
            Vectors[~/.kim/data/vectors/]
        end
        
        LLM_App <-->|MCP: stdio or HTTP| KIM_Process
        KIM_Process -->|File I/O| Storage
    end
    
    subgraph Optional["☁️ Optional External Service"]
        Embedding[Embedding API<br/>OpenAI / Cohere / Local]
    end
    
    KIM_Process -.->|HTTPS<br/>text-embedding-3-small| Embedding
    
    style Client fill:#FFF9C4,stroke:#F57F17,stroke-width:2px
    style Optional fill:#E8EAF6,stroke:#3F51B5,stroke-width:1px,stroke-dasharray: 5 5
```

---

## Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **🌐 LLM-Agnostic** | Works with any MCP-capable LLM (Claude, Copilot, ChatGPT) |
| **⚡ Zero Compute** | No internal LLM required — pure logic + data |
| **📚 Research-Backed** | Based on GATE (ICLR 2025), Wu et al. (2024) |
| **💾 Portable** | File-based storage, no database required |
| **🔒 Privacy-First** | All data stays local, no cloud transmission |
| **✅ Deterministic** | Validation is rule-based, no LLM needed |

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Protocol | Python MCP SDK | Official SDK, well-documented |
| Runtime | Python 3.11+ | Async support, type hints |
| Package Manager | uv | Fast, modern, deterministic |
| Data Models | Pydantic v2 | Validation, serialization |
| Vector Search | ChromaDB / FAISS | Embedded, no external service |
| Embeddings | OpenAI API / sentence-transformers | Flexible (cloud or local) |
| Storage | File system (JSON) | Simple, portable |
| Testing | pytest + pytest-asyncio | Industry standard |

---

## Research Foundations

### GATE (Li et al., ICLR 2025)
- LLM-driven preference elicitation via edge-cases
- Forced choices reveal tacit knowledge
- 5-10 minute optimal window
- Works with open-source models

### User Profile Roles (Wu et al., 2024)
- User **outputs** (not inputs) drive personalization
- Output-only format fits 2-5x more in context
- Most-relevant-first ordering critical
- Non-user content hurts performance

### Multi-Agent Personalization (Westhaeusser et al., 2025)
- Coordinator → Operator → Validator → Generator
- Multi-tiered memory (STM/LTM)
- 96% retrieval accuracy with full system

---

## Build Status

```mermaid
graph LR
    S0[✅ Segment 0<br/>Skeleton]
    S1[⏳ Segment 1<br/>MCP Server]
    S2[📋 Segment 2<br/>Data Layer]
    S3[📋 Segment 3<br/>Retrieval]
    S4[📋 Segment 4<br/>Validation]
    S5[📋 Segment 5<br/>Onboarding]
    S6[📋 Segment 6<br/>Anleitung]
    S7[📋 Segment 7<br/>Sampling]
    S8[📋 Segment 8<br/>Learning]
    S9[📋 Segment 9<br/>Production]
    
    S0 --> S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9
    
    style S0 fill:#C8E6C9,stroke:#2E7D32,stroke-width:3px
    style S1 fill:#FFF9C4,stroke:#F57F17,stroke-width:3px
    style S2 fill:#f5f5f5,stroke:#bbb
    style S3 fill:#f5f5f5,stroke:#bbb
    style S4 fill:#f5f5f5,stroke:#bbb
    style S5 fill:#f5f5f5,stroke:#bbb
    style S6 fill:#f5f5f5,stroke:#bbb
    style S7 fill:#f5f5f5,stroke:#bbb
    style S8 fill:#f5f5f5,stroke:#bbb
    style S9 fill:#f5f5f5,stroke:#bbb
```

---

**Legend:**
- ✅ Complete
- ⏳ In Progress
- 📋 Planned

---

**Document Version:** 1.0  
**Last Updated:** 2026-08-25  
**Format:** Mermaid (renders in VS Code, GitHub, compatible tools)
