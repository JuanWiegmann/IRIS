# IRIS System Architecture — Professional Documentation

**Document Version:** 1.0  
**Last Updated:** 2026-07-24  
**Status:** Segment 0 Complete, Segment 1 In Progress  
**Architecture Style:** Microservice / Middleware / MCP Protocol

---

## Executive Summary

**IRIS (Knowledge & Identity Middleware)** is an MCP-compliant middleware server that provides personalization capabilities to any LLM-based system. IRIS acts as a context provider and validator, enabling consistent user experience across multiple LLM providers (Claude, GitHub Copilot, ChatGPT) without requiring model-specific integrations.

**Core Value Proposition:**
- Single user profile works across all LLMs
- Zero vendor lock-in (LLM-agnostic design)
- Research-backed personalization (GATE, Wu et al. 2024)
- No compute cost (pure logic + data, no internal LLM)

---

## 1. Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                         ENTERPRISE USER                          │
│                    (Human User / End Customer)                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Uses
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Client Application                      │
│                                                                  │
│  • Claude Desktop / claude.ai / Claude Code                     │
│  • GitHub Copilot (VSCode, JetBrains)                           │
│  • ChatGPT / OpenAI clients                                     │
│  • Custom LLM applications                                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ MCP Protocol
                                 │ (stdio / HTTP)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                          IRIS SERVER                              │
│                   (MCP Middleware Server)                        │
│                                                                  │
│  Responsibilities:                                               │
│  • Store and retrieve user profiles                             │
│  • Provide personalized context to LLMs                         │
│  • Validate LLM outputs against user preferences                │
│  • Manage onboarding workflows                                  │
│  • Log and index user outputs                                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Reads/Writes
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSISTENT STORAGE                          │
│                                                                  │
│  • User profiles (JSON/YAML)                                    │
│  • User outputs (indexed, embedded)                             │
│  • Memory (STM/LTM)                                             │
│  • Vector index (embeddings)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### External Dependencies

| System | Protocol | Purpose | Criticality |
|--------|----------|---------|-------------|
| LLM Client | MCP (stdio/HTTP) | Primary interface for tool invocation | **Critical** |
| Embedding Service | REST API | Generate vector embeddings (optional) | Medium |
| File System | OS native | Persistent data storage | **Critical** |

---

## 2. Container Diagram (C4 Level 2)

```
┌───────────────────────────────────────────────────────────────────┐
│                          LLM CLIENT                                │
│  (Claude Desktop, Copilot, ChatGPT, Custom Application)           │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ MCP Protocol (JSON-RPC 2.0)
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        IRIS MCP SERVER                            ┃
┃                                                                  ┃
┃  ┌─────────────────────────────────────────────────────────┐   ┃
┃  │              MCP INTERFACE LAYER                        │   ┃
┃  │  • Tool registration & schema validation               │   ┃
┃  │  • Request routing                                      │   ┃
┃  │  • Resource exposure (Anleitung protocol)              │   ┃
┃  └────────────────────────┬────────────────────────────────┘   ┃
┃                           │                                     ┃
┃  ┌────────────────────────┴────────────────────────────────┐   ┃
┃  │              TOOL EXECUTION LAYER                       │   ┃
┃  │                                                         │   ┃
┃  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │   ┃
┃  │  │ get_context │  │ check_draft  │  │ onboard_*    │ │   ┃
┃  │  └─────────────┘  └──────────────┘  └──────────────┘ │   ┃
┃  │  ┌─────────────┐                                      │   ┃
┃  │  │ log_output  │                                      │   ┃
┃  │  └─────────────┘                                      │   ┃
┃  └────────────────────────┬────────────────────────────────┘   ┃
┃                           │                                     ┃
┃  ┌────────────────────────┴────────────────────────────────┐   ┃
┃  │            BUSINESS LOGIC LAYER                         │   ┃
┃  │                                                         │   ┃
┃  │  ┌──────────────┐  ┌───────────────┐  ┌────────────┐ │   ┃
┃  │  │  Retrieval   │  │    Profile    │  │    GATE    │ │   ┃
┃  │  │   Engine     │  │   Checker     │  │   State    │ │   ┃
┃  │  └──────────────┘  └───────────────┘  └────────────┘ │   ┃
┃  │  ┌──────────────┐                                     │   ┃
┃  │  │    Output    │                                     │   ┃
┃  │  │    Logger    │                                     │   ┃
┃  │  └──────────────┘                                     │   ┃
┃  └────────────────────────┬────────────────────────────────┘   ┃
┃                           │                                     ┃
┃  ┌────────────────────────┴────────────────────────────────┐   ┃
┃  │              DATA ACCESS LAYER                          │   ┃
┃  │                                                         │   ┃
┃  │  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐ │   ┃
┃  │  │ Profile  │  │  Output  │  │ Memory │  │ Vector  │ │   ┃
┃  │  │   Store  │  │   Store  │  │ Store  │  │  Store  │ │   ┃
┃  │  └──────────┘  └──────────┘  └────────┘  └─────────┘ │   ┃
┃  └─────────────────────────────────────────────────────────┘   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                         │
                         │ File I/O
                         ▼
┌───────────────────────────────────────────────────────────────────┐
│                     PERSISTENT STORAGE                             │
│  ~/iris_data/profiles/, ~/iris_data/outputs/, ~/iris_data/vectors/   │
└───────────────────────────────────────────────────────────────────┘
```

