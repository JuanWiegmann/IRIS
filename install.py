"""
IRIS Installer
=============

Automated installation and configuration for IRIS MCP server.

Usage:
    python install.py

What it does:
- Installs Python dependencies
- Clones Ponytail (code quality) and mxcli (Mendix support)
- Registers IRIS as MCP server in Claude Code config
- Optionally configures OpenAI API key for semantic search
- Verifies installation

For LLMs:
Run `python install.py` when user says:
"install iris", "setup iris", "configure iris"

After installation:
User runs `/startIris` in Claude Code to complete onboarding.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List


# ═══════════════════════════════════════════════════════════
# ANSI COLOR CODES
# ═══════════════════════════════════════════════════════════

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Wrap text in ANSI color codes."""
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"


def print_animated_logo():
    """Animated smiley on single line with different expressions."""

    # Animation frames - cycling through expressions
    frames = [
        # Neutral
        f"{colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •_• )', Colors.BRIGHT_CYAN)} {colorize('initializing...', Colors.DIM + Colors.WHITE)}",
        # Looking left (checking past)
        f"{colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( ←_• )', Colors.BRIGHT_MAGENTA)} {colorize('scanning memory...', Colors.DIM + Colors.WHITE)}",
        # Thinking
        f"{colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( ·_· )', Colors.WHITE)} {colorize('processing...', Colors.DIM + Colors.WHITE)}",
        # Looking right (seeing present)
        f"{colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •_→ )', Colors.BRIGHT_BLUE)} {colorize('ready to serve...', Colors.DIM + Colors.WHITE)}",
        # Happy
        f"{colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •‿• )', Colors.BRIGHT_GREEN, bold=True)} {colorize('JANUS online!', Colors.BRIGHT_GREEN)}",
    ]

    # Play animation on single line
    print()
    print()
    for frame in frames:
        sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line
        sys.stdout.write('    ' + frame)
        sys.stdout.flush()
        time.sleep(0.3)

    # Final frame - stays visible
    print()
    print()
    print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
    print(f"                {colorize('J A N U S', Colors.BRIGHT_WHITE, bold=True)}")
    print(f"                {colorize('( •‿• )', Colors.BRIGHT_GREEN, bold=True)}")
    print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
    print()
    print(f"       {colorize('Knowledge & Interaction Manager', Colors.BRIGHT_WHITE)}")
    print(f"       {colorize('Personalized AI for every LLM', Colors.DIM + Colors.WHITE)}")
    print()


def print_logo():
    """Wrapper for animated logo."""
    print_animated_logo()


def print_status(message: str, status: str = "info"):
    """Print a status message with Janus JANUS face."""
    if status == "success":
        face = colorize("( •‿• )", Colors.BRIGHT_GREEN, bold=True)  # Happy
    elif status == "error":
        face = colorize("( ×_× )", Colors.BRIGHT_RED, bold=True)  # Error
    elif status == "working":
        face = colorize("( ←_• )", Colors.BRIGHT_CYAN, bold=True)  # Working
    else:
        face = colorize("( •_• )", Colors.BRIGHT_BLUE)  # Neutral

    print(f"{face} {message}")


def print_progress(message: str, end: str = ''):
    """Print progress on same line with JANUS looking left (searching)."""
    face = colorize("( ←_• )", Colors.BRIGHT_CYAN, bold=True)
    print(f"\r{face} {message}...", end=end, flush=True)


def print_done(message: str):
    """Complete a progress line with happy JANUS face."""
    face = colorize("( •‿• )", Colors.BRIGHT_GREEN, bold=True)
    print(f"\r{face} {message}                    ")  # Extra spaces to clear


def print_skip(message: str):
    """Complete a progress line with neutral JANUS face."""
    face = colorize("( •_• )", Colors.DIM + Colors.YELLOW)
    print(f"\r{face} {message}                    ")


# ═══════════════════════════════════════════════════════════
# CONFIGURATION DETECTION
# ═══════════════════════════════════════════════════════════

def get_claude_config_path() -> Path:
    """
    Detect Claude Code config file location.

    Returns:
        Path to claude_desktop_config.json

    Raises:
        FileNotFoundError: If config location can't be determined
    """
    # Windows
    if sys.platform == "win32":
        appdata = Path(os.getenv("APPDATA", ""))
        config_path = appdata / "Claude" / "claude_desktop_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path

    # macOS
    elif sys.platform == "darwin":
        home = Path.home()
        config_path = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path

    # Linux
    else:
        home = Path.home()
        config_path = home / ".config" / "Claude" / "claude_desktop_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path


