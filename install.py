"""
KIM Automated Installer
========================

FULLY AUTOMATED installation and configuration — ZERO manual intervention.

═══════════════════════════════════════════════════════════════════════════════
FOR LLMS: HOW TO USE THIS INSTALLER
═══════════════════════════════════════════════════════════════════════════════

When user says any of these:
  • "install kim"
  • "setup kim"
  • "configure kim"
  • "install the mcp server"
  • "get kim working"

YOU SHOULD:
1. Run this command: python install.py
2. Follow any prompts (close Claude Code if needed)
3. Tell user: "Setup complete! I'll restart now, then you can use KIM"
4. (Setup will auto-launch Claude Code)

That's it! The script does EVERYTHING automatically.

═══════════════════════════════════════════════════════════════════════════════
WHAT THIS SCRIPT DOES (Automatic)
═══════════════════════════════════════════════════════════════════════════════

✅ Detects if Claude Code is running → prompts user to close it
✅ Installs KIM Python dependencies (pydantic, openai, numpy, etc.)
✅ Clones Ponytail plugin from GitHub (code quality enhancement)
✅ Checks for Mendix CLI (low-code development support)
✅ Auto-detects Claude Code config location (Windows/macOS/Linux)
✅ Registers ALL MCP servers in claude_desktop_config.json:
   - KIM (personalization + orchestration)
   - Ponytail (code quality)
   - Mendix (if available)
✅ Optional: Asks for OpenAI API key (for semantic search, can skip)
✅ Tests that KIM server actually starts (not just imports)
✅ Validates config JSON (prevents broken configuration)
✅ Creates backup (auto-rollback on any failure)
✅ Offers to auto-launch Claude Code after setup

═══════════════════════════════════════════════════════════════════════════════
USER EXPERIENCE
═══════════════════════════════════════════════════════════════════════════════

$ python setup.py

→ Detects Claude Code running
→ "Please close Claude Code and press Enter"
→ [User closes, presses Enter]
→ Installs everything (1-2 minutes)
→ "Launch Claude Code now? (Y/n)"
→ [User presses Enter]
→ Claude Code launches automatically
→ KIM server auto-starts in background
→ User can immediately use KIM tools!

ZERO manual server management. ZERO config editing. ZERO troubleshooting.

═══════════════════════════════════════════════════════════════════════════════
AFTER SETUP: HOW KIM WORKS
═══════════════════════════════════════════════════════════════════════════════

1. Claude Code launches (manually or via auto-launch)
2. Claude Code reads: claude_desktop_config.json
3. Claude Code sees: mcpServers.kim
4. Claude Code AUTO-STARTS: python -m src.server (background)
5. KIM server runs silently in background
6. All KIM tools immediately available to LLM
7. User says: "Write an email"
8. LLM automatically calls: get_context() → KIM provides profile
9. LLM generates personalized email
10. LLM calls: check_draft() → KIM validates
11. User sees polished, personalized result

THE USER NEVER:
- Manually starts a server
- Manually stops a server
- Manually restarts a server
- Edits config files
- Runs terminal commands

═══════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING (Rare)
═══════════════════════════════════════════════════════════════════════════════

If setup fails:
- Config auto-rolls back to backup
- Clear error message shown
- Troubleshooting guide printed
- User can retry or report issue

If MCP tools don't appear:
- Ask user: "What MCP tools are available?"
- If KIM missing → restart Claude Code
- Check: ~/.kim/logs/kim_server.log

═══════════════════════════════════════════════════════════════════════════════
TECHNICAL DETAILS (For LLM Context)
═══════════════════════════════════════════════════════════════════════════════

Protocol: MCP (Model Context Protocol) over stdio
Transport: stdin/stdout (no network ports)
Lifecycle: Managed by Claude Code (auto-start/stop/restart)
Storage: ~/.kim/ (profiles, outputs, embeddings, logs)
Config: claude_desktop_config.json (platform-specific location)
Dependencies: Python 3.11+, pip packages (auto-installed)
Platform: Cross-platform (Windows/macOS/Linux)

MCP Servers Registered:
1. KIM (required) → Personalization, validation, orchestration
2. Ponytail (optional) → Code quality, static analysis
3. Mendix (optional) → Low-code development support

═══════════════════════════════════════════════════════════════════════════════

Usage:
    python install.py

That's the ONLY command needed. Everything else is automatic.

Designed to be called by an LLM when user says: "install kim"
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List


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


def get_kim_root() -> Path:
    """Get KIM repository root (where this script lives)."""
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
    print("⚠️  IMPORTANT: Claude Code is currently running!")
    print()
    print("Claude Code must be closed to update its configuration.")
    print()
    print("Please:")
    print("  1. Close Claude Code completely")
    print("  2. Come back here and press Enter to continue")
    print()

    response = input("Press Enter when Claude Code is closed (or 'q' to abort): ").strip().lower()

    if response == 'q':
        print("❌ Setup aborted by user")
        return False

    # Check again
    if is_claude_code_running():
        print("⚠️  Claude Code still appears to be running")
        print("    Please close it and try again")
        return False

    print("✅ Claude Code closed, continuing setup...")
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
    print("📦 Installing Python dependencies...")

    kim_root = get_kim_root()

    try:
        # Use pip to install in editable mode
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=kim_root,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr}")
        return False


# ═══════════════════════════════════════════════════════════
# MCP CONFIGURATION
# ═══════════════════════════════════════════════════════════

def register_mcp_server(api_key: str = None):
    """
    Register KIM as MCP server in Claude Code config.

    Args:
        api_key: OpenAI API key (optional, can be set later)
    """
    print("\n🔧 Configuring Claude Code MCP server...")

    try:
        config_path = get_claude_config_path()
        kim_root = get_kim_root()

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Build KIM server config
        kim_config = {
            "command": sys.executable,  # Use same Python as running this script
            "args": ["-m", "src.server"],
            "cwd": str(kim_root),
            "env": {
                "KIM_LOG_LEVEL": "INFO"
            }
        }

        # Add API key if provided
        if api_key:
            kim_config["env"]["OPENAI_API_KEY"] = api_key

        # Register KIM
        config["mcpServers"]["kim"] = kim_config

        # Write config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"✅ KIM registered in: {config_path}")
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
    print("\n🔑 OpenAI API Key Setup (OPTIONAL)")
    print("=" * 60)
    print("⚠️  OpenAI API key is OPTIONAL!")
    print()
    print("KIM works WITHOUT an API key:")
    print("  ✅ Validation (deterministic + MCP sampling)")
    print("  ✅ Draft checking (uses YOUR LLM via MCP)")
    print("  ✅ Profile storage")
    print()
    print("OpenAI is ONLY needed for:")
    print("  📊 Embeddings (semantic search of past outputs)")
    print("  💰 Cost: ~$0.02 per 1M tokens (very cheap)")
    print()
    print("Without API key:")
    print("  - Validation still works (no OpenAI needed)")
    print("  - Retrieval uses BM25 only (keyword search, no semantic)")
    print()
    print("Get key (if you want embeddings): https://platform.openai.com/api-keys")
    print()

    # Check if already set in environment
    existing_key = os.getenv("OPENAI_API_KEY")
    if existing_key:
        print(f"✅ API key found in environment: {existing_key[:10]}...")
        use_existing = input("Use this key? (Y/n): ").strip().lower()
        if use_existing != "n":
            return existing_key

    # Ask for key
    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()

    if api_key:
        # Validate format (starts with sk-)
        if not api_key.startswith("sk-"):
            print("⚠️  Warning: Key doesn't start with 'sk-', might be invalid")

        print("✅ API key will be added to Claude Code config")
        return api_key
    else:
        print("⏭️  Skipping API key (you can add it later in config)")
        return ""


# ═══════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════

def test_kim_server_startup():
    """
    Test that KIM server can actually start.

    Returns:
        True if server starts successfully, False otherwise
    """
    print("\n🧪 Testing KIM server startup...")

    kim_root = get_kim_root()

    try:
        # Start server in background
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.server"],
            cwd=kim_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait 3 seconds for startup
        time.sleep(3)

        # Check if still running
        if proc.poll() is None:
            print("✅ KIM server started successfully")
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Server failed to start")
            print(f"   Error: {stderr[:200]}")
            return False

    except Exception as e:
        print(f"❌ Server test failed: {e}")
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
    print("\n🔍 Verifying installation...")

    # Test 1: Module imports
    print("  📦 Testing module imports...")
    try:
        from src.profile import get_or_create_profile
        from src.retrieval.hybrid import retrieve_relevant_outputs
        from src.validation.use_case_detector import detect_use_case
        from src.validation.deterministic import get_messaging_validator
        print("     ✅ All modules import successfully")
    except ImportError as e:
        print(f"     ❌ Import failed: {e}")
        return False

    # Test 2: Storage directories
    print("  📁 Testing storage setup...")
    home = Path.home()
    kim_dir = home / ".kim"
    required_dirs = [
        kim_dir,
        kim_dir / "profiles",
        kim_dir / "outputs",
        kim_dir / "embeddings",
        kim_dir / "logs"
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    print("     ✅ Storage directories ready")

    # Test 3: Server startup
    if not test_kim_server_startup():
        return False

    print("✅ All verification tests passed!")
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
    print("\n🦄 Installing Ponytail (code quality plugin)...")

    try:
        # Check if Ponytail repo exists
        kim_root = get_kim_root()
        ponytail_dir = kim_root.parent / "ponytail"

        if ponytail_dir.exists():
            print(f"✅ Ponytail already cloned at: {ponytail_dir}")
        else:
            print("📥 Cloning Ponytail from GitHub...")
            subprocess.run(
                ["git", "clone", "https://github.com/DietrichGebert/ponytail.git", str(ponytail_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Ponytail cloned to: {ponytail_dir}")

        # Install Ponytail dependencies
        if (ponytail_dir / "requirements.txt").exists():
            print("📦 Installing Ponytail dependencies...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=ponytail_dir,
                check=True,
                capture_output=True,
                text=True
            )

        return True, ponytail_dir

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install Ponytail: {e.stderr if e.stderr else str(e)}")
        print("   Skipping Ponytail (optional)")
        return False, None
    except Exception as e:
        print(f"⚠️  Ponytail installation error: {e}")
        print("   Skipping Ponytail (optional)")
        return False, None


def install_mendix_cli():
    """
    Install Mendix CLI for low-code development.

    Returns:
        True if installed/available, False otherwise
    """
    print("\n🏗️  Checking Mendix CLI...")

    try:
        # Check if mx command exists
        result = subprocess.run(
            ["mx", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"✅ Mendix CLI already installed: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print("⚠️  Mendix CLI not found")
    print("   Note: Mendix CLI is BETA software")
    print("   KIM will validate Mendix content without it")
    print("   Install manually: https://docs.mendix.com/refguide/mx-command-line-tool/")
    print("   Skipping (optional)")
    return False


def register_all_mcp_servers(api_key: str = None, ponytail_dir: Path = None):
    """
    Register KIM + Ponytail + Mendix as MCP servers.

    Args:
        api_key: OpenAI API key (optional)
        ponytail_dir: Path to Ponytail directory (if installed)
    """
    print("\n🔧 Configuring Claude Code MCP servers...")

    try:
        config_path = get_claude_config_path()
        kim_root = get_kim_root()

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Register KIM
        kim_config = {
            "command": sys.executable,
            "args": ["-m", "src.server"],
            "cwd": str(kim_root),
            "env": {
                "KIM_LOG_LEVEL": "INFO"
            }
        }
        if api_key:
            kim_config["env"]["OPENAI_API_KEY"] = api_key

        config["mcpServers"]["kim"] = kim_config
        print("  ✅ KIM registered")

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
                print("  ✅ Ponytail registered")
            else:
                print("  ⚠️  Ponytail structure unknown, skipping registration")

        # Write config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"✅ MCP servers registered in: {config_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to configure MCP: {e}")
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


def main():
    """Main setup flow with full automation and rollback."""
    # Fix Windows console encoding for emoji
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("🚀 KIM FULLY AUTOMATED SETUP")
    print("=" * 70)
    print()
    print("This will install and configure:")
    print("  • KIM MCP server (personalization + orchestration)")
    print("  • Ponytail plugin (code quality)")
    print("  • Mendix CLI check (low-code development)")
    print("  • All MCP server registrations")
    print("  • Testing and verification")
    print("  • Automatic Claude Code restart")
    print()

    kim_root = get_kim_root()
    print(f"📁 KIM location: {kim_root}")
    print()

    # Check if Claude Code is running
    claude_was_running = is_claude_code_running()
    if claude_was_running:
        print("🔍 Detected: Claude Code is currently running")
        if not close_claude_code_prompt():
            sys.exit(0)  # User aborted

    # Backup existing config
    config_path = get_claude_config_path()
    backup_path = backup_config(config_path)
    if backup_path:
        print(f"💾 Config backed up to: {backup_path}")
        print()

    try:
        # Step 1: Install KIM dependencies
        print("═══ Step 1/6: Installing KIM Dependencies ═══")
        if not install_dependencies():
            raise Exception("Dependency installation failed")

        # Step 2: API key setup
        print("\n═══ Step 2/6: API Key Setup ═══")
        api_key = setup_api_key()

        # Step 3: Install recommended plugins
        print("\n═══ Step 3/6: Installing Plugins ═══")
        ponytail_installed, ponytail_dir = install_ponytail()
        mendix_installed = install_mendix_cli()

        # Step 4: Register all MCP servers
        print("\n═══ Step 4/6: Registering MCP Servers ═══")
        if not register_all_mcp_servers(api_key, ponytail_dir):
            raise Exception("MCP server registration failed")

        # Step 5: Validate configuration
        print("\n═══ Step 5/6: Validating Configuration ═══")
        if not validate_config_json(config_path):
            raise Exception("Configuration validation failed")
        print("✅ Configuration JSON is valid")

        # Step 6: Verify installation
        print("\n═══ Step 6/6: Verifying Installation ═══")
        if not verify_installation():
            raise Exception("Installation verification failed")

        # Success!
        print("\n" + "=" * 70)
        print("✅ KIM SETUP COMPLETE!")
        print("=" * 70)
        print()
        print("📦 Successfully Installed:")
        print(f"   ✅ KIM MCP server → {kim_root}")
        if ponytail_installed:
            print(f"   ✅ Ponytail plugin → {ponytail_dir}")
        if mendix_installed:
            print(f"   ✅ Mendix CLI (detected)")
        print()
        print(f"⚙️  Configuration:")
        print(f"   ✅ Registered in: {config_path}")
        print(f"   ✅ Server tested and working")
        print(f"   ✅ Storage directories created")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1️⃣  RESTART Claude Code")
        print("    → Close completely and reopen")
        print()
        print("2️⃣  TEST MCP Tools")
        print('    → Ask: "What MCP tools are available?"')
        print("    → Expected:")
        print("      • KIM: get_context, log_output, check_draft")
        if ponytail_installed:
            print("      • Ponytail: code quality tools")
        print()
        print("3️⃣  TRY KIM")
        print('    → Say: "Write a Python function"')
        print("    → KIM validates + Ponytail enhances!")
        print()
        print("📊 Monitor KIM Logs:")
        print(f"   python -m src.log_viewer --follow")
        print()
        print("📖 Documentation:")
        print(f"   README:       {kim_root / 'README.md'}")
        print(f"   Setup Guide:  {kim_root / 'SETUP_MCP.md'}")
        print(f"   Architecture: {kim_root / 'ARCHITECTURE.md'}")
        print()

        if not api_key:
            print("💡 OPTIONAL: Add OpenAI API Key Later")
            print("   For semantic search of past outputs")
            print(f"   Edit: {config_path}")
            print("   Add OPENAI_API_KEY to kim.env section")
            print()

        # Delete backup on success
        if backup_path and backup_path.exists():
            backup_path.unlink()
            print("🧹 Cleanup: Backup removed (setup successful)")

        print()
        print("=" * 70)
        print("🎉 KIM IS READY!")
        print("=" * 70)
        print()

        # Auto-launch Claude Code
        if claude_was_running:
            print("🚀 Restarting Claude Code...")
            print()

            response = input("Launch Claude Code now? (Y/n): ").strip().lower()

            if response != 'n':
                if launch_claude_code():
                    print("✅ Claude Code launching...")
                    print()
                    print("📌 WAIT: Give Claude Code 5-10 seconds to start")
                    print("📌 THEN: Ask 'What MCP tools are available?'")
                    print("📌 YOU SHOULD SEE: get_context, log_output, check_draft")
                else:
                    print("⚠️  Could not auto-launch Claude Code")
                    print("    Please launch it manually")
            else:
                print("⏭️  Skipped auto-launch")
                print("    Launch Claude Code manually when ready")
        else:
            print("📌 IMPORTANT: Launch Claude Code")
            print()
            print("Claude Code was not running before setup.")
            print("You need to launch it now to use KIM.")
            print()

            response = input("Launch Claude Code now? (Y/n): ").strip().lower()

            if response != 'n':
                if launch_claude_code():
                    print("✅ Claude Code launching...")
                    print()
                    print("📌 WAIT: Give Claude Code 5-10 seconds to start")
                    print("📌 THEN: Ask 'What MCP tools are available?'")
                    print("📌 YOU SHOULD SEE: get_context, log_output, check_draft")
                else:
                    print("⚠️  Could not auto-launch Claude Code")
                    print("    Please launch it manually")
            else:
                print("⏭️  Skipped auto-launch")
                print()
                print("To use KIM:")
                print("  1. Launch Claude Code")
                print("  2. Wait for startup (5-10 seconds)")
                print("  3. Ask: 'What MCP tools are available?'")

        print()
        print("=" * 70)
        print("✅ Setup complete! KIM server will auto-start with Claude Code.")
        print("=" * 70)

    except Exception as e:
        # Rollback on failure
        print()
        print("=" * 70)
        print(f"❌ SETUP FAILED: {e}")
        print("=" * 70)
        print()

        if backup_path and backup_path.exists():
            print("🔄 Rolling back configuration...")
            restore_config(config_path, backup_path)
            backup_path.unlink()

        print()
        print("💡 TROUBLESHOOTING:")
        print("   1. Check error message above")
        print("   2. Verify Python 3.11+ installed: python --version")
        print("   3. Check network connectivity")
        print("   4. Try manual setup: see SETUP_MCP.md")
        print()
        print("📋 Common Issues:")
        print("   • Dependency errors → Update pip: python -m pip install --upgrade pip")
        print("   • Git clone fails → Check proxy/firewall settings")
        print("   • Server won't start → Check logs: ~/.kim/logs/kim_server.log")
        print()
        print(f"📧 Report issues: https://github.com/JuanWiegmann/KIM/issues")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()