### Container Responsibilities

| Container | Technology | Responsibility | Scale Characteristics |
|-----------|-----------|----------------|----------------------|
| MCP Interface | Python MCP SDK | Protocol handling, request routing | Lightweight, single-threaded |
| Tool Execution | Python | Execute exposed MCP tools | Stateless, parallel-safe |
| Business Logic | Python | Core algorithms (retrieval, validation, GATE) | CPU-bound for embeddings |
| Data Access | Python + File System | CRUD operations, indexing | I/O-bound |

---

## 3. Component Diagram (C4 Level 3)

### 3.1 Tool Execution Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  get_context(query: str) → ContextResponse              │   │
│  │                                                          │   │
│  │  Input:  User query or task description                 │   │
│  │  Output: {                                               │   │
│  │    profile: UserProfile,                                 │   │
│  │    relevant_outputs: List[UserOutput],  # ranked        │   │
│  │    memory: RecentContext                                 │   │
│  │  }                                                       │   │
│  │  Dependencies: RetrievalEngine, ProfileStore            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  check_draft(draft: str) → ValidationResult             │   │
│  │                                                          │   │
│  │  Input:  Draft text generated by LLM                    │   │
│  │  Output: {                                               │   │
│  │    is_valid: bool,                                       │   │
│  │    issues: List[ValidationIssue],  # tone, format, etc. │   │
│  │    suggestions: List[str]                                │   │
│  │  }                                                       │   │
│  │  Dependencies: ProfileChecker, ProfileStore             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  log_output(text: str, context: str) → Success          │   │
│  │                                                          │   │
│  │  Input:  Final output text + context                    │   │
│  │  Output: { stored: bool, id: str }                      │   │
│  │  Dependencies: OutputLogger, VectorStore                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Onboarding Tools (GATE System)                         │   │
│  │                                                          │   │
│  │  • get_targets() → List[OnboardingTarget]               │   │
│  │  • store_insight(target_id, evidence) → BarrierStatus   │   │
│  │  • check_satisfied(target_id) → SatisfactionLevel       │   │
│  │                                                          │   │
│  │  Dependencies: GATEStateMachine, ProfileStore           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Business Logic Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RetrievalEngine                                         │  │
│  │  ────────────────                                        │  │
│  │  + query(text: str) → List[UserOutput]                  │  │
│  │  + rank_by_relevance(outputs, query) → Sorted           │  │
│  │                                                          │  │
│  │  Algorithm:                                              │  │
│  │  1. BM25 keyword search                                  │  │
│  │  2. Vector similarity (cosine)                           │  │
│  │  3. Hybrid ranking (weighted combination)                │  │
│  │  4. Most-relevant-first ordering (Wu et al.)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ProfileChecker                                          │  │
│  │  ──────────────                                          │  │
│  │  + validate_tone(text, profile) → Issue[]               │  │
│  │  + validate_format(text, profile) → Issue[]             │  │
│  │  + validate_boundaries(text, profile) → Issue[]         │  │
│  │                                                          │  │
│  │  Rules:                                                  │  │
│  │  • Tone: formal vs casual, technical depth              │  │
│  │  • Format: length, structure, examples                  │  │
│  │  • Boundaries: topics to avoid, constraints             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GATEStateMachine                                        │  │
│  │  ────────────────                                        │  │
│  │  + get_open_targets() → List[Target]                    │  │
│  │  + record_evidence(target, evidence) → void             │  │
│  │  + check_barrier(target) → Satisfied | NeedsMore        │  │
│  │                                                          │  │
│  │  State:                                                  │  │
│  │  • Targets: research-backed dimensions                  │  │
│  │  • Barriers: minimum evidence thresholds                │  │
│  │  • Progress: per-target satisfaction level              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  OutputLogger                                            │  │
│  │  ────────────                                            │  │
│  │  + log(text, context) → void                            │  │
│  │  + embed(text) → Vector                                 │  │
│  │  + index(output) → void                                 │  │
│  │                                                          │  │
│  │  Process:                                                │  │
│  │  1. Store raw text + metadata                           │  │
│  │  2. Generate embedding (async)                          │  │
│  │  3. Update vector index                                 │  │
│  │  4. Update STM/LTM memory                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Use Case Diagrams

