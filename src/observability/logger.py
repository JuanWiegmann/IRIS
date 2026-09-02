"""
KIM Logger
==========

Detailed logging for all KIM operations.

Logs to:
- ~/.kim/logs/kim_server.log (rotating file)
- stderr (console, for MCP client)

Log levels:
- DEBUG: Every tool call, validation step, embedding request
- INFO: Tool calls, major operations
- WARNING: Issues, fallbacks
- ERROR: Failures

Format:
2026-09-02 15:30:45.123 | INFO     | Tool: get_context | query="email to team"
2026-09-02 15:30:45.234 | DEBUG    | Retrieval | BM25 scores: 3 results
2026-09-02 15:30:45.345 | DEBUG    | Retrieval | Vector scores: 3 results
2026-09-02 15:30:45.456 | INFO     | Response | 156 tokens
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import os


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

def get_log_dir() -> Path:
    """Get log directory (~/.kim/logs/)."""
    kim_root = Path(os.getenv("KIM_DATA_DIR", Path.home() / ".kim"))
    log_dir = kim_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_level() -> int:
    """Get log level from environment."""
    level_str = os.getenv("KIM_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_str, logging.INFO)


# ═══════════════════════════════════════════════════════════
# CUSTOM FORMATTER
# ═══════════════════════════════════════════════════════════

class KIMFormatter(logging.Formatter):
    """
    Custom formatter with color support and structured output.

    Format: timestamp | level | module | message | context
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m"
    }

    def __init__(self, use_color: bool = False):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional color."""
        if self.use_color:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


# ═══════════════════════════════════════════════════════════
# LOGGER SETUP
# ═══════════════════════════════════════════════════════════

_loggers: dict[str, logging.Logger] = {}


def setup_logging():
    """
    Set up logging for KIM.

    Creates:
    - File handler: ~/.kim/logs/kim_server.log (rotating, 10MB, 5 backups)
    - Console handler: stderr (for MCP client visibility)
    """
    log_dir = get_log_dir()
    log_file = log_dir / "kim_server.log"
    log_level = get_log_level()

    # Root logger
    root_logger = logging.getLogger("kim")
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # File handler (detailed, rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Always DEBUG in file
    file_handler.setFormatter(KIMFormatter(use_color=False))
    root_logger.addHandler(file_handler)

    # Console handler (for MCP client)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(KIMFormatter(use_color=True))
    root_logger.addHandler(console_handler)

    # Log startup
    root_logger.info("=" * 60)
    root_logger.info("KIM MCP Server Starting")
    root_logger.info(f"Log level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (e.g., "server", "retrieval.hybrid")

    Returns:
        Configured logger

    Example:
        logger = get_logger("retrieval.hybrid")
        logger.info("Searching for relevant outputs")
        logger.debug(f"BM25 scores: {scores}")
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(f"kim.{name}")

    return _loggers[name]


# ═══════════════════════════════════════════════════════════
# STRUCTURED LOGGING HELPERS
# ═══════════════════════════════════════════════════════════

def log_tool_call(logger: logging.Logger, tool_name: str, arguments: dict):
    """
    Log an MCP tool call.

    Args:
        logger: Logger instance
        tool_name: Tool name (e.g., "get_context")
        arguments: Tool arguments
    """
    # Truncate long arguments for readability
    args_str = str(arguments)
    if len(args_str) > 200:
        args_str = args_str[:200] + "..."

    logger.info(f"Tool: {tool_name} | args={args_str}")


def log_validation(logger: logging.Logger, use_case: str, passed: bool, issue_count: int):
    """
    Log validation result.

    Args:
        logger: Logger instance
        use_case: Use case (messaging/coding/Mendix)
        passed: Whether validation passed
        issue_count: Number of issues found
    """
    status = "✓ PASSED" if passed else "✗ FAILED"
    logger.info(f"Validation: {use_case} | {status} | issues={issue_count}")


def log_retrieval(logger: logging.Logger, query: str, result_count: int, method: str):
    """
    Log retrieval operation.

    Args:
        logger: Logger instance
        query: Search query
        result_count: Number of results
        method: Retrieval method (bm25/vector/hybrid)
    """
    logger.info(f"Retrieval: {method} | query=\"{query[:50]}...\" | results={result_count}")


def log_embedding(logger: logging.Logger, text_length: int, success: bool):
    """
    Log embedding operation.

    Args:
        logger: Logger instance
        text_length: Length of text embedded
        success: Whether embedding succeeded
    """
    status = "✓" if success else "✗"
    logger.debug(f"Embedding: {status} | text_length={text_length}")


# ═══════════════════════════════════════════════════════════
# CONTEXT MANAGER FOR OPERATION TIMING
# ═══════════════════════════════════════════════════════════

import time
from contextlib import contextmanager


@contextmanager
def log_operation(logger: logging.Logger, operation: str):
    """
    Context manager for logging operation duration.

    Usage:
        with log_operation(logger, "hybrid_search"):
            results = search(query)
        # Logs: "hybrid_search completed in 45ms"
    """
    start = time.time()
    logger.debug(f"{operation} starting...")

    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.debug(f"{operation} completed in {duration_ms:.1f}ms")
