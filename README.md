# KIM — Knowledge & Interaction Middleware

**Personalized AI communication layer for ANY LLM**

KIM is an MCP middleware server that provides personalization, validation, and memory to Claude Code, ChatGPT, Copilot, and any MCP-capable LLM.

---

## What KIM Does

- **📝 Personalizes responses** — Learns your tone, format preferences, and boundaries
- **✅ Validates drafts** — Checks emails, code, and documents before showing them to you
- **🧠 Remembers context** — Stores past outputs and retrieves relevant examples
- **🎯 Use-case aware** — Different validation for messaging, coding, and Mendix development

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/you/KIM.git
cd KIM
```

### 2. Install KIM

**For Users (Simple):**
```bash
python install.py
```

**For Developers:**
```bash
python -m pip install -e .
```

### 3. Configure API Key (OPTIONAL)

**OpenAI API key is OPTIONAL!**

KIM works WITHOUT it:
- ✅ Validation (uses your LLM via MCP)
- ✅ Draft checking
- ✅ Profile storage

**Only needed for:** Semantic search of past outputs (embeddings)

**Without key:** Retrieval uses BM25 keyword search only (still works!)

**Get key (optional):** https://platform.openai.com/api-keys

The setup script will ask, or press Enter to skip.

### 4. Restart Claude Code

Close and reopen Claude Code completely.

### 5. Test KIM

In Claude Code, ask:
```
What MCP tools are available?
```

You should see: `get_context`, `log_output`, `check_draft`

---

## How It Works

```
You: "Write an email to the team"

Your LLM → KIM: get_context("email to team")
KIM → Your LLM: Profile + past emails (ranked by relevance)

Your LLM generates draft using personalized context

Your LLM → KIM: check_draft(draft)
KIM → Your LLM: ✅ Passed OR ❌ Issues found (fix before showing)

Your LLM → You: Personalized, validated email

Your LLM → KIM: log_output(final_email)
KIM: Stores + embeds for future retrieval
```

**The magic:** Your LLM self-validates using KIM as an independent oracle.

---

## Features

### ✅ Built (MVP Ready)

- **File-based storage** — 100% transparent (`~/.kim/` JSON files)
- **Hybrid retrieval** — BM25 keyword + vector similarity
- **Use-case detection** — Messaging vs Coding vs Mendix
- **Draft validation** — Deterministic rules + semantic checks
- **Comprehensive logging** — See every operation (`python -m src.log_viewer`)

### ⏳ Coming Soon

- **GATE onboarding** — Target-based preference elicitation
- **MCP sampling** — Semantic validation in fresh context (no bias)
- **The Anleitung** — Protocol instructions for optimal LLM usage

---

## MCP Tools

| Tool | What It Does |
|------|--------------|
| `get_context(query)` | Returns profile + top-5 relevant past outputs |
| `log_output(content, context, type)` | Stores output + embeds for future retrieval |
| `check_draft(draft, context)` | Validates draft (tone, format, use-case rules) |

---

## Use Cases

### 📧 Messaging (Emails, Documents)

**Checks:**
- Tone (formal vs casual markers)
- Format (bullets vs paragraphs)
- Jargon (user-specific blacklist)
- Length (concise vs detailed preference)

### 💻 Coding (Python, JS, etc.)

**Checks:**
- TODO/FIXME markers
- Print statements (should use logging)
- Bare except clauses
- Hardcoded credentials
- SQL injection risks
- **Ponytail integration** (if installed)

### 🏗️ Mendix (Low-Code Development)

**Checks:**
- Entity naming (singular not plural)
- XML structure basics
- Microflow patterns
- **No CLI execution** (Mendix CLI is beta)

---

## Storage

**Location:** `~/.kim/`

```
~/.kim/
├── profiles/
│   └── {user_id}.json          # Your profile (tone, style, boundaries)
├── outputs/
│   └── {user_id}/
│       ├── 001_email_team.json # Past outputs with metadata
│       └── ...
├── embeddings/
│   └── {user_id}.npy           # Vector embeddings (NumPy)
└── logs/
    └── kim_server.log          # Detailed operation logs
```

**Inspect storage:**
```bash
python -m src.inspect
```

---

## Monitoring

**View logs:**
```bash
python -m src.log_viewer --follow
```

**What you'll see:**
- Every tool call
- Validation decisions
- Retrieval rankings
- Embedding operations
- Performance timing

**Log location:** `~/.kim/logs/kim_server.log`

---

## Architecture

**Research-backed:**
- **GATE** (Li et al., ICLR 2025) — Target-based preference elicitation
- **Wu et al. (2024)** — User outputs > inputs for personalization
- **Westhaeusser et al. (2025)** — Multi-tiered memory

**Technology:**
- Python 3.11+
- MCP SDK (stdio transport)
- OpenAI embeddings (text-embedding-3-small, 768 dim)
- BM25 + vector similarity (hybrid retrieval)
- File-based storage (no database required)

---

## Configuration

**Manual config:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\KIM",
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "KIM_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Environment variables:**
- `OPENAI_API_KEY` — Required for embeddings
- `KIM_LOG_LEVEL` — DEBUG/INFO/WARNING/ERROR
- `KIM_DATA_DIR` — Storage location (default: `~/.kim/`)

---

## Development

```bash
# Install in development mode
python -m pip install -e .

# Run tests
python -m pytest tests/ -v

# View logs
python -m src.log_viewer --follow --detailed

# Inspect storage
python -m src.inspect --detailed
```

---

## Documentation

- **Setup Guide:** [SETUP_MCP.md](SETUP_MCP.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Development Status:** [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md)
- **Ponytail Integration:** [docs/ponytail_integration.md](docs/ponytail_integration.md)

---

## Contributing

See [CLAUDE.md](CLAUDE.md) for project conventions and design principles.

---

## License

[Add your license here]

---

## Support

- **Issues:** https://github.com/you/KIM/issues
- **Logs:** Share `~/.kim/logs/kim_server.log`

---

**Built with:** Python, MCP SDK, OpenAI, NumPy, rank-bm25

**Certified:** Claude Certified Architect – Professional

**Status:** MVP (Segments 0-4 complete, ready for testing)