### 4.1 Primary Use Cases

```
                    ┌────────────────┐
                    │  End User      │
                    │  (Human)       │
                    └───────┬────────┘
                            │
                            │ uses
                            ▼
                    ┌────────────────┐
                    │  LLM Client    │
                    │  Application   │
                    └───┬────────┬───┘
                        │        │
        ┌───────────────┘        └───────────────┐
        │                                        │
        │ MCP calls                              │ MCP calls
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  UC-01           │                    │  UC-02           │
│  Get             │                    │  Validate        │
│  Personalized    │                    │  Draft           │
│  Context         │                    │                  │
└──────────────────┘                    └──────────────────┘
        │                                        │
        │ includes                               │ includes
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  Retrieve User   │                    │  Check Against   │
│  Profile         │                    │  Profile Rules   │
└──────────────────┘                    └──────────────────┘
        │
        │ includes
        ▼
┌──────────────────┐
│  Rank Relevant   │
│  Past Outputs    │
└──────────────────┘


                    ┌────────────────┐
                    │  End User      │
                    └───────┬────────┘
                            │
                            │ initiates
                            ▼
┌──────────────────┐                    ┌──────────────────┐
│  UC-03           │                    │  UC-04           │
│  Complete        │                    │  Log User        │
│  Onboarding      │                    │  Output          │
│                  │                    │                  │
└──────────────────┘                    └──────────────────┘
        │                                        │
        │ includes                               │ includes
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  Get Open        │                    │  Store Text      │
│  Targets         │                    │  + Metadata      │
└──────────────────┘                    └──────────────────┘
        │                                        │
        │ includes                               │ includes
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  Store           │                    │  Generate        │
│  Insight         │                    │  Embedding       │
└──────────────────┘                    └──────────────────┘
        │                                        │
        │ includes                               │ includes
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  Check Barrier   │                    │  Update Vector   │
│  Satisfaction    │                    │  Index           │
└──────────────────┘                    └──────────────────┘
```

### 4.2 Use Case Specifications

#### UC-01: Get Personalized Context