def get_iris_root() -> Path:
    """Get IRIS repository root (where this script lives)."""
    return Path(__file__).parent.absolute()


def is_claude_code_running() -> bool:
    """
    Check if Claude Code is currently running.

    Returns:
        True if Claude Code process is running, False otherwise
    """
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name']
                if name and 'claude' in name.lower():
                    # Check for Claude desktop app
                    if 'claude' in name.lower() or 'Claude' in str(proc.info.get('exe', '')):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception:
        # If psutil fails, assume not running
        return False


def close_claude_code_prompt():
    """
    Prompt user to close Claude Code if it's running.

    Returns:
        True if user confirms closed, False to abort
    """
    print()
    print(f"{colorize('( •_• )', Colors.BRIGHT_YELLOW, bold=True)} {colorize('Close Claude Code to continue installation.', Colors.BRIGHT_YELLOW)}")
    print()

    response = input(f"Press {colorize('Enter', Colors.BRIGHT_CYAN)} when closed (or {colorize('q', Colors.BRIGHT_RED)} to abort): ").strip().lower()

    if response == 'q':
        print(f"{colorize('( ×_× )', Colors.BRIGHT_RED, bold=True)} Aborted")
        return False

    if is_claude_code_running():
        print(f"{colorize('( ×_× )', Colors.BRIGHT_RED, bold=True)} Claude Code still running. Please close it and try again.")
        return False

    return True


def launch_claude_code() -> bool:
    """
    Attempt to launch Claude Code application.

    Returns:
        True if launch attempted, False if not found
    """
    try:
        if sys.platform == "win32":
            # Windows: Try to find Claude Code in common locations
            possible_paths = [
                Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "claude" / "Claude.exe",
                Path(os.getenv("PROGRAMFILES", "")) / "Claude" / "Claude.exe",
                Path(os.getenv("PROGRAMFILES(X86)", "")) / "Claude" / "Claude.exe",
            ]

            for path in possible_paths:
                if path.exists():
                    subprocess.Popen([str(path)], shell=True)
                    return True

        elif sys.platform == "darwin":
            # macOS: Use open command
            subprocess.Popen(["open", "-a", "Claude"])
            return True

        else:
            # Linux: Try common executable names
            for cmd in ["claude", "claude-code", "claude-desktop"]:
                try:
                    subprocess.Popen([cmd])
                    return True
                except FileNotFoundError:
                    continue

        return False

    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# DEPENDENCY INSTALLATION
# ═══════════════════════════════════════════════════════════

def install_dependencies():
    """Install Python dependencies."""
    print_progress("Installing dependencies")

    iris_root = get_iris_root()

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=iris_root,
            check=True,
            capture_output=True,
            text=True
        )
        print_done("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\r{colorize('( ×_× )', Colors.BRIGHT_RED, bold=True)} Dependencies failed: {e.stderr[:60]}")
        return False


# ═══════════════════════════════════════════════════════════
# MCP CONFIGURATION
# ═══════════════════════════════════════════════════════════

def register_mcp_server(api_key: str = None):
    """
    Register IRIS as MCP server in Claude Code config.

    Args:
        api_key: OpenAI API key (optional, can be set later)
    """
    print("\n🔧 Configuring Claude Code MCP server...")

    try:
        config_path = get_claude_config_path()
        iris_root = get_iris_root()

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Build IRIS server config
        iris_config = {
            "command": sys.executable,  # Use same Python as running this script
            "args": ["-m", "src.server"],
            "cwd": str(iris_root),
            "env": {
                "IRIS_LOG_LEVEL": "INFO"
            }
        }

        # Add API key if provided
        if api_key:
            iris_config["env"]["OPENAI_API_KEY"] = api_key

        # Register IRIS
        config["mcpServers"]["iris"] = iris_config

        # Write config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"✅ IRIS registered in: {config_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to configure MCP: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# API KEY SETUP
# ═══════════════════════════════════════════════════════════

