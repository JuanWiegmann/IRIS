# KIM MCP Server Setup Guide

## Prerequisites

1. **Claude Code** installed (desktop app or CLI)
2. **Python 3.11+** installed
3. **OpenAI API key** (for embeddings)

---

## Step 1: Install KIM Dependencies

```bash
cd C:\Users\AV013EV\dev\work\KIM

# Install with pip
python -m pip install -e .

# Verify installation
python -m src.inspect
# Should show: "No users found." (normal for first run)
```

---

## Step 2: Set OpenAI API Key

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-your-key-here"

# OR create .env file in KIM directory
echo OPENAI_API_KEY=sk-your-key-here > .env
```

**Get API key:** https://platform.openai.com/api-keys

---

## Step 3: Configure Claude Code MCP

### Option A: Claude Code Desktop App

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

Full path: `C:\Users\AV013EV\AppData\Roaming\Claude\claude_desktop_config.json`

**Edit the file:**
```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Users\\AV013EV\\dev\\work\\KIM",
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "KIM_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**Notes:**
- Use double backslashes `\\` in Windows paths
- Replace `sk-your-key-here` with your actual key
- `KIM_LOG_LEVEL=DEBUG` enables detailed logging

### Option B: Claude Code CLI

Create `mcp_config.json` in KIM directory:

```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Users\\AV013EV\\dev\\work\\KIM",
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "KIM_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

Then run:
```bash
claude --mcp-config mcp_config.json
```

---

## Step 4: Restart Claude Code

**Desktop App:**
- Close Claude Code completely
- Reopen it

**CLI:**
- Start new session: `claude`

---

## Step 5: Verify KIM is Connected

In Claude Code, ask:

```
What MCP tools are available?
```

**Expected response:** Should list:
- `get_context` - Retrieve personalized context
- `log_output` - Store user outputs
- `check_draft` - Validate drafts

If you see these, **KIM is connected!** ✅

---

## Step 6: Test KIM

### Test 1: Check Context (should work immediately)

```
Call the get_context tool with query "test connection"
```

**Expected:** Returns default profile (low confidence, needs onboarding)

### Test 2: Log an Output

```
Call log_output with:
- content: "Hi team, this is a test email"
- context: "test email"
- output_type: "email"
```

**Expected:** "✅ Output logged successfully"

### Test 3: Get Context Again (should show the logged output)

```
Call get_context with query "email to team"
```

**Expected:** Returns profile + the test email you just logged (ranked by relevance)

### Test 4: Validate a Draft

```
Call check_draft with:
- draft: "Dear Sir or Madam, I am writing to inform you..."
- context: "team email"
```

**Expected:** Should flag "too formal" if user profile prefers casual tone

---

## Logs: Where to Find Them

KIM logs to two places:

### 1. KIM Server Log (detailed backend)

**Location:** `~/.kim/logs/kim_server.log`

Full path: `C:\Users\AV013EV\.kim\logs\kim_server.log`

**View in real-time:**
```bash
# PowerShell
Get-Content C:\Users\AV013EV\.kim\logs\kim_server.log -Wait -Tail 50

# OR use the log viewer
python -m src.log_viewer
```

### 2. Claude Code Console

**Desktop App:**
- Help → Developer Tools → Console
- MCP server output appears here

**CLI:**
- Logs appear in terminal

---

## Log Viewer

KIM includes a log analyzer:

```bash
# View recent activity
python -m src.log_viewer

# View specific tool calls
python -m src.log_viewer --tool get_context

# View with timestamps
python -m src.log_viewer --detailed

# Follow logs in real-time
python -m src.log_viewer --follow
```

---

## Troubleshooting

### MCP Server Not Starting

**Check:**
```bash
# Test server directly
python -m src.server

# Should show: "KIM MCP Server starting..."
# Press Ctrl+C to stop
```

**Common issues:**
- Python not in PATH → Use full path to python.exe
- Dependencies missing → Run `pip install -e .` again
- Port conflict → KIM uses stdio (no port needed)

### Tools Not Appearing

**Check config file syntax:**
```bash
# Validate JSON
python -c "import json; print(json.load(open('mcp_config.json')))"
```

**Check paths:**
- Use absolute paths (not relative)
- Use double backslashes on Windows
- Verify `cwd` points to KIM directory

### OpenAI API Errors

**Check API key:**
```bash
# Test embeddings
python -c "from src.retrieval.embeddings import embed_text; import asyncio; print(asyncio.run(embed_text('test')))"
```

**Expected:** Array of 768 numbers
**Error:** "OPENAI_API_KEY not set" → Set environment variable

### No Outputs Retrieved

**Check storage:**
```bash
python -m src.inspect

# Should show:
# - Profile: exists
# - Outputs: N files
# - Embeddings: N vectors
```

**If empty:** Log some outputs first with `log_output` tool

---

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key for embeddings |
| `KIM_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `KIM_DATA_DIR` | `~/.kim` | Where to store data |

### Example: Change Data Directory

```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Users\\AV013EV\\dev\\work\\KIM",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "KIM_DATA_DIR": "C:\\KIM_Data",
        "KIM_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## Next Steps

Once connected:

1. **Onboard KIM** (future: Segment 5)
   - Manually edit `~/.kim/profiles/{user_id}.json`
   - Set your tone, format preferences, boundaries

2. **Use KIM naturally:**
   - Ask Claude to write emails, documents, code
   - Claude calls `get_context()` automatically
   - Claude calls `check_draft()` to validate
   - Claude calls `log_output()` to remember

3. **Inspect what KIM learns:**
   ```bash
   python -m src.inspect
   python -m src.log_viewer
   ```

4. **Monitor logs:**
   - Watch `~/.kim/logs/kim_server.log`
   - See every tool call, validation, embedding

---

## Advanced: Multiple Profiles

KIM currently uses demo user ID. To support multiple profiles:

**TODO (future):** MCP session authentication
- Extract user from Claude session
- Create profile per user
- Store separately

**For now:** Single user (demo ID) works fine for testing

---

## Support

**Issues:**
- GitHub: https://github.com/you/KIM/issues
- Logs: Share `~/.kim/logs/kim_server.log`

**Documentation:**
- Architecture: `ARCHITECTURE.md`
- Development: `DEVELOPMENT_STATUS.md`
- Ponytail: `docs/ponytail_integration.md`