| Field | Value |
|-------|-------|
| **ID** | UC-01 |
| **Name** | Get Personalized Context |
| **Actor** | LLM Client Application |
| **Precondition** | User profile exists in IRIS |
| **Trigger** | LLM needs context for user query |
| **Main Flow** | 1. LLM calls `get_context(query)`<br>2. IRIS retrieves user profile<br>3. IRIS searches for relevant past outputs (BM25 + vector)<br>4. IRIS ranks results (most-relevant-first)<br>5. IRIS returns {profile, outputs, memory} |
| **Postcondition** | LLM receives personalized context |
| **Alternative Flow** | If no profile exists → return default/empty profile |
| **Performance Req** | < 500ms for typical queries |

#### UC-02: Validate Draft

| Field | Value |
|-------|-------|
| **ID** | UC-02 |
| **Name** | Validate Draft Against Profile |
| **Actor** | LLM Client Application |
| **Precondition** | User profile exists, draft text provided |
| **Trigger** | LLM generates draft and calls `check_draft(text)` |
| **Main Flow** | 1. LLM calls `check_draft(draft)`<br>2. IRIS retrieves user profile rules<br>3. IRIS checks tone, format, boundaries<br>4. IRIS identifies issues (if any)<br>5. IRIS returns {is_valid, issues[], suggestions[]} |
| **Postcondition** | LLM receives validation feedback |
| **Alternative Flow** | If no issues → return {is_valid: true} |
| **Performance Req** | < 200ms (deterministic, no LLM call) |

#### UC-03: Complete Onboarding

| Field | Value |
|-------|-------|
| **ID** | UC-03 |
| **Name** | Complete User Onboarding |
| **Actor** | End User (via LLM Client) |
| **Precondition** | IRIS initialized, targets defined |
| **Trigger** | User starts onboarding ("let's work on my profile") |
| **Main Flow** | 1. LLM calls `get_targets()`<br>2. IRIS returns open targets + barriers<br>3. LLM decides question strategy (edge-case/binary/open)<br>4. LLM asks user question<br>5. User responds<br>6. LLM calls `store_insight(target, evidence)`<br>7. IRIS checks if barrier satisfied<br>8. Repeat until minimum viable profile complete |
| **Postcondition** | User profile meets all target barriers |
| **Alternative Flow** | User can pause/resume onboarding |
| **Performance Req** | Full onboarding: 5-10 minutes (GATE research) |

#### UC-04: Log User Output

| Field | Value |
|-------|-------|
| **ID** | UC-04 |
| **Name** | Log User Output for Future Retrieval |
| **Actor** | LLM Client Application |
| **Precondition** | Final output approved by user |
| **Trigger** | LLM calls `log_output(text, context)` |
| **Main Flow** | 1. LLM calls `log_output(final_text, context)`<br>2. IRIS stores text + metadata<br>3. IRIS generates embedding (async)<br>4. IRIS updates vector index<br>5. IRIS updates STM/LTM memory<br>6. IRIS returns success |
| **Postcondition** | Output indexed and retrievable |
| **Alternative Flow** | Embedding generation can happen asynchronously |
| **Performance Req** | Synchronous: < 100ms; Async embedding: < 2s |

---

## 5. Data Model

### 5.1 Entity-Relationship Diagram