def setup_api_key() -> str:
    """
    Guide user through API key setup.

    Returns:
        API key or empty string if skipped
    """
    print()
    print(f"{colorize('OpenAI API Key', Colors.BRIGHT_YELLOW)} {colorize('(optional, for semantic search)', Colors.DIM + Colors.WHITE)}")

    # Check if already set in environment
    existing_key = os.getenv("OPENAI_API_KEY")
    if existing_key:
        use_existing = input(f"Use existing key {colorize(existing_key[:10] + '...', Colors.BRIGHT_CYAN)}? (Y/n): ").strip().lower()
        if use_existing != "n":
            return existing_key

    # Ask for key
    api_key = input(f"{colorize('Enter API key', Colors.WHITE)} (or press Enter to skip): ").strip()

    if api_key and not api_key.startswith("sk-"):
        print(f"{colorize('Warning:', Colors.BRIGHT_YELLOW)} Key format may be invalid")

    return api_key


# ═══════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════

def test_iris_server_startup():
    """
    Test that IRIS server can actually start.

    Returns:
        True if server starts successfully, False otherwise
    """
    iris_root = get_iris_root()

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.server"],
            cwd=iris_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(3)

        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            return False

    except Exception:
        try:
            proc.terminate()
        except:
            pass
        return False


def verify_installation():
    """
    Comprehensive verification of installation.

    Tests:
    1. Module imports
    2. Server startup
    3. Storage directories

    Returns:
        True if all tests pass, False otherwise
    """
    print_progress("Verifying installation")

    # Test 1: Module imports
    try:
        from src.profile import get_or_create_profile
        from src.retrieval.hybrid import retrieve_relevant_outputs
        from src.validation.use_case_detector import detect_use_case
        from src.validation.deterministic import get_messaging_validator
    except ImportError:
        print(f"\r{colorize('✗', Colors.BRIGHT_RED, bold=True)} Module imports failed")
        return False

    # Test 2: Storage directories
    home = Path.home()
    iris_dir = home / ".iris"
    required_dirs = [
        iris_dir,
        iris_dir / "profiles",
        iris_dir / "outputs",
        iris_dir / "embeddings",
        iris_dir / "logs"
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Test 3: Server startup
    if not test_iris_server_startup():
        print(f"\r{colorize('✗', Colors.BRIGHT_RED, bold=True)} Server startup failed")
        return False

    print_done("Installation verified")
    return True


def backup_config(config_path: Path) -> Optional[Path]:
    """
    Create backup of Claude Code config.

    Args:
        config_path: Path to config file

    Returns:
        Path to backup file, or None if backup failed
    """
    if not config_path.exists():
        return None

    backup_path = config_path.with_suffix('.json.backup')
    try:
        import shutil
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        return None


def restore_config(config_path: Path, backup_path: Path):
    """
    Restore config from backup.

    Args:
        config_path: Path to config file
        backup_path: Path to backup file
    """
    try:
        import shutil
        shutil.copy2(backup_path, config_path)
        print(f"✅ Configuration restored from backup")
    except Exception as e:
        print(f"❌ Failed to restore backup: {e}")


# ═══════════════════════════════════════════════════════════
# MAIN SETUP FLOW
# ═══════════════════════════════════════════════════════════

def install_ponytail():
    """
    Install Ponytail plugin for code quality.

    Returns:
        True if installed/already present, False if failed
    """
    print_progress("Installing Ponytail")

    try:
        iris_root = get_iris_root()
        ponytail_dir = iris_root.parent / "ponytail"

        if not ponytail_dir.exists():
            subprocess.run(
                ["git", "clone", "https://github.com/DietrichGebert/ponytail.git", str(ponytail_dir)],
                check=True,
                capture_output=True,
                text=True
            )

        if (ponytail_dir / "requirements.txt").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=ponytail_dir,
                check=True,
                capture_output=True,
                text=True
            )

        print_done("Ponytail installed")
        return True, ponytail_dir

    except (subprocess.CalledProcessError, Exception):
        print_skip("Ponytail skipped")
        return False, None


def install_mendix_cli():
    """
    Install mxcli for Mendix low-code development.

    Returns:
        True if installed, False if failed
    """
    print_progress("Installing mxcli")

    try:
        iris_root = get_iris_root()
        mxcli_dir = iris_root.parent / "mxcli"

        if not mxcli_dir.exists():
            subprocess.run(
                ["git", "clone", "https://github.com/mendixlabs/mxcli.git", str(mxcli_dir)],
                check=True,
                capture_output=True,
                text=True
            )

        if (mxcli_dir / "requirements.txt").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=mxcli_dir,
                check=True,
                capture_output=True,
                text=True
            )
        elif (mxcli_dir / "setup.py").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                cwd=mxcli_dir,
                check=True,
                capture_output=True,
                text=True
            )

        print_done("mxcli installed")
        return True

    except (subprocess.CalledProcessError, Exception):
        print_skip("mxcli skipped")
        return False


