"""
Build IRIS GUI Installer
=========================

Compiles iris_gui_installer.py into a windowed .exe (no console).

Requirements:
    pip install pyinstaller

Usage:
    python build_gui_installer.py

Output:
    dist/IRIS-Setup.exe (GUI installer, no CMD window)
"""

import subprocess
import sys
import shutil
from pathlib import Path


def build_gui_installer():
    """Build GUI installer executable."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print()
    print("╔═══════════════════════════════════════════════════╗")
    print("║                                                   ║")
    print("║         Building IRIS GUI Installer              ║")
    print("║                                                   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found")
        print()
        print("Install: pip install pyinstaller")
        return False

    print()
    print("► Building GUI executable...")
    print()

    try:
        # PyInstaller command
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",                          # Single file
            "--windowed",                         # No console window
            "--name=IRIS-Setup",                  # Output name
            "--icon=NONE",                        # No icon (or add your own)
            "--clean",                            # Clean cache
            "iris_gui_installer.py"
        ]

        result = subprocess.run(cmd, check=True, text=True)

        print()
        print("✓ Build complete!")
        print()

        # Show output location
        exe_path = Path("dist") / "IRIS-Setup.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Output: {exe_path}")
            print(f"Size:   {size_mb:.1f} MB")
            print()
            print("GUI Installer ready!")
            print("User double-clicks → Modern window opens → Installation starts")
        else:
            print("⚠️  Warning: Expected output not found")

        print()
        return True

    except subprocess.CalledProcessError:
        print()
        print("✗ Build failed")
        return False


def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")

    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["IRIS-Setup.spec"]

    for d in dirs_to_remove:
        if Path(d).exists():
            shutil.rmtree(d)
            print(f"  Removed: {d}/")

    for f in files_to_remove:
        if Path(f).exists():
            Path(f).unlink()
            print(f"  Removed: {f}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build IRIS GUI installer")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    args = parser.parse_args()

    if args.clean:
        clean_build()
    else:
        if build_gui_installer():
            print("Build successful!")
        else:
            print("Build failed!")
            sys.exit(1)
