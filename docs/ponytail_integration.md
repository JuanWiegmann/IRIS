# Ponytail Plugin Integration

## Overview

**Ponytail** is a code quality plugin that runs as a separate MCP server alongside KIM.

- **Repository:** https://github.com/DietrichGebert/ponytail.git
- **Purpose:** Code editing, validation, quality checks
- **Use in KIM:** KIM detects code, recommends validation, LLM uses Ponytail directly

---

## Architecture: KIM Orchestrates, LLM Uses Tools

```
User: "Write Python code"
  ↓
Claude Code → KIM: check_draft(code)
  ↓
KIM detects: UseCase.CODING
KIM runs: Deterministic checks (TODO, print, bare except)
KIM returns: {
  "deterministic_issues": [...],
  "recommendation": "Validate code quality with available tools",
  "tools_available": ["ponytail_validate"]
}
  ↓
Claude Code sees recommendation
Claude Code → Ponytail MCP server: validate(code)
  ↓
Ponytail validates and returns quality report
  ↓
Claude Code combines: KIM deterministic + Ponytail semantic
  ↓
User sees: Complete validation feedback
```

**Key insight:** KIM is an orchestrator, not a validator. The LLM decides which tools to use based on KIM's recommendations.

---

## Validation Strategy by Use Case

### 1. MESSAGING (emails, documents)
```
KIM Response:
├─ Deterministic checks (tone, format, boundaries)
├─ Recommendation: "Standard validation complete"
└─ Tools needed: None

LLM Action:
└─ Uses KIM's feedback directly (no additional tools)
```

**No additional tools needed** — KIM's deterministic checks are sufficient

---

### 2. CODING (Python, JS, general programming)
```
KIM Response:
├─ Deterministic checks (TODO, print, bare except, security)
├─ Recommendation: "Validate code quality with available tools"
└─ Tools available: ["ponytail_validate", "ponytail_analyze"]

LLM Action:
├─ Sees KIM's recommendation
├─ Calls Ponytail: validate(code)
└─ Combines: KIM deterministic + Ponytail semantic
```

**Ponytail provides deep analysis** — LLM uses it based on KIM's guidance

---

### 3. MENDIX (low-code development)
```
KIM Response:
├─ Deterministic checks (entity naming, XML structure)
├─ Recommendation: "Mendix content detected, validate structure"
└─ Tools available: ["mendix_cli_validate"] (if installed)

LLM Action:
├─ Uses KIM's Mendix-specific feedback
└─ Optionally: Calls Mendix CLI for validation (NOT execution)
```

**Note:** Mendix CLI is **beta** — KIM recommends validation only, never execution

---

## KIM's Orchestration Response

### check_draft Response Format:

```json
{
  "passed": false,
  "use_case": "coding",
  "issues": [
    {
      "severity": "warning",
      "category": "best_practice",
      "message": "Uses print() instead of logging",
      "suggestion": "Consider using logging module"
    }
  ],
  "method": "deterministic",
  "confidence": 0.8,
  "recommendation": {
    "action": "validate_with_tools",
    "reason": "Code detected - quality analysis recommended",
    "suggested_tools": ["ponytail_validate"],
    "prompt": "Validate code quality: check complexity, test coverage, and best practices"
  }
}
```

### How LLM Uses This:

```
1. LLM receives KIM's response
2. LLM sees: recommendation.action = "validate_with_tools"
3. LLM sees: suggested_tools = ["ponytail_validate"]
4. LLM calls: ponytail_validate(code)
5. LLM combines results:
   - KIM deterministic issues
   - Ponytail semantic analysis
6. LLM presents complete feedback to user
```

**KIM guides, LLM executes** — clean separation of concerns

---

## Detection Logic

```python
# In check_draft()
use_case = detect_use_case(query, draft)

if use_case == UseCase.MESSAGING:
    # Standard validation
    validation = deterministic_checks(draft)
    if mcp_available:
        validation += semantic_check(draft)

elif use_case == UseCase.CODING:
    # Code-focused validation
    validation = code_pattern_checks(draft)
    if mcp_available:
        validation += code_quality_check(draft)
        # ^ This is where Ponytail would be invoked by Claude

elif use_case == UseCase.MENDIX:
    # Mendix-specific validation
    validation = mendix_pattern_checks(draft)
    if mcp_available:
        validation += mendix_semantic_check(draft)
```

---

## Ponytail Capabilities (from plugin)

Based on https://github.com/DietrichGebert/ponytail.git:

**Ponytail provides:**
- Enhanced code editing (better than standard Edit tool)
- Code analysis hooks
- Quality checks
- (Exact features TBD — need to inspect plugin code)