def register_mcp_json():
    """Register IRIS in .mcp.json for Claude Code CLI."""
    try:
        iris_root = get_iris_root()
        mcp_json_path = iris_root / ".mcp.json"

        mcp_config = {
            "$schema": "https://github.com/modelcontextprotocol/servers/raw/main/schemas/mcp.schema.json",
            "mcpServers": {
                "iris": {
                    "command": sys.executable,
                    "args": ["-m", "src.server"],
                    "cwd": str(iris_root),
                    "env": {
                        "IRIS_LOG_LEVEL": "INFO"
                    }
                }
            }
        }

        with open(mcp_json_path, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2)

        return True

    except Exception:
        return False


def setup_memory_redirects():
    """
    Create memory redirect files so Claude Code uses IRIS as source of truth.

    Creates reference memory files that point to IRIS tools instead of
    duplicating user profile/preferences in local memory.

    Returns:
        True if created successfully, False otherwise
    """
    try:
        iris_root = get_iris_root()
        # Claude Code memory path pattern: ~/.claude/projects/<sanitized-path>/memory/
        # Sanitize path: replace backslashes, colons, spaces with hyphens
        sanitized_path = str(iris_root).replace("\\", "-").replace(":", "-").replace(" ", "-")
        memory_dir = Path.home() / ".claude" / "projects" / sanitized_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # MEMORY.md - index
        (memory_dir / "MEMORY.md").write_text("""# IRIS Memory Index

All user-specific memory lives in **IRIS**, the MCP server this project builds.

## Reference Pointers

- [User Profile](user_profile.md) — Call `mcp__iris__get_context(query)` for preferences, style, boundaries
- [Past Outputs](past_outputs.md) — Call `mcp__iris__get_context(query)` for relevant examples (ranked by similarity)
- [Onboarding](onboarding.md) — Use `/startIris` skill to create or update profile

## Why IRIS, Not Local Files?

IRIS is a **research-backed personalization system**:
- Hybrid BM25 + vector retrieval
- Output-driven personalization (Wu et al. 2024)
- GATE preference elicitation (Li et al., ICLR 2025)
- Semantic ranking of past outputs

Local memory files can't compete. Use IRIS tools, don't reinvent them.

## The Meta-Rule

**Before checking memory, check if IRIS can answer it.**

If the question is about:
- User preferences → `mcp__iris__get_context()`
- User's past work → `mcp__iris__get_context(query)`
- User's style → `mcp__iris__get_context()`

Don't store these in local memory — they're already in IRIS, and IRIS does it better.
""", encoding="utf-8")

        # user_profile.md
        (memory_dir / "user_profile.md").write_text("""---
name: user-profile
description: User preferences, communication style, tone, format preferences, boundaries
metadata:
  type: reference
---

User profile lives in **IRIS** (the MCP server this project builds).

**Always call:** `mcp__iris__get_context(query)`

Never duplicate profile data in memory files. IRIS is the source of truth.

**Why:** IRIS uses hybrid BM25 + vector retrieval with output-driven personalization (Wu et al. 2024). Local memory files can't match that sophistication.

**When to call:**
- User asks "what do you know about me?"
- Starting any task where user preferences matter
- Generating content (emails, docs, code comments)
- Need to understand user's communication style

**What you get:**
- Language, tone, format preferences
- Boundaries (code style, response structure, proactivity level)
- Current projects
- Relevant past outputs (ranked by semantic similarity to current query)
""", encoding="utf-8")

        # past_outputs.md
        (memory_dir / "past_outputs.md").write_text("""---
name: past-outputs
description: User's past work, approved outputs, examples of their style
metadata:
  type: reference
---

Past outputs are stored in **IRIS** and retrieved via semantic search.

**Always call:** `mcp__iris__get_context(query)` with a relevant query

The `query` parameter determines which past outputs are returned (ranked by relevance).

**Never:**
- Store past outputs in memory files
- Duplicate examples here
- Try to recall user's past work from conversation history

**Why:** IRIS uses Wu et al. (2024) output-driven personalization — past outputs are better predictors than past inputs. Retrieval is hybrid BM25 + vector similarity, contextualized to the current query.

**Related:** [[user-profile]] for communication preferences
""", encoding="utf-8")

        # onboarding.md
        (memory_dir / "onboarding.md").write_text("""---
name: onboarding
description: How to onboard the user or update their profile
metadata:
  type: reference
---

User onboarding is handled by **IRIS** via the `/startIris` skill.

**Trigger onboarding when:**
- User asks to "set up my profile"
- User wants to "personalize IRIS"
- User says "run onboarding"
- `mcp__iris__get_context()` returns "ONBOARDING_REQUIRED"

**How to trigger:** `/startIris` skill (not manual tool calls)

**What it does:**
- GATE-based preference elicitation (Li et al., ICLR 2025)
- Target-based questioning (communication style, code preferences, boundaries)
- Generates UserProfile after completion
- Takes 3-5 minutes

**Never:**
- Ask onboarding questions manually
- Store profile information in memory files
- Bypass the onboarding system

**Related:** [[user-profile]] for the profile structure
""", encoding="utf-8")

        return True

    except Exception:
        return False


