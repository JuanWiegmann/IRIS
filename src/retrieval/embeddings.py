"""
Embeddings Integration
======================

OpenAI text-embedding-3-small (768 dimensions) for semantic similarity.

Why this model:
- Dimension: 768 (good balance of quality vs. cost)
- Performance: Better than ada-002 on MTEB benchmarks
- Cost: $0.02 per 1M tokens (cheap for PoC)
"""

import os
from typing import Optional
from openai import AsyncOpenAI

# Learning: learning/06_memory/README.md#embeddings


# ═══════════════════════════════════════════════════════════
# CLIENT INITIALIZATION
# ═══════════════════════════════════════════════════════════

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """
    Get or create OpenAI client.

    Reads API key from OPENAI_API_KEY environment variable.

    Raises:
        ValueError: If OPENAI_API_KEY not set
    """
    global _client

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Get your API key from: https://platform.openai.com/api-keys"
            )
        _client = AsyncOpenAI(api_key=api_key)

    return _client


# ═══════════════════════════════════════════════════════════
# EMBEDDING FUNCTIONS
# ═══════════════════════════════════════════════════════════

async def embed_text(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    Embed a single text string.

    Args:
        text: Text to embed
        model: OpenAI embedding model (default: text-embedding-3-small)

    Returns:
        768-dimensional embedding vector

    Raises:
        ValueError: If text is empty
        openai.OpenAIError: If API call fails
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    client = get_client()

    response = await client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float"
    )

    return response.data[0].embedding


async def embed_batch(
    texts: list[str],
    model: str = "text-embedding-3-small"
) -> list[list[float]]:
    """
    Embed multiple texts in a single API call (more efficient).

    Args:
        texts: List of texts to embed
        model: OpenAI embedding model

    Returns:
        List of 768-dimensional embedding vectors

    Raises:
        ValueError: If any text is empty or list is empty
        openai.OpenAIError: If API call fails
    """
    if not texts:
        raise ValueError("Cannot embed empty list")

    # Filter out empty texts
    non_empty_texts = [t for t in texts if t and t.strip()]
    if not non_empty_texts:
        raise ValueError("All texts are empty")

    client = get_client()

    response = await client.embeddings.create(
        model=model,
        input=non_empty_texts,
        encoding_format="float"
    )

    # Return embeddings in original order
    return [item.embedding for item in response.data]


# ═══════════════════════════════════════════════════════════
# COST TRACKING (Optional)
# ═══════════════════════════════════════════════════════════

def estimate_cost(num_tokens: int, model: str = "text-embedding-3-small") -> float:
    """
    Estimate embedding cost.

    Pricing (as of 2024):
    - text-embedding-3-small: $0.02 per 1M tokens
    - text-embedding-3-large: $0.13 per 1M tokens

    Args:
        num_tokens: Number of tokens to embed
        model: Model name

    Returns:
        Estimated cost in USD
    """
    pricing = {
        "text-embedding-3-small": 0.02 / 1_000_000,
        "text-embedding-3-large": 0.13 / 1_000_000,
    }

    rate = pricing.get(model, 0.02 / 1_000_000)
    return num_tokens * rate
