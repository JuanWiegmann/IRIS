# IRIS Claude Code Plugins

Visual extensions for IRIS personalization — status indicators, live profile views, and validation guards.

## Plugins

### 1. iris-status
**Status line indicator showing IRIS connection and onboarding status.**

**What it shows:**
- `( •‿• ) IRIS` — Active and personalized
- `⚠️ IRIS: onboarding required` — Setup needed
- `IRIS: not connected` — MCP server unavailable

**Updates:** Session start + after each turn

---

### 2. iris-profile-pane
**Live profile view pane with your personalization settings.**

**Usage:** `/iris-profile`

**Displays:**
- Language preference
- Tone (professional, casual, technical, etc.)
- Format preference (concise, detailed, step-by-step, etc.)
- Boundaries (proactivity, error handling rules)
- Current projects

**Features:**
- Refresh button to reload
- Error handling with retry
- Fallback when onboarding incomplete

---

### 3. iris-context-guard
**Validation toast that warns when IRIS context isn't loaded.**

**Why:** IRIS personalization requires `get_context()` to be called before generating responses. This plugin warns when that doesn't happen.

**Shows:** `⚠️ IRIS context not loaded — response may not be personalized`

**When:** At turn end, if no `mcp__iris__get_context` call was detected

---

## Installation

### Option 1: From IRIS Repo (Recommended)
```bash
# Copy all plugins to user-global plugin directory
cp -r ~/KIM_dev/IRIS/plugins/* ~/.claude/dev-mods/
```

### Option 2: Individual Plugins
```bash
# Status line only
cp -r ~/KIM_dev/IRIS/plugins/iris-status ~/.claude/dev-mods/

# Profile pane only
cp -r ~/KIM_dev/IRIS/plugins/iris-profile-pane ~/.claude/dev-mods/

# Context guard only
cp -r ~/KIM_dev/IRIS/plugins/iris-context-guard ~/.claude/dev-mods/
```

### Option 3: Hot Reload During Development
When working on IRIS in Claude Code with plugin-authoring skill loaded:
1. Plugins are in `~/KIM_dev/IRIS/plugins/`
2. When turn ends, you'll be asked to enable hot reloading
3. Select "Enable for this session"
4. Plugins auto-reload on file changes

---

## Prerequisites

**IRIS MCP server must be running and connected.**

Check: `~/.claude/.mcp.json` should contain:
```json
{
  "servers": {
    "iris": {
      "command": "uv",
      "args": ["run", "iris-mcp"],
      "env": {
        "IRIS_DATA_DIR": "~/.iris/data"
      }
    }
  }
}
```

If not set up: Run `cp ~/.claude/iris_mcp_template.json ~/.claude/.mcp.json`

---

## How They Work

All plugins use the **IRIS MCP tools** via `$.tool.call()`:

```typescript
const result = await $.tool.call({
  tool: 'mcp__iris__get_context',
  input: { query: 'status check' }
});
```

**iris-status:** Calls `get_context()` on session start and turn end to check if onboarding is complete.

**iris-profile-pane:** Calls `get_context()` and parses the profile from the response text.

**iris-context-guard:** Hooks `tool.call` events to detect if `get_context()` was called, warns at turn end if not.

---

## Development

### Structure
```
plugins/
├── README.md
├── iris-status/
│   ├── .claude-plugin/plugin.json
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── register.ts
├── iris-profile-pane/
│   ├── .claude-plugin/plugin.json
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── register.tsx
│   └── types/index.d.ts
└── iris-context-guard/
    ├── .claude-plugin/plugin.json
    ├── hooks/
    │   ├── hooks.json
    │   └── register.ts
    └── types/index.d.ts
```

### Validate
```bash
# Validate plugin manifests and hooks
claude plugin validate ~/.claude/dev-mods/iris-status
claude plugin validate ~/.claude/dev-mods/iris-profile-pane
claude plugin validate ~/.claude/dev-mods/iris-context-guard
```

### Type Check
```bash
# Type check with generated types
tsc -p ~/.claude/dev-mods/iris-status
tsc -p ~/.claude/dev-mods/iris-profile-pane
tsc -p ~/.claude/dev-mods/iris-context-guard
```

---

## Troubleshooting

**Plugin not loading:**
- Check `claude --debug` for errors
- Validate: `claude plugin validate <plugin-path>`
- Ensure IRIS MCP server is connected

**Status shows "not connected":**
- IRIS MCP server not running
- Check `.mcp.json` configuration
- Restart Claude Code session

**Profile pane shows "onboarding required":**
- Run `/startIris` to complete onboarding
- Check `~/.iris/data/profiles/` for profile files

**Context guard always warns:**
- IRIS protocol instructions not loaded in `CLAUDE.md`
- `get_context()` call failed silently
- Check debug log for tool call errors

---

## License

Part of IRIS — see main repo LICENSE