**How KIM uses it:**
1. KIM detects "this is code"
2. KIM requests validation via MCP sampling
3. User's Claude Code (with Ponytail) validates
4. Ponytail hooks run automatically (if installed)
5. Result returns to KIM
6. KIM combines with deterministic checks

---

## Mendix-Specific Considerations

### ⚠️ Mendix CLI — DO NOT USE

**Why:**
- Mendix CLI is in beta
- Unstable, incomplete features
- Breaking changes likely

**Instead:**
- Validate Mendix XML structure (deterministic)
- Ask user's LLM: "Is this valid Mendix?" (MCP sampling)
- Rely on Mendix Studio for actual deployment

**KIM's role:**
- Detect Mendix content
- Validate patterns (entity names, microflow structure)
- Provide feedback on best practices
- **DO NOT** execute Mendix CLI commands

---

## Implementation Phases

### Phase 1: Use Case Detection ✅
- Detect messaging vs coding vs Mendix
- Route to appropriate validator
- **Status:** Built (see `src/validation/use_case_detector.py`)

### Phase 2: Enhanced Validation (Segment 4)
- Deterministic checks per use case
- MCP sampling with code-focused prompts
- **Status:** Next to build

### Phase 3: Ponytail Awareness (Future)
- Explicit hints in MCP sampling prompts
- Detect if Ponytail is available
- Fallback gracefully if not installed
- **Status:** Planned after Segment 4

---

## Testing Strategy

### Unit Tests (Use Case Detection)
```python
# tests/test_use_case_detector.py
def test_detect_python_code():
    assert detect_use_case("Write Python", "def foo():...") == UseCase.CODING

def test_detect_mendix():
    assert detect_use_case("Create entity", "<entity>...") == UseCase.MENDIX
```

### Integration Tests (with Ponytail)
```python
# tests/integration/test_ponytail_validation.py
@pytest.mark.skipif(not ponytail_available(), reason="Ponytail not installed")
async def test_code_validation_with_ponytail():
    # KIM validates code
    # Ponytail should enhance validation
    result = await check_draft(python_code)
    assert result.ponytail_used is True
```

---

## User Experience

### Without Ponytail:
```
User: "Write a Python function"
Claude generates code
KIM validates → basic syntax + semantic check
User sees: "✓ Code looks correct"
```

### With Ponytail:
```
User: "Write a Python function"
Claude generates code
KIM validates → basic syntax + Ponytail-enhanced quality check
User sees: "✓ Code quality verified (complexity: low, coverage: good)"
```

**Ponytail adds depth** — not required, but improves validation quality.

---

## Configuration

### User Config (future):
```yaml
# ~/.kim/config.yaml
validation:
  use_ponytail: true  # Enable Ponytail integration if available
  mendix:
    warn_about_cli: true  # Warn users about beta CLI
    validate_xml: true
```

---

## Installation

### Automated (Recommended):
```bash
cd KIM
python install.py

# This installs:
# ✅ KIM MCP server
# ✅ Ponytail plugin (code quality)
# ✅ Mendix CLI check (optional)

# All registered as separate MCP servers
```

### Manual:
```bash
# Install KIM
cd KIM
pip install -e .

# Install Ponytail
cd ../
git clone https://github.com/DietrichGebert/ponytail.git
cd ponytail
pip install -e .

# Register both in claude_desktop_config.json
```

**Config file:**
```json
{
  "mcpServers": {
    "kim": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\KIM"
    },
    "ponytail": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\ponytail"
    }
  }
}
```

---

## Summary

**What KIM does:**
1. ✅ Detect use case (messaging/coding/Mendix)
2. ✅ Run deterministic validation
3. ✅ Recommend which tools LLM should use
4. ✅ Provide structured guidance

**What LLM does:**
- Receives KIM's recommendations
- Decides which tools to invoke
- Calls Ponytail/Mendix directly (separate MCP servers)
- Combines all feedback for user

**What Ponytail does:**
- Runs as separate MCP server
- Provides code quality tools
- Used by LLM when KIM recommends it
- Independent of KIM

**What KIM does NOT do:**
- ❌ Call Ponytail internally (LLM does this)
- ❌ Execute Mendix CLI (recommend only)
- ❌ Require any specific tools (graceful degradation)
- ❌ Force tool usage (LLM decides)

**Philosophy:** 
- **KIM = Orchestrator** (detects, validates, recommends)
- **LLM = Executor** (decides, calls tools, combines)
- **Ponytail/Mendix = Specialists** (domain-specific analysis)

Clean separation of concerns via MCP protocol.