```
┌────────────────────────────────────────────────────────────────┐
│  USER_PROFILE                                                   │
├────────────────────────────────────────────────────────────────┤
│  PK  id: UUID                                                   │
│      language: string (e.g. "de-DE", "en-US")                  │
│      tone: enum (formal, casual, technical, friendly)          │
│      format_preference: enum (concise, detailed, examples)     │
│      boundaries: JSON (topics to avoid, constraints)           │
│      confidence: float (0.0-1.0, profile completeness)         │
│      created_at: timestamp                                     │
│      updated_at: timestamp                                     │
└────────────┬───────────────────────────────────────────────────┘
             │
             │ 1:N
             │
┌────────────┴───────────────────────────────────────────────────┐
│  USER_OUTPUT                                                    │
├────────────────────────────────────────────────────────────────┤
│  PK  id: UUID                                                   │
│  FK  profile_id: UUID                                           │
│      content: text (the actual output)                         │
│      context: string (what the output was about)               │
│      output_type: enum (email, report, code, message)          │
│      created_at: timestamp                                     │
│      embedding: vector (float[], 768 or 1536 dim)              │
│      metadata: JSON (tags, source_llm, etc.)                   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  MEMORY                                                         │
├────────────────────────────────────────────────────────────────┤
│  PK  id: UUID                                                   │
│  FK  profile_id: UUID                                           │
│      type: enum (STM, summary, LTM)                            │
│      content: text                                             │
│      importance: float (0.0-1.0)                               │
│      created_at: timestamp                                     │
│      expires_at: timestamp (for STM)                           │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  ONBOARDING_TARGET                                              │
├────────────────────────────────────────────────────────────────┤
│  PK  id: UUID                                                   │
│  FK  profile_id: UUID                                           │
│      dimension: string (tone, format, domain_context, etc.)    │
│      research_basis: string (citation: "Wu et al. 2024")       │
│      barrier_type: enum (binary, count, quality)               │
│      barrier_threshold: JSON (e.g. {min_interactions: 2})      │
│      satisfied: boolean                                        │
│      confidence: float (0.0-1.0)                               │
│      evidence: JSON[] (list of recorded evidence)              │
│      created_at: timestamp                                     │
│      satisfied_at: timestamp                                   │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Constraints

| Entity | Constraint | Rationale |
|--------|-----------|-----------|
| USER_PROFILE | Unique per user | One profile per user across all LLMs |
| USER_OUTPUT | Foreign key to profile | All outputs belong to a profile |
| ONBOARDING_TARGET | Research-backed | Every target must cite source |
| MEMORY | Expiry policy (STM) | Short-term memory auto-expires after 24h |

---

## 6. Sequence Diagrams

### 6.1 Standard Interaction Flow

```
User          LLM Client        IRIS Server       Data Store
 │                │                 │                │
 │  "Write email" │                 │                │
 ├───────────────>│                 │                │
 │                │  get_context()  │                │
 │                ├────────────────>│                │
 │                │                 │  load_profile  │
 │                │                 ├───────────────>│
 │                │                 │<───────────────┤
 │                │                 │  search_outputs│
 │                │                 ├───────────────>│
 │                │                 │<───────────────┤
 │                │                 │  rank_results  │
 │                │                 │  (most-relevant│
 │                │                 │   first)       │
 │                │  ContextResponse│                │
 │                │<────────────────┤                │
 │                │  {profile,      │                │
 │                │   outputs,      │                │
 │                │   memory}       │                │
 │                │                 │                │
 │                │  [Generate draft│                │
 │                │   using context]│                │
 │                │                 │                │
 │                │  check_draft()  │                │
 │                ├────────────────>│                │
 │                │                 │  load_profile  │
 │                │                 ├───────────────>│
 │                │                 │<───────────────┤
 │                │                 │  validate_tone │
 │                │                 │  validate_fmt  │
 │                │                 │  validate_bnd  │
 │                │  ValidationResult│               │
 │                │<────────────────┤                │
 │                │  {is_valid,     │                │
 │                │   issues[]}     │                │
 │                │                 │                │
 │                │  [Revise if     │                │
 │                │   needed]       │                │
 │                │                 │                │
 │  Email draft   │                 │                │
 │<───────────────┤                 │                │
 │                │                 │                │
 │  [User approves]                 │                │
 │                │                 │                │
 │                │  log_output()   │                │
 │                ├────────────────>│                │
 │                │                 │  store_output  │
 │                │                 ├───────────────>│
 │                │                 │<───────────────┤
 │                │                 │  embed_async   │
 │                │                 ├───────────────>│
 │                │  Success        │<───────────────┤
 │                │<────────────────┤                │
