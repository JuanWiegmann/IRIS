"""
Hybrid Retrieval
================

Combines BM25 (keyword) and vector similarity (semantic) for best results.

Research basis:
- Wu et al. (2024): Most-relevant-first ordering maximizes quality
- Hybrid retrieval outperforms either method alone
- BM25 catches exact keyword matches
- Vector search catches semantic similarity
- Combined: "best of both worlds"

Algorithm:
1. BM25 search → keyword scores
2. Vector search → semantic scores
3. Normalize both scores to [0, 1]
4. Combine: score = 0.5 * bm25 + 0.5 * vector
5. Sort by combined score, return top-K
"""

from typing import Optional
from uuid import UUID
import numpy as np

from src.retrieval.bm25_search import search_bm25
from src.retrieval.embeddings import embed_text
from src.storage.file_store import get_output_store
from src.storage.embedding_store import get_embedding_store


# ═══════════════════════════════════════════════════════════
# HYBRID RETRIEVAL
# ═══════════════════════════════════════════════════════════

async def retrieve_relevant_outputs(
    user_id: UUID,
    query: str,
    top_k: int = 5,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> list[tuple[dict, float]]:
    """
    Retrieve most relevant outputs using hybrid search.

    Combines BM25 (keyword) and vector similarity (semantic).

    Args:
        user_id: User UUID
        query: Search query
        top_k: Number of results to return
        bm25_weight: Weight for BM25 scores (default: 0.5)
        vector_weight: Weight for vector scores (default: 0.5)

    Returns:
        List of (output_dict, combined_score) tuples, sorted by score (highest first)

    Example:
        results = await retrieve_relevant_outputs(
            user_id=uuid.UUID("..."),
            query="team status update email",
            top_k=3
        )
        # [
        #   ({"id": "001", "content": "Hi team..."}, 0.85),
        #   ({"id": "005", "content": "Quick update..."}, 0.72),
        #   ({"id": "012", "content": "Status report..."}, 0.68)
        # ]
    """
    # Load user outputs
    output_store = get_output_store()
    outputs = await output_store.list_all(user_id)

    if not outputs:
        return []

    # ═══ STEP 1: BM25 Keyword Search ═══
    bm25_results = await search_bm25(
        user_id=user_id,
        outputs=outputs,
        query=query,
        top_k=len(outputs)  # Get all scores
    )

    # Build BM25 score map: output_id → score
    bm25_scores = {output_id: score for output_id, score in bm25_results}

    # ═══ STEP 2: Vector Similarity Search ═══
    embedding_store = get_embedding_store()
    vector_scores = {}

    try:
        # Check if embeddings exist
        if await embedding_store.exists(user_id):
            # Embed query
            query_embedding = await embed_text(query)

            # Search
            vector_results = await embedding_store.search(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=len(outputs)  # Get all scores
            )

            # Build vector score map
            vector_scores = {output_id: score for output_id, score in vector_results}

    except Exception:
        # No embeddings yet, or embedding failed
        # Fall back to BM25 only
        vector_scores = {}

    # ═══ STEP 3: Normalize Scores ═══
    # Normalize BM25 scores to [0, 1]
    if bm25_scores:
        max_bm25 = max(bm25_scores.values())
        if max_bm25 > 0:
            bm25_scores = {
                output_id: score / max_bm25
                for output_id, score in bm25_scores.items()
            }

    # Normalize vector scores to [0, 1]
    if vector_scores:
        max_vector = max(vector_scores.values())
        min_vector = min(vector_scores.values())
        vector_range = max_vector - min_vector

        if vector_range > 0:
            vector_scores = {
                output_id: (score - min_vector) / vector_range
                for output_id, score in vector_scores.items()
            }

    # ═══ STEP 4: Combine Scores ═══
    combined_scores = {}

    for output in outputs:
        output_id = output["id"]

        # Get scores (default to 0 if missing)
        bm25_score = bm25_scores.get(output_id, 0.0)
        vector_score = vector_scores.get(output_id, 0.0)

        # Combine with weights
        combined = (bm25_weight * bm25_score) + (vector_weight * vector_score)
        combined_scores[output_id] = combined

    # ═══ STEP 5: Sort and Return Top-K ═══
    # Sort by combined score (highest first)
    sorted_outputs = sorted(
        outputs,
        key=lambda o: combined_scores.get(o["id"], 0.0),
        reverse=True
    )

    # Return top-K with scores
    return [
        (output, combined_scores[output["id"]])
        for output in sorted_outputs[:top_k]
        if combined_scores.get(output["id"], 0.0) > 0  # Filter zero scores
    ]


# ═══════════════════════════════════════════════════════════
# FORMATTING FOR LLM
# ═══════════════════════════════════════════════════════════

def format_outputs_for_llm(results: list[tuple[dict, float]]) -> str:
    """
    Format retrieved outputs as markdown for LLM.

    Args:
        results: List of (output_dict, score) tuples

    Returns:
        Markdown-formatted string

    Example output:
        ## Relevant Past Outputs

        ### 1. team status update (relevance: 85%)
        Hi team,

        Quick update:
        • Segment 2 complete
        ...

        ---

        ### 2. meeting notes (relevance: 72%)
        ...
    """
    if not results:
        return "*(No relevant past outputs found)*"

    lines = []

    for idx, (output, score) in enumerate(results, start=1):
        context = output.get("context", "output")
        content = output["content"]
        created_at = output.get("created_at", "")

        # Format score as percentage
        relevance = int(score * 100)

        lines.append(f"### {idx}. {context} (relevance: {relevance}%)")
        lines.append(f"*Created: {created_at}*")
        lines.append("")
        lines.append(content.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
