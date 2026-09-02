"""
Embedding Storage
=================

NumPy-based vector embedding storage for semantic similarity search.

Storage format:
- ~/.kim/embeddings/{user_id}.npy — NumPy array (N x 768)
- ~/.kim/embeddings/{user_id}_index.json — Metadata mapping (index → output_id)

Example:
    embeddings.npy: [[0.1, 0.2, ...], [0.3, 0.4, ...]]  # shape: (100, 768)
    index.json: ["001", "002", "003", ...]  # maps row index to output ID
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional
from uuid import UUID

from src.storage.file_store import get_kim_root


# ═══════════════════════════════════════════════════════════
# EMBEDDING STORE
# ═══════════════════════════════════════════════════════════

class EmbeddingStore:
    """
    NumPy-based embedding storage with cosine similarity search.

    Stores embeddings as .npy files (efficient binary format).
    Keeps index mapping for output_id lookups.
    """

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize embedding store.

        Args:
            root: Storage root (defaults to ~/.kim/)
        """
        self.root = root or get_kim_root()
        self.embeddings_dir = self.root / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)

    def _get_embeddings_path(self, user_id: UUID) -> Path:
        """Get path to user's embeddings file."""
        return self.embeddings_dir / f"{user_id}.npy"

    def _get_index_path(self, user_id: UUID) -> Path:
        """Get path to user's index file."""
        return self.embeddings_dir / f"{user_id}_index.json"

    async def save(
        self,
        user_id: UUID,
        embeddings: np.ndarray,
        output_ids: list[str]
    ) -> None:
        """
        Save embeddings and index.

        Args:
            user_id: User UUID
            embeddings: NumPy array of shape (N, 768)
            output_ids: List of output IDs (length N)

        Raises:
            ValueError: If shapes don't match
        """
        if len(embeddings) != len(output_ids):
            raise ValueError(
                f"Embeddings shape ({len(embeddings)}) must match "
                f"output_ids length ({len(output_ids)})"
            )

        # Save embeddings as NumPy binary
        embeddings_path = self._get_embeddings_path(user_id)
        np.save(embeddings_path, embeddings)

        # Save index as JSON
        index_path = self._get_index_path(user_id)
        index_path.write_text(
            json.dumps(output_ids, indent=2),
            encoding="utf-8"
        )

    async def load(self, user_id: UUID) -> tuple[np.ndarray, list[str]]:
        """
        Load embeddings and index.

        Args:
            user_id: User UUID

        Returns:
            (embeddings array, output_ids list)

        Raises:
            FileNotFoundError: If embeddings don't exist
        """
        embeddings_path = self._get_embeddings_path(user_id)
        index_path = self._get_index_path(user_id)

        if not embeddings_path.exists():
            raise FileNotFoundError(f"No embeddings found for user {user_id}")

        # Load embeddings
        embeddings = np.load(embeddings_path)

        # Load index
        output_ids = json.loads(index_path.read_text(encoding="utf-8"))

        return embeddings, output_ids

    async def append(
        self,
        user_id: UUID,
        embedding: np.ndarray,
        output_id: str
    ) -> None:
        """
        Append a new embedding (incremental).

        Args:
            user_id: User UUID
            embedding: Single embedding vector (shape: 768)
            output_id: Output ID for this embedding

        Raises:
            ValueError: If embedding shape is wrong
        """
        if embedding.shape != (768,):
            raise ValueError(f"Embedding must be shape (768,), got {embedding.shape}")

        # Load existing or create new
        try:
            embeddings, output_ids = await self.load(user_id)

            # Append new embedding
            embeddings = np.vstack([embeddings, embedding])
            output_ids.append(output_id)

        except FileNotFoundError:
            # First embedding
            embeddings = embedding.reshape(1, -1)  # Shape: (1, 768)
            output_ids = [output_id]

        # Save updated
        await self.save(user_id, embeddings, output_ids)

    async def search(
        self,
        user_id: UUID,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Search for most similar embeddings (cosine similarity).

        Args:
            user_id: User UUID
            query_embedding: Query vector (shape: 768)
            top_k: Number of results to return

        Returns:
            List of (output_id, similarity_score) tuples, sorted by score (highest first)

        Raises:
            FileNotFoundError: If no embeddings exist
            ValueError: If query embedding shape is wrong
        """
        if query_embedding.shape != (768,):
            raise ValueError(f"Query embedding must be shape (768,), got {query_embedding.shape}")

        # Load embeddings
        embeddings, output_ids = await self.load(user_id)

        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, embeddings)

        # Get top-K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]  # Highest first

        # Return (output_id, score) pairs
        return [
            (output_ids[idx], float(similarities[idx]))
            for idx in top_indices
        ]

    async def exists(self, user_id: UUID) -> bool:
        """
        Check if embeddings exist for user.

        Args:
            user_id: User UUID

        Returns:
            True if embeddings exist
        """
        return self._get_embeddings_path(user_id).exists()

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete all embeddings for user.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        embeddings_path = self._get_embeddings_path(user_id)
        index_path = self._get_index_path(user_id)

        if not embeddings_path.exists():
            return False

        embeddings_path.unlink()
        if index_path.exists():
            index_path.unlink()

        return True


# ═══════════════════════════════════════════════════════════
# COSINE SIMILARITY (NumPy Implementation)
# ═══════════════════════════════════════════════════════════

def cosine_similarity(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query and all embeddings.

    Formula: cos(θ) = (A · B) / (||A|| * ||B||)

    Args:
        query: Query vector (shape: 768)
        embeddings: Embedding matrix (shape: N x 768)

    Returns:
        Similarity scores (shape: N) — values in [-1, 1], higher = more similar
    """
    # Normalize query
    query_norm = query / np.linalg.norm(query)

    # Normalize embeddings
    embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    # Dot product = cosine similarity (when normalized)
    similarities = np.dot(embeddings_norm, query_norm)

    return similarities


# ═══════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════

_embedding_store: Optional[EmbeddingStore] = None


def get_embedding_store() -> EmbeddingStore:
    """Get default EmbeddingStore instance (singleton)."""
    global _embedding_store
    if _embedding_store is None:
        _embedding_store = EmbeddingStore()
    return _embedding_store