```

### 6.2 Onboarding Flow (GATE)

```
User          LLM Client        IRIS Server       GATE State
 │                │                 │                │
 │ "Let's set up  │                 │                │
 │  my profile"   │                 │                │
 ├───────────────>│                 │                │
 │                │  get_targets()  │                │
 │                ├────────────────>│                │
 │                │                 │  load_targets  │
 │                │                 ├───────────────>│
 │                │                 │  filter_open   │
 │                │                 │<───────────────┤
 │                │  TargetList[]   │                │
 │                │<────────────────┤                │
 │                │  {id, dimension,│                │
 │                │   research,     │                │
 │                │   barrier}      │                │
 │                │                 │                │
 │                │  [LLM decides   │                │
 │                │   strategy:     │                │
 │                │   edge-case]    │                │
 │                │                 │                │
 │  "Would you    │                 │                │
 │   prefer...?"  │                 │                │
 │<───────────────┤                 │                │
 │                │                 │                │
 │  "Option A"    │                 │                │
 ├───────────────>│                 │                │
 │                │  store_insight()│                │
 │                ├────────────────>│                │
 │                │  (target_id,    │                │
 │                │   evidence)     │                │
 │                │                 │  record_evidence
 │                │                 ├───────────────>│
 │                │                 │  check_barrier │
 │                │                 │<───────────────┤
 │                │  BarrierStatus  │                │
 │                │<────────────────┤                │
 │                │  {satisfied:    │                │
 │                │   false,        │                │
 │                │   needs_more}   │                │
 │                │                 │                │
 │                │  [LLM asks      │                │
 │                │   follow-up]    │                │
 │                │                 │                │
 │  ...           │                 │                │
 │                │                 │                │
 │                │  store_insight()│                │
 │                ├────────────────>│                │
 │                │                 │  check_barrier │
 │                │                 ├───────────────>│
 │                │  BarrierStatus  │<───────────────┤
 │                │<────────────────┤                │
 │                │  {satisfied:    │                │
 │                │   true}         │                │
 │                │                 │                │
 │                │  [Move to next  │                │
 │                │   target]       │                │
 │                │                 │                │
 │  ...           │                 │                │
 │                │                 │                │
 │  "Profile      │                 │                │
 │   complete!"   │                 │                │
 │<───────────────┤                 │                │
```

---

## 7. Deployment Architecture

### 7.1 Deployment View

```
┌────────────────────────────────────────────────────────────────┐
│                       CLIENT MACHINE                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LLM Client Application (Claude Desktop, VSCode, etc.)   │ │
│  │  OS: Windows / macOS / Linux                             │ │
│  └─────────────────────┬────────────────────────────────────┘ │
│                        │                                       │
│                        │ stdio / HTTP localhost                │
│                        │                                       │
│  ┌─────────────────────┴────────────────────────────────────┐ │
│  │  IRIS Server Process                                      │ │
│  │  ───────────────────                                     │ │
│  │  Runtime: Python 3.11+                                   │ │
│  │  Process: Single process, multi-threaded                 │ │
│  │  Port: stdio (default) or HTTP :8080                     │ │
│  │  Config: ~/.iris/config.yaml                              │ │
│  └─────────────────────┬────────────────────────────────────┘ │
│                        │                                       │
│                        │ File I/O                              │
│                        │                                       │
│  ┌─────────────────────┴────────────────────────────────────┐ │
│  │  File System Storage                                     │ │
│  │  ────────────────────                                    │ │
│  │  ~/.iris/data/                                            │ │
│  │    ├── profiles/    (JSON files)                        │ │
│  │    ├── outputs/     (text + metadata)                   │ │
│  │    ├── memory/      (STM/LTM)                           │ │
│  │    └── vectors/     (embeddings index)                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

Optional External Service:
┌────────────────────────────────────────────────────────────────┐
│  Embedding Service (Optional)                                  │
│  • OpenAI API (text-embedding-3-small)                         │
│  • Cohere Embed API                                            │
│  • Local: sentence-transformers                                │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 Installation & Configuration

