# Testing Conventions

## Philosophy

- Test behavior, not implementation details
- Each segment adds tests for its components
- Integration tests verify agent pipelines end-to-end
- Mock LLM responses for unit tests (deterministic)
- Use real LLM calls only in clearly marked integration tests

## Structure

```
tests/
├── unit/           # Fast, no external dependencies
├── integration/    # Requires Ollama/Bedrock running
└── conftest.py     # Shared fixtures (mock LLM, test profiles)
```

## Naming

- `test_{module}_{behavior}.py` — e.g., `test_router_selects_ollama_for_simple.py`
- Test functions: `test_{scenario}_returns_{expected}` or `test_{scenario}_raises_{error}`
