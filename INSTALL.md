# IRIS Installation

## Installation (Any Machine, Any User)

```bash
git clone <IRIS-repo>
cd IRIS
python install.py
```

**Then restart Claude Code.** Done.

*(Windows, macOS, Linux — same process for everyone)*

---

## What Gets Installed

**Python dependencies:**
- `mcp` — MCP SDK
- `pydantic` — Data models
- `sqlalchemy` + `asyncpg` + `pgvector` — Database
- `openai` — Embeddings
- `rank-bm25` — Text search

**IRIS package:**
- `iris-server` command (portable, no hardcoded paths)
- Works from any directory
- Same on all machines

**Data directories:**
```
~/.iris/
├── data/profiles/
├── data/outputs/
├── data/onboarding/
└── logs/
```

**Claude Code config:**
- Desktop app: `claude_desktop_config.json`
- CLI: `~/.claude/mcp.json`
- IRIS loads in all sessions automatically

---

## Prerequisites

- Python 3.11+
- Claude Code installed
- (Optional) OpenAI API key for semantic search

---

## First Use

1. Restart Claude Code
2. Run `/startIris` (5-minute onboarding)
3. IRIS auto-loads your profile in all future sessions

---

## Verification

```bash
# Command exists
which iris-server

# Package installed
pip list | grep iris-mcp

# Server starts
timeout 2 iris-server < /dev/null  # Exit 124 = success

# Config exists
cat ~/.claude/mcp.json
```

---

## Troubleshooting

**Command not found:**
```bash
pip install -e .
# Restart terminal
```

**MCP connection fails:**
- Check: `~/.iris/logs/iris_server.log`
- Verify: `~/.claude/mcp.json` contains `"iris"`
- Test: `iris-server < /dev/null` (should run without errors)

**ONBOARDING_REQUIRED:**
- Expected on first use
- Run `/startIris` to create profile

---

## Why Portable?

**No hardcoded paths:**
- Username: Works for any user
- Python: Found via PATH
- Repo location: Irrelevant after install

**One install process:**
- Same for everyone
- Clone → install → restart
- No per-machine configuration
