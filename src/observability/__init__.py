"""
Observability Module
====================

Logging and monitoring for IRIS.
"""

from src.observability.logger import (
    get_logger,
    setup_logging,
    log_tool_call,
    log_validation,
    log_retrieval,
    log_embedding,
    log_operation
)

__all__ = [
    "get_logger",
    "setup_logging",
    "log_tool_call",
    "log_validation",
    "log_retrieval",
    "log_embedding",
    "log_operation",
]
