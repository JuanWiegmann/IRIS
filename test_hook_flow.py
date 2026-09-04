#!/usr/bin/env python3
"""
Test Hook → Claude Flow
=======================

Simulates what happens when SessionStart hook fires.
"""

import subprocess
import sys
from pathlib import Path

def test_hook():
    """Run the hook and capture output."""
    print("=" * 60)
    print("Testing SessionStart Hook")
    print("=" * 60)
    print()

    hook_script = Path(__file__).parent / ".claude" / "hooks" / "iris_profile_check.py"

    result = subprocess.run(
        [sys.executable, str(hook_script)],
        capture_output=True,
        text=True
    )

    print("Hook Output:")
    print("-" * 60)
    print(result.stdout)
    print("-" * 60)

    if result.stderr:
        print("Hook Errors:")
        print(result.stderr)

    print()
    print("Exit Code:", result.returncode)
    print()

    if result.returncode == 0 and result.stdout:
        print("✅ Hook fires successfully")
        print()
        print("❓ QUESTION: Does Claude SEE this output?")
        print()
        print("The hook output above should appear as a system-reminder")
        print("in Claude's context when starting a session in this project.")
        print()
        print("If Claude doesn't call start_onboarding(), it means:")
        print("  1. Hook output isn't reaching Claude")
        print("  2. Hook output format is wrong")
        print("  3. Claude sees it but doesn't act on it")
    else:
        print("❌ Hook failed")

if __name__ == "__main__":
    test_hook()