| Deployment Model | Use Case | Complexity |
|-----------------|----------|------------|
| **Standalone (stdio)** | Single user, local development | ⭐ Low |
| **HTTP Server (localhost)** | Single user, multiple clients | ⭐⭐ Medium |
| **Shared Server (network)** | Team deployment, central profile | ⭐⭐⭐ High |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| `get_context()` latency | < 500ms (p95) | End-to-end tool call |
| `check_draft()` latency | < 200ms (p95) | Deterministic validation |
| `log_output()` sync | < 100ms (p95) | Store only, embedding async |
| Embedding generation | < 2s (async) | Background task |
| Concurrent requests | 10 parallel calls | No blocking on I/O |

### 8.2 Scalability

| Dimension | Current | Target (Future) |
|-----------|---------|----------------|
| Users per instance | 1 (single-user) | 100 (shared server) |
| Outputs per user | 10,000 | 100,000 |
| Profile size | < 100KB | < 1MB |
| Vector index size | < 500MB | < 5GB |

### 8.3 Reliability

| Requirement | Implementation |
|------------|----------------|
| Data durability | File-based storage, atomic writes |
| Crash recovery | Profile persisted after each update |
| Graceful degradation | If embedding fails, still return text-based results |
| Error handling | All tool calls return structured errors, never crash |

### 8.4 Security

| Aspect | Measure |
|--------|---------|
| Data storage | Local filesystem only, no cloud transmission |
| Profile privacy | No telemetry, no external API calls (except optional embedding) |
| Access control | File permissions (OS-level) |
| Secrets | No secrets stored (embedding API key via env var) |

### 8.5 Maintainability

| Aspect | Approach |
|--------|----------|
| Code structure | Layered architecture (tools → logic → data) |
| Testing | Unit tests (deterministic), integration tests (with mock LLM) |
| Logging | Structured JSON logs, DEBUG/INFO/ERROR levels |
| Monitoring | Prometheus metrics (optional) for request counts, latencies |

---

## 9. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **MCP Protocol** | Python MCP SDK | Official SDK, well-documented |
| **Server Runtime** | Python 3.11+ | Async support, type hints, rich ecosystem |
| **Package Manager** | uv | Fast, modern, deterministic |
| **Data Models** | Pydantic v2 | Validation, serialization, type safety |
| **Vector Search** | TBD (ChromaDB or FAISS) | Embedded, no external service |
| **Embeddings** | OpenAI API or sentence-transformers | Flexible (cloud or local) |
| **Storage** | File system (JSON/YAML) | Simple, portable, version-controllable |
| **Testing** | pytest + pytest-asyncio | Industry standard |
| **Linting** | ruff | Fast, comprehensive |
| **Documentation** | Markdown + LaTeX (diagrams) | Readable, professional |

---

## 10. Research Foundations

### 10.1 GATE (Li et al., ICLR 2025)

**Key Findings:**
- LLM-driven preference elicitation via edge-cases reveals tacit knowledge
- Forced binary choices outperform open-ended questions in technical domains
- 5-10 minute window optimal (18-30 questions across 6 sections)
- Works with open-source models (Mixtral matched GPT-4)

