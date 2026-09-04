# Learning Module 01: MCP Tools & Server

**Certification Topic:** MCP Protocol, Tool Design, Server Architecture  
**What We Built:** MCP server with `get_context()` tool (stub)  
**Time:** ~30 minutes

---

## WHY — Why This Matters

### The Problem
LLMs are powerful, but they don't know anything about YOU specifically. Every time you ask ChatGPT, Claude, or Copilot a question, they start from zero. No memory of your preferences, your writing style, your boundaries.

This means:
- You repeat yourself constantly ("I prefer bullet points", "keep it technical but accessible")
- The LLM generates text that doesn't match YOUR voice
- No learning between sessions or across different LLMs

### The MCP Solution
**Model Context Protocol (MCP)** is a standard way for LLMs to call external tools. Instead of the LLM guessing your preferences, it can **ask IRIS** via MCP.

IRIS is like a "personality card" that follows you across ALL LLMs:
- Claude asks IRIS: "How should I write for this user?"
- Copilot asks IRIS: "What's this user's tone preference?"
- ChatGPT asks IRIS: "What are relevant past outputs?"

**One profile. All LLMs.**

### Why MCP, Not REST API?
- **Standard:** Supported by Claude, Copilot, and growing ecosystem
- **Simple:** stdio transport (no HTTP server needed for local use)
- **Discovery:** LLMs auto-discover your tools (no manual registration)
- **Typed:** JSON Schema for validation (prevents errors)

---

## WHAT — What We Built

### Architecture
```
User's LLM (Claude, Copilot, ChatGPT)
    │
    │ MCP Protocol (JSON-RPC 2.0)
    │ via stdio or HTTP
    ▼
IRIS MCP Server (src/server.py)
    │
    ├─ list_tools() → Tool[]
    │   Returns available tools with schemas
    │
    └─ call_tool(name, args) → TextContent[]
        Executes the requested tool
```

### What We Implemented

**1. Server Setup (`src/server.py`)**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("iris-server")
```
- Creates an MCP server instance
- Name: "iris-server" (identifies this server to clients)

**2. Tool Registration**
```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_context",
            description="...",
            inputSchema={...}
        )
    ]
```
- Decorator registers the function as a tool lister
- LLMs call this to discover what tools are available
- Returns list of Tool objects (name, description, schema)

**3. Tool Execution**
```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "get_context":
        return await handle_get_context(arguments)
```
- Decorator registers the function as the tool executor
- Routes tool calls to the correct handler
- Returns list of TextContent blocks (MCP format)

**4. The `get_context()` Tool**
```python
Tool(
    name="get_context",
    description="Retrieve personalized context...",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "..."}
        },
        "required": ["query"]
    }
)
```

**What it does:**
- Takes a query (e.g., "Write an email")
- Returns user profile + relevant past outputs
- **Currently:** Returns MOCK data (Segment 1 stub)
- **Later:** Will load real data (Segment 2 & 3)

**Why mock data?**
We need to verify the MCP round-trip works BEFORE adding complexity. Stub data proves:
- Server starts correctly
- LLM can discover tools
- Tool calls execute
- Responses are formatted correctly

---

## HOW — How It Works

### MCP Protocol Flow

**1. Server Startup**
```python
async with stdio_server() as (read_stream, write_stream):
    await app.run(read_stream, write_stream, ...)
```
- Server reads from stdin, writes to stdout
- Uses JSON-RPC 2.0 (same as LSP, if you know that)
- Waits for LLM to send requests

**2. Tool Discovery (LLM → IRIS)**
```json
// LLM sends:
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}

// IRIS responds:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_context",
        "description": "Retrieve personalized context...",
        "inputSchema": {...}
      }
    ]
  }
}
```

**3. Tool Execution (LLM → IRIS)**
```json
// LLM sends:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_context",
    "arguments": {"query": "Write an email"}
  },
  "id": 2
}

// IRIS responds:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "# Personalized Context...\n\n## User Profile\n..."
      }
    ]
  }
}
```

**4. LLM Uses Context**
The LLM now has:
- User's tone preference (professional but approachable)
- Format preference (bullet points)
- Relevant past examples

It generates a response matching YOUR style.

---

### Key Concepts

#### 1. **Async/Await**
```python
async def handle_get_context(arguments: dict) -> list[TextContent]:
    # Async allows non-blocking I/O
    # Future: will await database reads, vector searches
