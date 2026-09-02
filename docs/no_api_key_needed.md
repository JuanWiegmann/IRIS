# Why KIM Doesn't Need OpenAI API Key

## Summary

**KIM works WITHOUT an OpenAI API key** for all core functionality.

---

## What Works WITHOUT API Key

### ✅ Draft Validation (Full Functionality)

**How it works:**
1. **Deterministic checks** — Pure pattern matching (no LLM)
   - Tone detection (formal vs casual)
   - Format checking (bullets vs paragraphs)
   - Jargon detection (keyword blacklist)
   - Security patterns (hardcoded credentials, SQL injection)

2. **Semantic validation** — Uses YOUR LLM via MCP sampling
   - KIM calls back to your LLM (Claude Code)
   - Your LLM validates in fresh context
   - No OpenAI API needed
   - No additional cost (uses your Claude subscription)

**Architecture:**
```
Your LLM generates draft
  ↓
KIM: check_draft(draft)
  ├─ Deterministic checks (no API)
  └─ MCP sampling → YOUR LLM validates (no OpenAI!)
  ↓
KIM returns feedback
  ↓
Your LLM revises if needed
```

---

### ✅ Profile Storage

- Stores your preferences in `~/.kim/profiles/`
- Pure file I/O (no API needed)
- Reads tone, format, boundaries

---

### ✅ BM25 Keyword Search

- Searches past outputs by keywords
- rank-bm25 library (no API)
- Works for retrieval (just no semantic similarity)

---

## What NEEDS API Key

### 📊 Semantic Search (Embeddings Only)

**When you call `log_output()`:**
- KIM tries to embed the text with OpenAI
- If no API key: Skips embedding, stores text only
- **Result:** Retrieval uses BM25 only (keyword search)

**When you call `get_context()`:**
- KIM tries hybrid search (BM25 + vector)
- If no embeddings: Falls back to BM25 only
- **Result:** Still returns relevant outputs (keyword-based)

**Cost:** ~$0.02 per 1M tokens (very cheap)

---

## Degradation Behavior

| Feature | With API Key | Without API Key |
|---------|-------------|-----------------|
| **Validation** | ✅ Full (deterministic + MCP) | ✅ Full (same) |
| **Draft Checking** | ✅ Full | ✅ Full |
| **Profile Storage** | ✅ Full | ✅ Full |
| **Retrieval** | ✅ Hybrid (BM25 + vector) | ✅ BM25 only |
| **Semantic Search** | ✅ Yes | ⚠️ No (keyword only) |

**Bottom line:** System is **fully functional** without API key!

---

## MCP Sampling vs OpenAI

### MCP Sampling (No API Key Needed)

**What it is:**
- KIM calls YOUR LLM (Claude Code) in fresh context
- User's Claude subscription covers it
- No OpenAI involved

**Used for:**
- Semantic validation ("Is this draft usable?")
- Quality checks ("Is this code correct?")
- Ponytail integration (code quality)

**How it works:**
```python
# KIM requests validation from YOUR LLM
response = await request_sampling(
    prompt="Validate this draft: ...",
    model_preferences=["haiku", "sonnet"]
)
# Your Claude Code responds (no OpenAI)
```

---

### OpenAI Embeddings (API Key Needed)

**What it is:**
- Converts text to 768-dimensional vectors
- Used for semantic similarity search

**Used for:**
- Finding similar past outputs
- "Email to team" → finds similar emails semantically

**Alternative:**
- BM25 keyword search works without it
- "Email to team" → finds outputs with those keywords

---

## Why This Architecture?

**Design goal:** Zero forced dependencies

1. **User owns their LLM** — Use Claude, ChatGPT, Copilot, any MCP client
2. **No vendor lock-in** — OpenAI is optional enhancement
3. **Graceful degradation** — Works without embeddings
4. **Cost control** — User decides if semantic search is worth $0.02/1M tokens

**Philosophy:** KIM augments your LLM, doesn't replace or require additional services

---

## Configuration Examples

### Minimal (No API Key)

```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\KIM"
    }
  }
}
```

**What works:**
- ✅ All validation
- ✅ All profile features
- ✅ BM25 retrieval

---

### Full Featured (With API Key)

```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\KIM",
      "env": {
        "OPENAI_API_KEY": "sk-your-key"
      }
    }
  }
}
```

**What works:**
- ✅ All validation
- ✅ All profile features
- ✅ Hybrid retrieval (BM25 + semantic)

---

## Summary

**KIM's core value proposition works WITHOUT OpenAI:**
- Your LLM generates content
- KIM validates it (deterministic + MCP sampling)
- KIM stores it (file-based)
- KIM retrieves it (BM25 keyword search)

**OpenAI is just an enhancement:**
- Adds semantic search
- Costs ~$0.02 per 1M tokens
- Totally optional

**You decide:** Is semantic search worth the cost?