def register_all_mcp_servers(api_key: str = None, ponytail_dir: Path = None):
    """
    Register IRIS + Ponytail + Mendix as MCP servers.

    Args:
        api_key: OpenAI API key (optional)
        ponytail_dir: Path to Ponytail directory (if installed)
    """
    print_progress("Registering MCP servers")

    try:
        config_path = get_claude_config_path()
        iris_root = get_iris_root()

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Register IRIS (always update cwd to current location)
        iris_config = {
            "command": sys.executable,
            "args": ["-m", "src.server"],
            "cwd": str(iris_root),
            "env": {
                "IRIS_LOG_LEVEL": "INFO"
            }
        }
        if api_key:
            iris_config["env"]["OPENAI_API_KEY"] = api_key
        # Preserve existing API key if present
        elif "iris" in config["mcpServers"] and "env" in config["mcpServers"]["iris"]:
            existing_key = config["mcpServers"]["iris"]["env"].get("OPENAI_API_KEY")
            if existing_key:
                iris_config["env"]["OPENAI_API_KEY"] = existing_key

        config["mcpServers"]["iris"] = iris_config

        # Register Ponytail (if installed)
        if ponytail_dir and ponytail_dir.exists():
            # Check for server.py or main.py in Ponytail
            ponytail_entry = None
            if (ponytail_dir / "server.py").exists():
                ponytail_entry = "server.py"
            elif (ponytail_dir / "src" / "server.py").exists():
                ponytail_entry = str(Path("src") / "server.py")

            if ponytail_entry:
                config["mcpServers"]["ponytail"] = {
                    "command": sys.executable,
                    "args": ["-m", ponytail_entry.replace(".py", "").replace(os.sep, ".")],
                    "cwd": str(ponytail_dir)
                }

        # Write config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print_done("MCP servers registered")
        return True

    except Exception as e:
        print(f"\r{colorize('✗', Colors.BRIGHT_RED, bold=True)} MCP registration failed: {str(e)[:50]}")
        return False