```
- MCP SDK is async (modern Python pattern)
- Allows multiple concurrent tool calls without blocking
- Essential for retrieval (Segment 3) and embeddings (Segment 8)

#### 2. **Tool Schema (JSON Schema)**
```python
inputSchema={
    "type": "object",
    "properties": {
        "query": {"type": "string"}
    },
    "required": ["query"]
}
```
- Defines what arguments the tool accepts
- LLM validates before calling (prevents errors)
- Auto-generates documentation

#### 3. **TextContent Response**
```python
return [
    TextContent(type="text", text="...")
]
```
- MCP responses are lists of content blocks
- Can be text, images, resources
- We use text (markdown-formatted for LLM)

#### 4. **Stub Pattern**
```python
# MOCK DATA (Segment 1 stub)
# This will be replaced with real data in Segment 2 & 3
mock_response = f"""# Personalized Context...
"""
```
- Stub = placeholder that returns fake data
- Verifies interface works before implementation
- Replaced incrementally (Segment 2: real profile, Segment 3: real retrieval)

---

## THINK ABOUT — Reflection Questions

### Architecture Questions

**Q1: Why not just store the profile in the LLM's context directly?**

Think about:
- Context window limits (you'd waste space repeating profile every message)
- Multiple LLMs (how do you sync profiles?)
- Privacy (do you want your profile sent to OpenAI/Microsoft/Google?)

**A:** MCP keeps profile local. LLM requests it only when needed. One profile, all LLMs.

---

**Q2: Why use stdio instead of HTTP for local development?**

Think about:
- Security (HTTP = open port, potential attack surface)
- Simplicity (no CORS, auth, TLS)
- Performance (no network stack overhead)

**A:** stdio is simpler for single-user local deployments. HTTP is for shared/remote servers (Segment 9).

---

**Q3: Why return mock data instead of building the full retrieval engine first?**

Think about:
- What if MCP protocol doesn't work?
- What if tool schema is wrong?
- What if response format is incompatible?

**A:** Stub proves the interface BEFORE investing in implementation. Fail fast on protocol issues.

---

### Design Questions

**Q4: Should `get_context()` take the full conversation history, or just the current query?**

Current design: just `query` (one string).

Think about:
- **Pro (full history):** More context for relevance ranking
- **Con (full history):** Large payloads, privacy concerns, complexity
- **Trade-off:** How much does history actually improve retrieval?

**Decision:** Start simple (query only). Add history if needed (future).

---

**Q5: Why return markdown text instead of structured JSON?**

Current design: Returns formatted markdown string.

Think about:
- **Pro (markdown):** LLMs understand markdown natively, easy to read
- **Con (markdown):** LLM must parse, can't validate structure
- **Pro (JSON):** Structured, typed, validatable
- **Con (JSON):** LLM must format for user, extra step

**Decision:** Markdown = simpler for LLM consumption. JSON if we need machine processing later.

---

## Certification Relevance

### Claude Certified Architect – Professional

**Topics Covered:**
1. **MCP Protocol** (Tool registration, discovery, execution)
2. **Tool Design** (Schemas, naming, descriptions)
3. **Async Patterns** (Event loops, non-blocking I/O)
4. **Testing Strategies** (Stub data, interface verification)
5. **Architecture Decisions** (When to stub, when to build)

**Exam-Style Questions:**

**Q1:** Your MCP tool needs to return multiple pieces of data (profile + outputs + memory). Should you:
- A) Create one tool that returns everything
- B) Create three separate tools (get_profile, get_outputs, get_memory)
- C) Create one tool with optional flags

**Answer:** It depends on usage patterns.
- If LLMs ALWAYS need all three → **A** (fewer round-trips)
- If LLMs sometimes need only one → **B** (flexibility, granular control)
- If usage is mixed → **C** (balance)

**Our choice:** A (get_context returns everything). Why? Wu et al. 2024 shows profile + outputs together improves quality. One call = simpler for LLMs.

---

**Q2:** Why use JSON Schema for tool input validation?

**A:** 
- Prevents runtime errors (LLM can't call tool with wrong types)
- Auto-generates documentation (LLM knows what to pass)
- Type safety (Python + Pydantic can validate)

---

## Next Steps

**Segment 2: Profile & Data Layer**
- Define User Profile schema (Pydantic)
- Implement profile storage (read/write)
- Replace mock data in `get_context()` with real profile

**What Changes:**
```python
# Before (Segment 1):
mock_response = "## User Profile\n- Language: German\n..."

# After (Segment 2):
profile = await load_profile(user_id)
response = format_profile(profile)
```

---

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [JSON Schema](https://json-schema.org/)
- Wu et al. (2024): "User Profile Roles in Personalized LLM Responses"

---

**Learning Path:**
- ✅ Module 00: Project Setup & Persistence
- ✅ **Module 01: MCP Tools & Server** ← You are here
- ⏭️ Module 02: Data Modeling (next)
