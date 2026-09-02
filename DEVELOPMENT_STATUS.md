# KIM Development Status

**Last Updated:** 2026-09-02  
**Current State:** Segments 0-3 Complete, Retrieval Engine Working

---

## ✅ What's Built and Working

### **Segment 0: Project Skeleton** (Complete)
- ✅ Claude Code hooks (PRE-INFO explainer, architect radar, progress tracker)
- ✅ Skills (/start, /end, /dump, /status)
- ✅ Session tracking (.claude/last_session.json)
- ✅ Context dumps for session recovery
- ✅ Learning modules structure

### **Segment 1: MCP Server Foundation** (Complete)
- ✅ `src/server.py` — MCP server with stdio transport
- ✅ `get_context()` tool exposed
- ✅ MCP SDK integration (async/await)
- ✅ Demo user ID working (auth not yet wired)

### **Segment 2: Profile & Data Layer** (Complete - Refactored)

**Architecture Change:** Switched from PostgreSQL to file-based storage for local-per-user deployment model.

### **Segment 3: Retrieval Engine** (Complete)
- ✅ Pydantic schema (`src/profile/schema.py`)
  - UserProfile model with research-backed enums
  - Tone, format preferences, boundaries, confidence scoring
  - `format_profile_for_llm()` markdown formatter

- ✅ Database layer (`src/database/`)
  - SQLAlchemy ORM models (3NF normalized)
  - UserProfileModel, UserToneModel, UserBoundaryModel, UserProjectModel
  - UserOutputModel (ready for Segment 3)
  - MemoryEntryModel (ready for multi-tiered memory)
  - OnboardingTargetModel (ready for GATE)

- ✅ Database storage (`src/profile/store_db.py`)
  - ProfileStoreDB: full async CRUD
  - Pydantic ↔ SQLAlchemy conversion
  - Relationship management (cascading deletes)
  - get_or_create_profile_db()

- ✅ Infrastructure
  - Docker Compose (pgvector/postgres:pg17)
  - init_db.sql (3NF + vector columns)
  - Health checks, auto-initialization

- ✅ Tests
  - tests/test_profile_db.py (full CRUD + relationships)
  - pytest + asyncio working

- ✅ **File-based storage** (`src/storage/`)
  - ProfileStore: JSON files in `~/.kim/profiles/`
  - OutputStore: JSON files in `~/.kim/outputs/{user_id}/`
  - EmbeddingStore: NumPy arrays in `~/.kim/embeddings/`
  - 100% transparent (human-readable)
  - No Docker required

- ✅ **Hybrid retrieval** (`src/retrieval/`)
  - BM25 keyword search (rank-bm25 library)
  - Vector similarity (cosine, NumPy)
  - Hybrid ranking: 0.5*BM25 + 0.5*vector
  - Wu et al. 2024: most-relevant-first ordering

- ✅ **OpenAI embeddings** (`src/retrieval/embeddings.py`)
  - text-embedding-3-small (768 dimensions)
  - Batch embedding support
  - Cost tracking

- ✅ **MCP Tools**
  - `get_context(query)` → profile + ranked outputs ✅
  - `log_output(content, context, type)` → store + embed ✅

- ✅ **Storage inspector** (`src/inspect.py`)
  - CLI tool: `python -m src.inspect`
  - Shows profile, outputs, embeddings, sizes
  - 100% transparency into what KIM knows

**Git:** 4 commits on master (latest: a612bdb)

---

## 🎯 Core Function (Confirmed Design)

KIM is an **agentic validation loop**:

```
1. User → LLM: "Write email"
2. LLM → KIM: get_context(query)
   ↳ Returns: profile + ranked past outputs
3. LLM generates draft
4. LLM → KIM: check_draft(draft)
   ├─ Stage 1: Deterministic checks (onboarding rules)
   └─ Stage 2: MCP sampling (ask AI in fresh context)
5. KIM → LLM: validation feedback
6. IF failed: LLM revises → back to step 4
7. IF passed: Show to user
8. LLM → KIM: log_output(final)
   ↳ Store + embed for future retrieval
```

