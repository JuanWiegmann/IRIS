"""
IRIS Installation Checker
=========================

Checks if all components are installed:
1. iris-server command
2. MCP config (~/.claude/mcp.json)
3. CLAUDE.md global instructions
4. mxcli (optional VW tool)
5. Ponytail config
"""
import subprocess
import json
import sys
import time
from pathlib import Path


# Spinner frames (npm-style)
SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']


def spinner_check(label, check_fn):
    """
    Run check with animated spinner (npm-style).

    Args:
        label: What's being checked
        check_fn: Function that returns (bool, msg) or bool

    Returns:
        (status, msg)
    """
    # Start spinner
    for i in range(5):  # ~0.5 seconds
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        sys.stdout.write(f'\r{frame} Checking {label}...')
        sys.stdout.flush()
        time.sleep(0.1)

    # Run check
    result = check_fn()

    # Handle result
    if isinstance(result, tuple):
        status, msg = result
    else:
        status = result
        msg = "OK" if status else "Missing"

    # Clear spinner line
    sys.stdout.write('\r' + ' ' * 60 + '\r')
    sys.stdout.flush()

    return status, msg


def check_iris_server():
    """Check if iris-server command exists."""
    try:
        result = subprocess.run(
            ["iris-server", "--help"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def check_mcp_config():
    """Check if MCP config exists and has iris entry."""
    mcp_path = Path.home() / ".claude" / "mcp.json"

    if not mcp_path.exists():
        return False, "File missing"

    try:
        with open(mcp_path) as f:
            config = json.load(f)

        if "mcpServers" not in config:
            return False, "No mcpServers key"

        if "iris" not in config["mcpServers"]:
            return False, "No iris entry"

        iris_config = config["mcpServers"]["iris"]
        if iris_config.get("command") != "iris-server":
            return False, f"Wrong command: {iris_config.get('command')}"

        return True, "OK"
    except Exception as e:
        return False, f"Parse error: {e}"


def check_claude_md():
    """Check if global CLAUDE.md exists."""
    claude_md = Path.home() / ".claude" / "CLAUDE.md"

    if not claude_md.exists():
        return False, "File missing"

    content = claude_md.read_text()

    if "IRIS" not in content:
        return False, "No IRIS section"

    if "get_context" not in content:
        return False, "No protocol"

    return True, "OK"


def check_mxcli():
    """Check if mxcli is installed (optional)."""
    try:
        result = subprocess.run(
            ["mxcli", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0, "OK"
    except:
        return False, "Not installed (optional)"


def check_ponytail():
    """Check if Ponytail config exists."""
    # Check settings.json first (most reliable)
    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)

            hooks = settings.get("hooks", {})
            if "SessionStart:compact" in hooks:
                hook_data = hooks["SessionStart:compact"]
                if isinstance(hook_data, dict) and hook_data.get("script"):
                    content = hook_data["script"]
                    if "ponytail" in content.lower():
                        return True, "Active in SessionStart hook"
        except:
            pass

    # Fallback: check standalone file
    ponytail_path = Path.home() / ".claude" / "ponytail.md"
    if ponytail_path.exists():
        return True, "OK (file exists)"

    return False, "Not configured"


def main():
    # Fix Windows console encoding
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print()
    print("\033[1m\033[36m>> IRIS Installation Check\033[0m")
    print()

    checks = [
        ("iris-server command", check_iris_server),
        ("MCP config", check_mcp_config),
        ("Global CLAUDE.md", check_claude_md),
        ("mxcli (optional)", check_mxcli),
        ("Ponytail config", check_ponytail),
    ]

    all_ok = True
    results = []

    # Run checks with animation
    for name, check_fn in checks:
        status, msg = spinner_check(name, check_fn)
        results.append((name, status, msg))

        if not status and "optional" not in msg.lower():
            all_ok = False

    # Print results (npm-style)
    print()
    for name, status, msg in results:
        if status:
            symbol = "\033[32m✓\033[0m"  # Green checkmark
        else:
            symbol = "\033[31m✗\033[0m"  # Red X

        print(f"{symbol} {name:25} \033[2m{msg}\033[0m")

    print()
    print("=" * 60)

    if all_ok:
        print("\033[32mSTATUS: All required components installed\033[0m")
        print()
        print("✨ IRIS is ready to use!")
        return 0
    else:
        print("\033[33mSTATUS: Some components missing\033[0m")
        print()
        print("Run: \033[36mpython install.py\033[0m")
        return 1


if __name__ == "__main__":
    exit(main())
