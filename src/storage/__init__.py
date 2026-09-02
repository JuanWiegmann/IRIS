"""
Storage Layer
=============

File-based storage for local-per-user deployment.

Each user has their own KIM instance with data stored in ~/.kim/:
- profiles/{user_id}.json — User profile (tone, style, boundaries)
- outputs/{user_id}/*.json — Past outputs with metadata
- embeddings/{user_id}.npy — Vector embeddings (NumPy array)

Design:
- 100% transparent (JSON files, human-readable)
- No database required (no Docker, no PostgreSQL)
- Fast enough for single-user (< 10,000 outputs)
- Easy to backup/migrate (just copy ~/.kim/)
"""

from src.storage.file_store import ProfileStore, OutputStore, EmbeddingStore

__all__ = [
    "ProfileStore",
    "OutputStore",
    "EmbeddingStore",
]
