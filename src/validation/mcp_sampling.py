"""
MCP Sampling Validator
======================

Semantic validation using MCP sampling (calling user's LLM in fresh context).

The "Self-Check Pattern":
- LLM generates draft (in generation context)
- IRIS requests validation via MCP sampling
- User's LLM validates in FRESH context (no generation bias)
- Result returns to IRIS
- IRIS combines with deterministic checks

This is how the LLM gets unbiased feedback on its own output.
"""

import json
from typing import Optional
from uuid import UUID

from src.validation.models import ValidationIssue, Severity
from src.validation.use_case_detector import UseCase
from src.profile import get_or_create_profile


# ═══════════════════════════════════════════════════════════
# MCP SAMPLING (PLACEHOLDER)
# ═══════════════════════════════════════════════════════════

# TODO: This will be implemented when MCP SDK adds sampling support
# For now, this is the interface design

_sampling_available: Optional[bool] = None


async def is_sampling_available() -> bool:
    """
    Check if MCP client supports sampling.

    Returns:
        True if sampling is available
    """
    global _sampling_available

    if _sampling_available is not None:
        return _sampling_available

    # TODO: Check MCP client capabilities
    # For now, assume not available
    _sampling_available = False
    return False


async def request_sampling(
    prompt: str,
    model_preferences: Optional[list[str]] = None,
    max_tokens: int = 500,
    temperature: float = 0.0
) -> str:
    """
    Request LLM sampling from MCP client.

    This calls back to the user's LLM in a fresh context.

    Args:
        prompt: Validation prompt
        model_preferences: Preferred models (e.g., ["haiku", "sonnet"])
        max_tokens: Max response tokens
        temperature: Temperature (0.0 for deterministic)

    Returns:
        LLM response text

    Raises:
        NotImplementedError: Sampling not yet implemented
    """
    # TODO: Implement with MCP SDK when available
    # from mcp.server.sampling import SamplingRequest
    #
    # sampling_request = SamplingRequest(
    #     messages=[{"role": "user", "content": prompt}],
    #     modelPreferences=model_preferences or ["haiku", "sonnet"],
    #     maxTokens=max_tokens,
    #     temperature=temperature
    # )
    #
    # response = await app.request_sampling(sampling_request)
    # return response.content

    raise NotImplementedError("MCP sampling not yet implemented")


# ═══════════════════════════════════════════════════════════
# SEMANTIC VALIDATORS (PER USE CASE)
# ═══════════════════════════════════════════════════════════

class MCPSamplingValidator:
    """
    Semantic validation via MCP sampling.

    Creates appropriate prompts per use case and parses responses.
    """

    async def validate_messaging(
        self,
        draft: str,
        context: str,
        user_id: UUID
    ) -> list[ValidationIssue]:
        """
        Semantic validation for messaging.

        Asks: "Is this message appropriate and usable?"

        Args:
            draft: Draft content
            context: Context description
            user_id: User UUID

        Returns:
            List of validation issues from LLM
        """
        if not await is_sampling_available():
            return []

        # Load profile for context
        profile = await get_or_create_profile(user_id)

        # Block if no profile exists (onboarding required)
        if profile is None:
            raise ValueError("ONBOARDING_REQUIRED: No profile found. Complete onboarding before using validation.")

        prompt = f"""Validate this message for appropriateness and usability.

**Context:** {context}

**User Profile:**
- Tone: {', '.join([t.value for t in profile.tone])}
- Format: {profile.format_preference.value}
- Language: {profile.language}

**Draft:**
{draft}

**Question:** Is this message appropriate for the context and user?

Check:
1. Does it address the topic appropriately?
2. Is the tone suitable?
3. Is it clear and understandable?
4. Would the recipient find it helpful?

Respond in JSON:
{{
  "usable": true/false,
  "issues": [
    {{"severity": "error/warning/info", "message": "specific issue"}}
  ],
  "reasoning": "brief explanation"
}}
"""

        try:
            response = await request_sampling(prompt, model_preferences=["haiku"])
            return self._parse_validation_response(response)
        except Exception:
            # Sampling failed, return empty (deterministic checks still ran)
            return []

    async def validate_coding(
        self,
        draft: str,
        context: str,
        user_id: UUID
    ) -> list[ValidationIssue]:
        """
        Semantic validation for code.

        Asks: "Is this code correct and quality?"
        Hints that tools (like Ponytail) might be useful.

        Args:
            draft: Draft code
            context: Context description
            user_id: User UUID

        Returns:
            List of validation issues from LLM
        """
        if not await is_sampling_available():
            return []

        prompt = f"""Validate this code for correctness and quality.

**Context:** {context}

**Use any available code analysis tools if applicable.**

**Code:**
```
{draft}
```

Check:
1. Syntax correctness
2. Logic errors
3. Best practices
4. Potential bugs
5. Code quality (complexity, readability)

Respond in JSON:
{{
  "usable": true/false,
  "issues": [
    {{"severity": "error/warning/info", "message": "specific issue", "suggestion": "how to fix"}}
  ],
  "reasoning": "brief explanation"
}}
"""

        try:
            response = await request_sampling(
                prompt,
                model_preferences=["sonnet"]  # Sonnet better for code
            )
            return self._parse_validation_response(response)
        except Exception:
            return []

    async def validate_mendix(
        self,
        draft: str,
        context: str,
        user_id: UUID
    ) -> list[ValidationIssue]:
        """
        Semantic validation for Mendix.

        Asks: "Is this valid Mendix?"

        Args:
            draft: Draft Mendix content
            context: Context description
            user_id: User UUID

        Returns:
            List of validation issues from LLM
        """
        if not await is_sampling_available():
            return []

        prompt = f"""Validate this Mendix content for correctness.

**Context:** {context}

**Mendix Content:**
{draft}

Check:
1. Does this follow Mendix conventions?
2. Is the structure correct (entities, microflows, etc.)?
3. Are naming conventions appropriate?
4. Any logical issues?

**Note:** Do NOT attempt to execute Mendix CLI (it's in beta).
Validation only, no execution.

Respond in JSON:
{{
  "usable": true/false,
  "issues": [
    {{"severity": "error/warning/info", "message": "specific issue"}}
  ],
  "reasoning": "brief explanation"
}}
"""

        try:
            response = await request_sampling(prompt, model_preferences=["sonnet"])
            return self._parse_validation_response(response)
        except Exception:
            return []

    def _parse_validation_response(self, response: str) -> list[ValidationIssue]:
        """
        Parse LLM validation response into ValidationIssue objects.

        Args:
            response: JSON response from LLM

        Returns:
            List of ValidationIssue objects
        """
        try:
            data = json.loads(response)
            issues = []

            for issue_data in data.get("issues", []):
                issues.append(ValidationIssue(
                    severity=Severity(issue_data["severity"]),
                    category="semantic",  # MCP sampling is semantic
                    message=issue_data["message"],
                    suggestion=issue_data.get("suggestion")
                ))

            return issues

        except (json.JSONDecodeError, KeyError, ValueError):
            # Failed to parse, return empty
            # Deterministic checks already ran, so not a total failure
            return []


# ═══════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════

def get_mcp_sampling_validator() -> MCPSamplingValidator:
    """Get MCP sampling validator instance."""
    return MCPSamplingValidator()