**Application in IRIS:**
- `get_targets()` exposes research-backed dimensions
- Barriers define minimum evidence thresholds
- LLM freely chooses question strategy (IRIS doesn't prescribe)

### 10.2 User Profile Roles (Wu et al., 2024)

**Key Findings:**
- User OUTPUTS (not inputs) are primary personalization driver
- Output-only format fits 2-5x more examples in context
- Most-relevant-first ordering significantly improves quality
- Semantic similarity from NON-user sources hurts performance

**Application in IRIS:**
- `log_output()` stores final user-approved outputs
- Retrieval engine ranks by relevance (BM25 + vector)
- Most relevant examples returned first
- No external content mixed with user outputs

### 10.3 Multi-Agent Personalization (Westhaeusser et al., 2025)

**Key Findings:**
- Coordinator → Operator → Validator → Generator pipeline
- Multi-tiered memory: STM (recent), Summaries, LTM (embeddings)
- Dynamic user profile built implicitly from interactions
- 96% retrieval accuracy vs 87% RAG baseline

**Application in IRIS:**
- Memory tiers (STM expires after 24h, LTM permanent)
- Profile confidence evolves over time
- Validation patterns (separate validator role)

---

## 11. Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| ARCH-001 | No internal LLM | User's LLM is powerful enough; IRIS = pure logic + data | 2026-07-22 |
| ARCH-002 | MCP protocol | Standard, LLM-agnostic, supported by major providers | 2026-07-22 |
| ARCH-003 | File-based storage (PoC) | Simple, portable, version-controllable | 2026-07-22 |
| ARCH-004 | Research-backed targets | Every onboarding dimension must cite evidence | 2026-07-22 |
| ARCH-005 | Two-layer design | Layer 1 (tools) works everywhere; Layer 2 (sampling) for advanced | 2026-07-22 |
| ARCH-006 | User outputs > inputs | Wu et al. 2024 research shows outputs drive personalization | 2026-07-22 |
| ARCH-007 | Most-relevant-first | Wu et al. 2024: position in context matters | 2026-07-22 |
| ARCH-008 | Tools start broad | Finer tools emerge from real usage patterns | 2026-07-22 |

---

## 12. Open Questions & Future Work

### 12.1 Open Questions

| ID | Question | Impact | Status |
|----|----------|--------|--------|
| Q-001 | Which vector store for production? | Performance | TBD |
| Q-002 | Embedding service: cloud or local? | Cost vs latency | TBD |
| Q-003 | Multi-user deployment architecture? | Scalability | Deferred (post-Segment 9) |
| Q-004 | Profile conflict resolution (user says X, does Y)? | UX | Research needed |

### 12.2 Future Enhancements (Out of Scope for v1.0)

| Enhancement | Description | Segment |
|------------|-------------|---------|
| VW Workday orchestration | Task execution, calendar, email | Post-production |
| Multi-language support | Full i18n/l10n | Post-production |
| Team profiles | Shared organizational knowledge | Post-production |
| Active learning | Proactive profile updates | Segment 8 extension |
| Analytics dashboard | Profile quality metrics, usage stats | Post-production |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol — standard for LLM-tool communication |
| **Anleitung** | German: "instruction" — protocol that guides LLM behavior |
| **GATE** | Guided Automated Tutoring Environment — preference elicitation method |
| **STM** | Short-Term Memory — recent conversation context (expires 24h) |
| **LTM** | Long-Term Memory — permanent user knowledge (embeddings) |
| **BM25** | Best Matching 25 — keyword-based ranking algorithm |
| **Cosine Similarity** | Vector similarity measure (for embeddings) |
| **Barrier** | Minimum evidence threshold for onboarding target satisfaction |
| **Self-Check** | Pattern where LLM validates own output via external tool |

---

## Appendix B: References

1. Li, B., Tamkin, A., Goodman, N., Andreas, J. (2025). "GATE: Guided Automated Tutoring Environment for Preference Elicitation." *ICLR 2025*.

2. Wu, T., Shi, Y., Rahmani, H., Ramineni, K., Yilmaz, E. (2024). "The Role of User Profiles in Personalized Language Model Responses." *arXiv:2406.17803*.

3. Westhaeusser, A., Minker, S., Zepf, M. (2025). "Multi-Agent Personalization with Persistent Memory." *arXiv:2510.07925*.

4. Model Context Protocol Specification: https://spec.modelcontextprotocol.io/

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-24 | IRIS Team | Initial professional architecture documentation |

**Review & Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Solution Architect | — | — | — |
| Technical Lead | — | — | — |
| Product Owner | — | — | — |
