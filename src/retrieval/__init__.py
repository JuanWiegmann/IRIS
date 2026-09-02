"""
Retrieval Engine
================

Hybrid retrieval system combining BM25 (keyword) and vector similarity (semantic).

Research basis:
- Wu et al. (2024): User outputs drive personalization
- Most-relevant-first ordering maximizes quality
- Position in context matters

Components:
- embeddings.py: OpenAI text-embedding-3-small integration
- hybrid.py: BM25 + vector similarity ranking
- ranker.py: Top-K selection with Wu et al. ordering
"""

from src.retrieval.embeddings import embed_text, embed_batch
from src.retrieval.hybrid import retrieve_relevant_outputs

__all__ = [
    "embed_text",
    "embed_batch",
    "retrieve_relevant_outputs",
]
