"""
BM25 Keyword Search
===================

BM25 (Best Matching 25) algorithm for keyword-based retrieval.

Why BM25:
- Industry standard for keyword search (used by Elasticsearch, Lucene)
- Better than TF-IDF for short documents
- Handles document length normalization
- Fast: O(n) search over indexed documents

Research basis:
- Robertson & Zaragoza (2009): "The Probabilistic Relevance Framework: BM25 and Beyond"
- Used in hybrid retrieval systems (BM25 + vector) for best of both worlds
"""

from typing import Optional
from uuid import UUID
from rank_bm25 import BM25Okapi


# ═══════════════════════════════════════════════════════════
# BM25 INDEX
# ═══════════════════════════════════════════════════════════

class BM25Index:
    """
    BM25 keyword search index for user outputs.

    Builds an in-memory BM25 index from outputs.
    Fast enough for <10,000 documents (single-user use case).
    """

    def __init__(self):
        """Initialize empty BM25 index."""
        self.bm25: Optional[BM25Okapi] = None
        self.output_ids: list[str] = []
        self.outputs: list[dict] = []

    def build(self, outputs: list[dict]) -> None:
        """
        Build BM25 index from outputs.

        Args:
            outputs: List of output dicts with 'id' and 'content' fields

        Example:
            outputs = [
                {"id": "001", "content": "Quick team update..."},
                {"id": "002", "content": "Meeting notes..."},
            ]
        """
        if not outputs:
            self.bm25 = None
            self.output_ids = []
            self.outputs = []
            return

        # Store outputs
        self.outputs = outputs
        self.output_ids = [o["id"] for o in outputs]

        # Tokenize documents (simple whitespace split)
        # Production: use nltk or spaCy for better tokenization
        tokenized_docs = [
            self._tokenize(output["content"])
            for output in outputs
        ]

        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """
        Search for most relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (output_id, bm25_score) tuples, sorted by score (highest first)

        Example:
            results = index.search("team status update", top_k=3)
            # [("001", 5.23), ("005", 3.45), ("012", 2.11)]
        """
        if self.bm25 is None or not self.outputs:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-K indices
        import numpy as np
        top_indices = np.argsort(scores)[-top_k:][::-1]  # Highest first

        # Return (output_id, score) pairs
        return [
            (self.output_ids[idx], float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0  # Filter out zero scores
        ]

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text for BM25.

        Simple whitespace split + lowercase for PoC.
        Production: use proper tokenizer (nltk, spaCy).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        return text.lower().split()


# ═══════════════════════════════════════════════════════════
# USER-SPECIFIC INDEX MANAGER
# ═══════════════════════════════════════════════════════════

class BM25Manager:
    """
    Manages BM25 indices per user.

    Caches indices in memory for fast subsequent searches.
    """

    def __init__(self):
        """Initialize manager with empty cache."""
        self._indices: dict[UUID, BM25Index] = {}

    async def get_index(self, user_id: UUID, outputs: list[dict]) -> BM25Index:
        """
        Get or build BM25 index for user.

        Args:
            user_id: User UUID
            outputs: User's outputs (used if index not cached)

        Returns:
            BM25Index ready for searching
        """
        # Check cache
        if user_id in self._indices:
            return self._indices[user_id]

        # Build new index
        index = BM25Index()
        index.build(outputs)

        # Cache it
        self._indices[user_id] = index

        return index

    def invalidate(self, user_id: UUID) -> None:
        """
        Invalidate cached index for user.

        Call this when new outputs are added.

        Args:
            user_id: User UUID
        """
        if user_id in self._indices:
            del self._indices[user_id]

    async def search(
        self,
        user_id: UUID,
        outputs: list[dict],
        query: str,
        top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Search user's outputs with BM25.

        Args:
            user_id: User UUID
            outputs: User's outputs
            query: Search query
            top_k: Number of results

        Returns:
            List of (output_id, score) tuples
        """
        index = await self.get_index(user_id, outputs)
        return index.search(query, top_k=top_k)


# ═══════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════

_bm25_manager: Optional[BM25Manager] = None


def get_bm25_manager() -> BM25Manager:
    """Get default BM25Manager instance (singleton)."""
    global _bm25_manager
    if _bm25_manager is None:
        _bm25_manager = BM25Manager()
    return _bm25_manager
