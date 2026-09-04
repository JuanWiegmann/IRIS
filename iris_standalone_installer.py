"""
IRIS Standalone Installer
=========================

Retro-style console installer that:
1. Clones IRIS repository
2. Runs install.py
3. Self-contained, shareable executable

Build:
    pyinstaller --onefile --noconsole --name=IRIS-Installer iris_standalone_installer.py
"""

import os
import sys
import subprocess
import time
import tempfile
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# RETRO CONSOLE COLORS
# ═══════════════════════════════════════════════════════════

class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    BRIGHT_CYAN = '\033[96m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_YELLOW = '\033[93m'


# ═══════════════════════════════════════════════════════════
# RETRO UI
# ═══════════════════════════════════════════════════════════

def clear_screen():
    """Clear console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_box(text, width=60, color=Color.CYAN):
    """Print text in retro box."""
    line = "═" * (width - 2)
    print(f"{color}╔{line}╗{Color.RESET}")

    # Center text
    padding = (width - 2 - len(text)) // 2
    padded = " " * padding + text + " " * (width - 2 - len(text) - padding)
    print(f"{color}║{Color.RESET}{padded}{color}║{Color.RESET}")

    print(f"{color}╚{line}╝{Color.RESET}")


def print_header():
    """Print retro IRIS header."""
    clear_screen()
    print()
    print(f"{Color.BRIGHT_CYAN}    ╔════════════════════════════════════════════════════╗{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}    ║{Color.RESET}                                                    {Color.BRIGHT_CYAN}║{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}    ║{Color.RESET}              {Color.BOLD}{Color.WHITE}I R I S   I N S T A L L E R{Color.RESET}              {Color.BRIGHT_CYAN}║{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}    ║{Color.RESET}                    {Color.BRIGHT_GREEN}{Color.BOLD}( •‿• ){Color.RESET}                        {Color.BRIGHT_CYAN}║{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}    ║{Color.RESET}                                                    {Color.BRIGHT_CYAN}║{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}    ╚════════════════════════════════════════════════════╝{Color.RESET}")
    print()


def animate_dots(message, duration=2.0):
    """Animate loading dots."""
    frames = ['   ', '.  ', '.. ', '...']
    steps = int(duration / 0.3)

    for i in range(steps):
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r    {Color.BRIGHT_CYAN}►{Color.RESET} {message}{frame}")
        sys.stdout.flush()
        time.sleep(0.3)


def print_step(step_num, total, message):
    """Print step indicator."""
    print(f"\n    {Color.CYAN}[{step_num}/{total}]{Color.RESET} {message}")


def print_success(message):
    """Print success message."""
    print(f"\r    {Color.BRIGHT_GREEN}✓{Color.RESET} {message}                    ")


def print_error(message):
    """Print error message."""
    print(f"\r    {Color.BRIGHT_RED}✗{Color.RESET} {message}")


# ═══════════════════════════════════════════════════════════
# INSTALLATION LOGIC
# ═══════════════════════════════════════════════════════════

def check_git():
    """Check if git is installed."""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except:
        return False


def check_python():
    """Check if Python 3.11+ is available."""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip()
        return True, version
    except:
        return False, None


def clone_iris_repo(target_dir):
    """
    Clone IRIS repository.

    Args:
        target_dir: Where to clone

    Returns:
        True if successful, False otherwise
    """
    try:
        # Animated clone
        import threading
        stop_animation = threading.Event()

        def animate():
            frames = ['   ', '.  ', '.. ', '...']
            i = 0
            while not stop_animation.is_set():
                frame = frames[i % len(frames)]
                sys.stdout.write(f"\r    {Color.BRIGHT_CYAN}►{Color.RESET} Cloning IRIS repository{frame}")
                sys.stdout.flush()
                time.sleep(0.3)
                i += 1

        anim_thread = threading.Thread(target=animate)
        anim_thread.start()

        subprocess.run(
            ["git", "clone", "https://github.com/JuanWiegmann/IRIS.git", str(target_dir)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        stop_animation.set()
        anim_thread.join()

        print_success("IRIS repository cloned")
        return True

    except subprocess.TimeoutExpired:
        stop_animation.set()
        anim_thread.join()
        print_error("Clone timeout (check network)")
        return False
    except subprocess.CalledProcessError as e:
        stop_animation.set()
        anim_thread.join()
        print_error(f"Clone failed: {e.stderr[:40] if e.stderr else 'unknown error'}")
        return False


def run_install(iris_dir):
    """
    Run install.py from cloned repo.

    Args:
        iris_dir: IRIS directory path

    Returns:
        True if successful, False otherwise
    """
    install_script = iris_dir / "install.py"

    if not install_script.exists():
        print_error("install.py not found in repo")
        return False

    try:
        print()
        print(f"    {Color.DIM}─────────────────────────────────────────────────────{Color.RESET}")
        print()

        # Run install.py (inherit output to show progress)
        result = subprocess.run(
            [sys.executable, str(install_script)],
            cwd=iris_dir,
            check=True,
            timeout=600  # 10 minutes max
        )

        print()
        print(f"    {Color.DIM}─────────────────────────────────────────────────────{Color.RESET}")
        print()

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print_error("Installation timeout")
        return False
    except subprocess.CalledProcessError:
        print_error("Installation failed")
        return False


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    """Main installer flow."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        os.system('')  # Enable ANSI colors

    print_header()

    # Step 1: Check prerequisites
    print_step(1, 3, "Checking prerequisites")
    print()

    # Check Git
    animate_dots("Checking Git", 1.0)
    if not check_git():
        print_error("Git not found")
        print()
        print(f"    {Color.YELLOW}Install Git:{Color.RESET} https://git-scm.com/download/win")
        print()
        input(f"    Press Enter to exit...")
        return 1
    print_success("Git found")

    # Check Python
    animate_dots("Checking Python", 1.0)
    has_python, version = check_python()
    if not has_python:
        print_error("Python not found")
        print()
        input(f"    Press Enter to exit...")
        return 1
    print_success(f"Python found ({version})")

    # Step 2: Clone repository
    print_step(2, 3, "Downloading IRIS")
    print()

    # Use temp directory or user choice
    default_dir = Path.home() / "IRIS"
    print(f"    {Color.WHITE}Install location:{Color.RESET} {default_dir}")
    print()

    choice = input(f"    Press Enter to continue (or 'q' to quit): ").strip().lower()
    if choice == 'q':
        print()
        print_error("Installation cancelled")
        return 0

    print()

    # Clone
    if not clone_iris_repo(default_dir):
        print()
        input(f"    Press Enter to exit...")
        return 1

    # Step 3: Run installation
    print_step(3, 3, "Running IRIS installer")
    print()

    if not run_install(default_dir):
        print()
        print_error("Installation failed")
        print()
        print(f"    {Color.WHITE}Check logs at:{Color.RESET} {default_dir / 'install.log'}")
        print()
        input(f"    Press Enter to exit...")
        return 1

    # Success!
    print()
    print(f"{Color.BRIGHT_GREEN}    ╔════════════════════════════════════════════════════╗{Color.RESET}")
    print(f"{Color.BRIGHT_GREEN}    ║{Color.RESET}                                                    {Color.BRIGHT_GREEN}║{Color.RESET}")
    print(f"{Color.BRIGHT_GREEN}    ║{Color.RESET}          {Color.BRIGHT_GREEN}{Color.BOLD}I N S T A L L A T I O N   C O M P L E T E{Color.RESET}          {Color.BRIGHT_GREEN}║{Color.RESET}")
    print(f"{Color.BRIGHT_GREEN}    ║{Color.RESET}                    {Color.BRIGHT_GREEN}{Color.BOLD}( •‿• ){Color.RESET}                        {Color.BRIGHT_GREEN}║{Color.RESET}")
    print(f"{Color.BRIGHT_GREEN}    ║{Color.RESET}                                                    {Color.BRIGHT_GREEN}║{Color.RESET}")
    print(f"{Color.BRIGHT_GREEN}    ╚════════════════════════════════════════════════════╝{Color.RESET}")
    print()
    print(f"    {Color.WHITE}Next:{Color.RESET} Start Claude Code and run {Color.BRIGHT_CYAN}/startIris{Color.RESET}")
    print()
    print()

    input(f"    Press Enter to exit...")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print(f"    {Color.YELLOW}Installation cancelled{Color.RESET}")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"    {Color.BRIGHT_RED}Unexpected error:{Color.RESET} {str(e)[:60]}")
        print()
        input(f"    Press Enter to exit...")
        sys.exit(1)