def validate_config_json(config_path: Path) -> bool:
    """
    Validate Claude Code config JSON.

    Args:
        config_path: Path to config file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False


def is_iris_installed() -> bool:
    """Check if IRIS is already installed."""
    try:
        config_path = get_claude_config_path()
        if not config_path.exists():
            return False

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Check if IRIS is registered in MCP servers
        return 'iris' in config.get('mcpServers', {})
    except Exception:
        return False


def main():
    """Main setup flow with full automation and rollback."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        # Enable ANSI colors on Windows
        os.system('')

    iris_root = get_iris_root()

    # Check if already installed
    if is_iris_installed():
        print()
        print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
        print(f"                {colorize('J A N U S', Colors.BRIGHT_WHITE, bold=True)}")
        print(f"                {colorize('( •‿• )', Colors.BRIGHT_GREEN, bold=True)}")
        print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
        print()
        print(f"       {colorize('JANUS ist bereits installiert!', Colors.BRIGHT_GREEN)}")
        print(f"       {colorize('IRIS is ready to use', Colors.WHITE)}")
        print()
        print(f"       Start Claude Code and run {colorize('/startIris', Colors.BRIGHT_CYAN, bold=True)} to begin")
        print()
        return

    # Not installed - show setup needed
    print()
    print(f"    {colorize('J A N U S', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •_• )', Colors.BRIGHT_CYAN)} {colorize('nicht bereit - Installation erforderlich', Colors.BRIGHT_YELLOW)}")
    print()

    # Check if Claude Code is running
    if is_claude_code_running():
        if not close_claude_code_prompt():
            sys.exit(0)

    # Backup existing config
    config_path = get_claude_config_path()
    backup_path = backup_config(config_path)

    try:
        # Install dependencies
        if not install_dependencies():
            raise Exception("Dependency installation failed")

        # API key setup
        api_key = setup_api_key()

        # Install plugins
        ponytail_installed, ponytail_dir = install_ponytail()
        mendix_installed = install_mendix_cli()

        # Register MCP servers
        if not register_all_mcp_servers(api_key, ponytail_dir):
            raise Exception("MCP server registration failed")
        register_mcp_json()

        # Setup memory redirects
        print_progress("Setting up memory integration")
        if setup_memory_redirects():
            print_done("Memory integration configured")
        else:
            print_skip("Memory integration skipped")

        # Validate configuration
        if not validate_config_json(config_path):
            raise Exception("Configuration validation failed")

        # Verify installation
        if not verify_installation():
            raise Exception("Installation verification failed")

        # Success - cleanup
        if backup_path and backup_path.exists():
            backup_path.unlink()

        # Show animated success
        print()
        print()
        success_frames = [
            f"    {colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •_• )', Colors.WHITE)} {colorize('Installation abgeschlossen...', Colors.WHITE)}",
            f"    {colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •_• )', Colors.BRIGHT_CYAN)} {colorize('Starte JANUS...', Colors.BRIGHT_CYAN)}",
            f"    {colorize('JANUS', Colors.BRIGHT_WHITE, bold=True)} {colorize('( •‿• )', Colors.BRIGHT_GREEN, bold=True)} {colorize('JANUS bereit!', Colors.BRIGHT_GREEN, bold=True)}",
        ]

        for frame in success_frames:
            sys.stdout.write('\r' + ' ' * 100 + '\r')
            sys.stdout.write(frame)
            sys.stdout.flush()
            time.sleep(0.4)

        print()
        print()
        print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
        print(f"                {colorize('J A N U S', Colors.BRIGHT_WHITE, bold=True)}")
        print(f"                {colorize('( •‿• )', Colors.BRIGHT_GREEN, bold=True)}")
        print(f"    {colorize('═══════════════════════════════════════', Colors.BRIGHT_CYAN)}")
        print()

        # Show what was installed
        installed = [colorize("IRIS", Colors.BRIGHT_CYAN)]
        if ponytail_installed:
            installed.append(colorize("Ponytail", Colors.BRIGHT_MAGENTA))
        if mendix_installed:
            installed.append(colorize("mxcli", Colors.BRIGHT_BLUE))
        print(f"       {colorize('Installed:', Colors.WHITE)} {', '.join(installed)}")
        print(f"       {colorize('Location:', Colors.WHITE)} {colorize(str(iris_root), Colors.DIM + Colors.WHITE)}")
        print()
        print(f"       {colorize('Next:', Colors.BRIGHT_YELLOW, bold=True)} Start Claude Code and run {colorize('/startIris', Colors.BRIGHT_CYAN, bold=True)}")
        if not api_key:
            print(f"       {colorize('Note:', Colors.DIM + Colors.YELLOW)} Skipped OpenAI key (add later for semantic search)")
        print()

    except Exception as e:
        # Rollback on failure
        print()
        print(f"{colorize('( ×_× )', Colors.BRIGHT_RED, bold=True)} {colorize('Installation failed', Colors.BRIGHT_RED)}: {str(e)[:60]}")

        if backup_path and backup_path.exists():
            restore_config(config_path, backup_path)
            backup_path.unlink()

        print()
        print(f"{colorize('( •_• )', Colors.WHITE)} {colorize('Logs:', Colors.WHITE)} ~/.iris/logs/iris_server.log")
        print(f"{colorize('( •_• )', Colors.WHITE)} {colorize('Report:', Colors.WHITE)} https://github.com/JuanWiegmann/IRIS/issues")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()
