"""
KIM Automated Setup
===================

One-command installation and configuration.

Usage:
    python setup.py

This script:
1. Installs Python dependencies
2. Detects Claude Code configuration location
3. Registers KIM as MCP server
4. Guides through API key setup
5. Tests the connection

Designed to be called by an LLM when user says: "install kim"
"""

import json
import os
import subprocess
import sys
from pathlib import Path


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
            capture_output=True
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr.decode()}")
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
    print("\n🔑 OpenAI API Key Setup")
    print("=" * 60)
    print("KIM uses OpenAI for embeddings (text-embedding-3-small)")
    print("Cost: ~$0.02 per 1M tokens (very cheap)")
    print()
    print("Get your API key: https://platform.openai.com/api-keys")
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

def verify_installation():
    """Test that KIM can start."""
    print("\n🧪 Testing KIM server...")

    try:
        # Try importing key modules
        from src.profile import get_or_create_profile
        from src.retrieval import embed_text
        from src.validation import detect_use_case

        print("✅ All modules import successfully")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# MAIN SETUP FLOW
# ═══════════════════════════════════════════════════════════

def main():
    """Main setup flow."""
    print("=" * 60)
    print("🚀 KIM Automated Setup")
    print("=" * 60)
    print()

    kim_root = get_kim_root()
    print(f"📁 KIM location: {kim_root}")
    print()

    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)

    # Step 2: API key setup
    api_key = setup_api_key()

    # Step 3: Register MCP server
    if not register_mcp_server(api_key):
        print("\n❌ Setup failed at MCP configuration")
        sys.exit(1)

    # Step 4: Verify installation
    if not verify_installation():
        print("\n❌ Setup failed at verification")
        sys.exit(1)

    # Success!
    print("\n" + "=" * 60)
    print("✅ KIM Setup Complete!")
    print("=" * 60)
    print()
    print("📋 Next Steps:")
    print("1. Restart Claude Code (close and reopen)")
    print("2. Ask: 'What MCP tools are available?'")
    print("3. You should see: get_context, log_output, check_draft")
    print()
    print("📊 Monitor KIM:")
    print(f"   python -m src.log_viewer --follow")
    print()
    print("📖 Full Documentation:")
    print(f"   {kim_root / 'SETUP_MCP.md'}")
    print()

    if not api_key:
        config_path = get_claude_config_path()
        print("⚠️  Remember to add your OpenAI API key to:")
        print(f"   {config_path}")
        print("   (Add OPENAI_API_KEY to env section)")
        print()


if __name__ == "__main__":
    main()
