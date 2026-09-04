# IRIS Installation Fixes

## Issues Found & Fixed

### Issue 1: Hook Encoding Crash ✅ FIXED
**Problem:** `iris_profile_check.py` crashed on Windows with emoji encoding errors
**Cause:** Windows terminal uses cp1252, can't encode UTF-8 emojis
**Fix:** Added UTF-8 wrapper + removed emoji characters

### Issue 2: Hook Output Corruption ✅ FIXED  
**Problem:** Hook output looped infinitely (44KB of repeated text)
**Cause:** String concatenation with `"=" * 70` broke under UTF-8 wrapper
**Fix:** Changed to literal string (triple-quoted)

### Issue 3: Auto-launch Confusion ✅ FIXED
**Problem:** Install script unclear about when/how Claude starts
**Cause:** Mixed messages about local vs global config
**Fix:** Simplified to use global config, clear manual instructions

## Current Status

✅ **Hook works:** SessionStart fires, prints onboarding trigger message
✅ **Server works:** IRIS MCP server starts and responds to tool calls
✅ **Onboarding works:** `start_onboarding()` returns first question
✅ **Global registration:** IRIS registered in Claude Desktop config

## How to Complete Setup

1. **Close this Claude session completely**
2. **Open terminal in IRIS directory:**
   ```bash
   cd C:\Users\AV013EV\IRIS_dev\IRIS
   ```
3. **Start new Claude Code session:**
   ```bash
   claude -p "Start IRIS onboarding"
   ```
4. **SessionStart hook will fire automatically**
5. **Claude will see the onboarding trigger message**
6. **Claude should call:** `start_onboarding(user_id='demo_user')`
7. **Answer 10 questions** (~5 minutes)
8. **Profile created** → IRIS fully active!

## Why Hook Doesn't Force Onboarding

The SessionStart hook **prints instructions** to Claude, but Claude still needs to:
- Read the hook output (system-reminder)
- Decide to call `start_onboarding()`
- Execute the onboarding flow

The hook is a **prompt**, not a forcing function. Claude must act on it.

## Verification Commands

Test hook:
```bash
python .claude/hooks/iris_profile_check.py
```

Test server:
```bash
python -m src.server
# Should start without errors
```

Test onboarding:
```bash
python -c "from src.tools.onboarding import start_onboarding; import json; print(json.dumps(start_onboarding('demo_user'), indent=2))"
```

## Next Session

When you restart Claude Code in the IRIS directory, the SessionStart hook will fire and display:

```
======================================================================
IRIS ONBOARDING REQUIRED
======================================================================

PROTOCOL:
1. Immediately call: start_onboarding(user_id='demo_user')
2. Present first question conversationally (not raw JSON)
...
```

Claude should then begin onboarding automatically.