**Key Innovation:** Two-stage validation
- Deterministic (free, fast) catches style violations
- MCP sampling (uses user's LLM) catches semantic failures
- Fresh context = no generation bias

---

## ✅ Built and Working

### **Segment 3: Retrieval Engine** ✅ COMPLETE

**What was built:**

**What to build:**
```
src/retrieval/
├── embeddings.py       # OpenAI text-embedding-3-small integration
├── hybrid.py           # BM25 + vector similarity ranking
└── ranker.py           # Wu et al. 2024 implementation (most-relevant-first)

src/tools/
└── log_output.py       # MCP tool for storing outputs

Update:
├── src/server.py       # Add log_output tool, update get_context()
└── src/database/       # User output storage with embeddings
```

**Design Decisions (All Made):**
- ✅ Embedding: OpenAI `text-embedding-3-small` (768 dimensions)
- ✅ BM25: Use `rank-bm25` Python package
- ✅ Hybrid scoring: `0.5 * bm25 + 0.5 * vector`
- ✅ Top-K: Return 3-5 most relevant outputs
- ✅ Wu et al. 2024: Most-relevant-first ordering

**Dependencies:**
- OpenAI API key (user provides via environment variable)
- Packages: `openai`, `rank-bm25`
- PostgreSQL with pgvector (already running in Docker)

**Estimated:** 2-3 work sessions

---

### **Segment 4: Draft Validation**

**Goal:** Implement `check_draft()` with two-stage validation

**What to build:**
```
src/validation/
├── deterministic.py    # Pattern matching, keyword checks, format detection
├── mcp_validator.py    # MCP sampling integration (fresh context)
└── strategy.py         # Adaptive validation (MCP sampling > deterministic)

src/tools/
└── check_draft.py      # MCP tool for validation

config/settings.yaml
└── validation:
      strategy_priority: [mcp_sampling, deterministic]
```

**Design Decisions (All Made):**
- ✅ Stage 1: Deterministic (formality, jargon, format, length, language)
- ✅ Stage 2: MCP sampling (semantic check in fresh context)
- ✅ Adaptive: Try MCP sampling, fallback to deterministic only
- ✅ No forced dependencies (works without API keys)

**Deterministic Checks:**
- Formality patterns (regex: "Dear Sir" vs "Hi")
- Jargon keywords (blacklist from profile boundaries)
- Format detection (bullet points vs paragraphs)
- Word count (profile length preferences)
- Language detection (langdetect library)

**MCP Sampling Check:**
- Capability detection (does client support sampling?)
- Fresh context validation prompt
- JSON response format
- Uses user's LLM (free, no API key needed)

**Dependencies:**
- MCP SDK sampling support (Claude Code has this)
- Packages: `langdetect`, `mcp` (already have)

**Estimated:** 2-3 work sessions

---

### **Segment 8: Output Logging**

**Goal:** Store user outputs for future retrieval

**What to build:**
- Already designed as part of Segment 3
- `log_output()` MCP tool
- Store to user_output table (schema ready)
- Embed content using Segment 3 embeddings
- Index for retrieval (PostgreSQL GIN + pgvector)

**Estimated:** 1 work session (builds alongside Segment 3)

---

## 🟡 Needs Design First

### **Segment 5: GATE Onboarding**

**Status:** Research complete, specific targets need defining

**Design Questions:**
- Which 10-15 onboarding dimensions? (tone, format, length, boundaries, ...)
- What research backs each dimension?
- What barrier thresholds count as "satisfied"?
- How does evidence accumulation work?

**Estimated Design:** 1 session  
**Estimated Build:** 3-4 sessions

**Action:** Design session after Segments 3-4 working

---

### **Segment 6: The Anleitung**

**Status:** Concept clear, write after Segments 3-4 built

**What it is:** Protocol instructions for Layer 1 LLMs
- When to call get_context vs check_draft
- How to handle validation failures
- Onboarding flow guidance
- Best practices for tool usage

**Estimated:** 1-2 sessions

**Action:** Write after experiencing how tools actually behave

---

## ⏸️ Too Early (Wait Until Core Works)

### **Segment 7: Advanced Layer 2 Orchestration**
- Core (MCP sampling for validation) is in Segment 4
- Complex multi-step flows can wait

### **Segment 9: Production Hardening**
- Error handling, logging, security
- Performance optimization
- Distribution model
- Tackle after MVP working

---

## 🎯 Minimum Viable KIM (MVP)

**After Segments 3-4, you have:**

```
✅ MCP server running
✅ get_context() → profile + ranked outputs
✅ check_draft() → deterministic + MCP sampling validation
✅ log_output() → store + embed user outputs
✅ PostgreSQL + pgvector storage
✅ Agentic validation loop working

USER EXPERIENCE:
- LLM gets personalized context (profile + past examples)
- LLM validates drafts independently (two-stage check)
- LLM learns from past outputs (ranked by relevance)
- Works across any MCP client (Claude Code, others)

MISSING (for full system):
- Onboarding flow (manual profile editing for now)
- The Anleitung (LLM figures it out from tool descriptions)
```

**MVP is fully usable for real work.**

---

## 📊 Current Architecture State

```
KIM MCP Server
├── ✅ MCP Interface (stdio transport)
├── ✅ Profile Storage (Pydantic + PostgreSQL)
├── 🟡 Retrieval Engine (next: Segment 3)
├── 🟡 Validation Engine (next: Segment 4)
├── ⏸️ GATE Onboarding (design needed)
└── ⏸️ The Anleitung (after tools built)

Tools Exposed:
├── ✅ get_context(query) — working (profile only)
├── 🟡 check_draft(draft) — next: Segment 4
├── 🟡 log_output(text) — next: Segment 3
├── ⏸️ get_targets() — Segment 5
└── ⏸️ store_insight() — Segment 5

Data Layer:
├── ✅ user_profile (with relationships)
├── ✅ user_tone, user_boundary, user_project
├── ✅ user_output (schema ready, empty)
├── ✅ memory_entry (schema ready)
└── ✅ onboarding_target (schema ready)
```

---

## 🚀 Recommended Next Steps

### **Option A: Build MVP (Segments 3-4)**
```
1. Segment 3: Retrieval Engine (2-3 sessions)
   → get_context() returns profile + ranked outputs
   
2. Segment 4: Draft Validation (2-3 sessions)
   → check_draft() two-stage validation
   
3. Test with real Claude Code session
   → Experience the agentic loop firsthand
   
4. Then decide: onboarding vs. production hardening
```

### **Option B: Design Onboarding First**
```
1. Design session: Define 10-15 GATE targets
   → Research-backed dimensions
   → Barrier thresholds
   
2. Then build Segment 5 (onboarding)
3. Then build Segments 3-4 (retrieval + validation)
```

**Recommendation:** **Option A** — Build the core loop first. You'll understand the system better after using it, which will inform better onboarding design.

---

## 📦 Dependencies Summary

### **Already Installed:**
- ✅ Python 3.11+
- ✅ uv (package manager)
- ✅ mcp SDK
- ✅ pydantic
- ✅ sqlalchemy + asyncpg
- ✅ pytest
- ✅ ruff

### **Need to Add (Segment 3):**
- `openai` — for embeddings
- `rank-bm25` — for keyword ranking
- OpenAI API key (environment variable: `OPENAI_API_KEY`)

### **Optional (Later):**
- `langdetect` — for language detection (Segment 4)
- `anthropic` — for Haiku fallback (optional, if no MCP sampling)

---

## 🎓 Learning & Certification

**Architect Radar has detected:**
- User Modeling & Preference Elicitation (GATE methodology)
- Deep-dive: `learning/07_user_profiles/README.md`

**Relevant certification topics:**
- MCP sampling (Layer 2)
- Tool design (granularity, composition)
- Agentic patterns (validation loops)
- Research application (GATE, Wu et al., Westhaeusser et al.)

---

## ✅ Summary: Ready for Full Development

**Status:** YES — everything needed for Segments 3-4 is specified

**What's clear:**
- ✅ Core function (agentic validation loop)
- ✅ Architecture (two-stage validation)
- ✅ Design decisions (embeddings, BM25, MCP sampling)
- ✅ Implementation plan (file structure, dependencies)
- ✅ Tests strategy (mock embeddings, mock MCP sampling)

**No blockers.** Can start building Segment 3 immediately.

**Estimated to MVP:** 4-6 work sessions (Segments 3-4 + testing)

---

*Generated by: /start recovery (2026-09-02)*
