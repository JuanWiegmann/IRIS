"""
IRIS Log Viewer
==============

Interactive log viewer for analyzing IRIS operations.

Usage:
    python -m src.log_viewer                    # View recent logs
    python -m src.log_viewer --follow           # Follow logs in real-time
    python -m src.log_viewer --tool get_context # Filter by tool
    python -m src.log_viewer --detailed         # Show full details
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import time
import os


# ═══════════════════════════════════════════════════════════
# LOG PARSING
# ═══════════════════════════════════════════════════════════

def get_log_file() -> Path:
    """Get IRIS log file path."""
    iris_root = Path(os.getenv("IRIS_DATA_DIR", Path.home() / ".iris"))
    return iris_root / "logs" / "iris_server.log"


def parse_log_line(line: str) -> dict:
    """
    Parse a log line into structured data.

    Format: 2026-09-02 15:30:45 | INFO | module | message

    Returns:
        Dict with: timestamp, level, module, message
    """
    try:
        parts = line.split(" | ", 3)
        if len(parts) < 4:
            return {"raw": line}

        return {
            "timestamp": parts[0],
            "level": parts[1].strip(),
            "module": parts[2],
            "message": parts[3].strip()
        }
    except Exception:
        return {"raw": line}


def colorize(text: str, color: str) -> str:
    """Add ANSI color to text."""
    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def format_log_line(data: dict, detailed: bool = False) -> str:
    """
    Format parsed log line for display.

    Args:
        data: Parsed log data
        detailed: Show full details or compact

    Returns:
        Formatted string
    """
    if "raw" in data:
        return data["raw"]

    # Color by level
    level_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "magenta"
    }

    level = data["level"]
    color = level_colors.get(level, "reset")

    if detailed:
        return (
            f"{colorize(data['timestamp'], 'blue')} | "
            f"{colorize(level.ljust(8), color)} | "
            f"{colorize(data['module'], 'magenta')} | "
            f"{data['message']}"
        )
    else:
        # Compact: just timestamp, level, and message
        return (
            f"{data['timestamp'][-8:]} | "  # Just time HH:MM:SS
            f"{colorize(level[:4], color)} | "
            f"{data['message']}"
        )


# ═══════════════════════════════════════════════════════════
# FILTERING
# ═══════════════════════════════════════════════════════════

def should_show(data: dict, filters: dict) -> bool:
    """
    Check if log line matches filters.

    Args:
        data: Parsed log data
        filters: Filter criteria

    Returns:
        True if should show
    """
    if "raw" in data:
        return True

    # Filter by tool
    if filters.get("tool"):
        tool_name = filters["tool"]
        if f"Tool: {tool_name}" not in data.get("message", ""):
            return False

    # Filter by level
    if filters.get("level"):
        level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        min_level = level_priority.get(filters["level"], 0)
        current_level = level_priority.get(data.get("level", "INFO"), 1)
        if current_level < min_level:
            return False

    # Filter by module
    if filters.get("module"):
        if filters["module"] not in data.get("module", ""):
            return False

    return True


# ═══════════════════════════════════════════════════════════
# VIEWERS
# ═══════════════════════════════════════════════════════════

def view_recent(log_file: Path, lines: int, detailed: bool, filters: dict):
    """View recent log lines."""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        print("Run IRIS server first to generate logs.")
        return

    print(colorize("=" * 80, "blue"))
    print(colorize(f"IRIS Server Logs (last {lines} lines)", "blue"))
    print(colorize("=" * 80, "blue"))
    print()

    # Read last N lines
    with open(log_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        recent = all_lines[-lines:]

    shown = 0
    for line in recent:
        data = parse_log_line(line)
        if should_show(data, filters):
            print(format_log_line(data, detailed))
            shown += 1

    print()
    print(colorize(f"Showing {shown} of {len(recent)} lines", "cyan"))


def follow_logs(log_file: Path, detailed: bool, filters: dict):
    """Follow logs in real-time (like tail -f)."""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        print("Waiting for log file to be created...")
        while not log_file.exists():
            time.sleep(1)

    print(colorize("=" * 80, "blue"))
    print(colorize("Following IRIS Server Logs (Ctrl+C to stop)", "blue"))
    print(colorize("=" * 80, "blue"))
    print()

    with open(log_file, "r", encoding="utf-8") as f:
        # Go to end of file
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if line:
                    data = parse_log_line(line)
                    if should_show(data, filters):
                        print(format_log_line(data, detailed))
                else:
                    time.sleep(0.1)  # Wait for new lines
        except KeyboardInterrupt:
            print()
            print(colorize("Stopped following logs.", "yellow"))


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="View and analyze IRIS server logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.log_viewer                           # View last 50 lines
  python -m src.log_viewer --lines 100               # View last 100 lines
  python -m src.log_viewer --follow                  # Follow in real-time
  python -m src.log_viewer --tool get_context        # Filter by tool
  python -m src.log_viewer --level WARNING           # Show warnings and errors only
  python -m src.log_viewer --detailed                # Show full details
  python -m src.log_viewer --follow --detailed       # Follow with details
        """
    )

    parser.add_argument(
        "--lines",
        type=int,
        default=50,
        help="Number of recent lines to show (default: 50)"
    )

    parser.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Follow logs in real-time (like tail -f)"
    )

    parser.add_argument(
        "--tool",
        type=str,
        help="Filter by tool name (e.g., get_context)"
    )

    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Show only logs at this level or higher"
    )

    parser.add_argument(
        "--module",
        type=str,
        help="Filter by module name (e.g., retrieval.hybrid)"
    )

    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed format with timestamps and modules"
    )

    args = parser.parse_args()

    log_file = get_log_file()

    filters = {
        "tool": args.tool,
        "level": args.level,
        "module": args.module
    }

    if args.follow:
        follow_logs(log_file, args.detailed, filters)
    else:
        view_recent(log_file, args.lines, args.detailed, filters)


if __name__ == "__main__":
    main()
