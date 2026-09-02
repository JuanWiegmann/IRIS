# Ponytail Plugin Integration

## Overview

**Ponytail** is a code quality plugin for Claude Code that enhances validation.

- **Repository:** https://github.com/DietrichGebert/ponytail.git
- **Purpose:** Better code editing, validation, quality checks
- **Use in KIM:** Validate coding and Mendix outputs via MCP sampling

---

## Architecture: KIM ↔ Ponytail Flow

```
User → Claude Code (with Ponytail) → MCP → KIM

KIM detects: "This is CODE"
KIM → (via MCP sampling) → Claude Code
Claude Code uses Ponytail to validate code quality
Claude Code → KIM: validation result
KIM → User's LLM: combined validation feedback
```

**Key:** KIM uses **MCP sampling** to call back to the user's LLM, which has Ponytail available.

---

## Validation Strategy by Use Case

### 1. MESSAGING (emails, documents)
```
KIM Validation:
├─ Deterministic checks (tone, format, boundaries)
└─ MCP sampling (semantic check: "Is this usable?")
```

**No Ponytail needed** — messaging is natural language

---

### 2. CODING (Python, JS, general programming)
```
KIM Validation:
├─ Deterministic checks (basic syntax patterns)
├─ MCP sampling WITHOUT Ponytail hint
│  └─ Ask: "Is this code correct and follows best practices?"
└─ (Future) MCP sampling WITH Ponytail hint
   └─ Ask: "Validate this code using available tools"
   └─ Claude Code invokes Ponytail automatically
```

**Ponytail enhances** — better code quality validation

---

### 3. MENDIX (low-code development)
```
KIM Validation:
├─ Deterministic checks (Mendix patterns, XML structure)
├─ MCP sampling: "Is this valid Mendix?"
└─ (Future) Ponytail for Mendix code quality
```

**Note:** Mendix CLI is in **beta** — advise users NOT to use it directly. Rely on validation only.

---

## MCP Sampling Implementation

### Current (Segment 3):
```python
# KIM calls user's LLM in fresh context
response = await request_sampling(
    prompt="Validate this draft: ...",
    model_preferences=["haiku", "sonnet"]
)
```

### Enhanced (with Ponytail awareness):
```python
# KIM hints that code validation would benefit from tools
response = await request_sampling(
    prompt=f"""Validate this code for quality and correctness.

Use any available code analysis tools if applicable.

Code:
{draft}

Check:
1. Syntax correctness
2. Logic errors
3. Best practices
4. Potential bugs
""",
    model_preferences=["sonnet"]  # Sonnet for code validation
)
```

**The LLM decides** whether to use Ponytail — KIM just provides the validation context.

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

## Summary

**What KIM does:**
1. ✅ Detect use case (messaging/coding/Mendix)
2. ✅ Route to appropriate validator
3. ⏳ Use MCP sampling for semantic checks
4. ⏳ (Future) Ponytail awareness for code quality

**What Ponytail does:**
- Enhances code validation (when available)
- Runs automatically via Claude Code hooks
- KIM doesn't control Ponytail — just benefits from it

**What KIM does NOT do:**
- ❌ Execute Mendix CLI (it's beta, unstable)
- ❌ Require Ponytail (optional enhancement)
- ❌ Force specific validation tools

**Philosophy:** KIM detects intent, delegates to best validator, gracefully degrades if tools unavailable.
