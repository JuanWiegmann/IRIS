# IRIS Standalone Installer

Shareable Windows executable that installs IRIS in one click.

## Features

- **Retro console UI** — Clean, minimal design
- **Automatic setup** — Clones repo + runs install.py
- **Single file** — Share the .exe, no dependencies needed
- **Animated progress** — User knows it's working, not frozen

## For Developers: Build the Installer

### Requirements

```bash
pip install pyinstaller
```

### Build Command

```bash
python build_installer.py
```

### Output

```
dist/IRIS-Installer.exe  (standalone executable, ~10-15 MB)
```

### Clean Build Artifacts

```bash
python build_installer.py --clean
```

## For Users: Install IRIS

### Method 1: Use the .exe (Recommended)

1. Download `IRIS-Installer.exe`
2. Double-click to run
3. Follow the retro console prompts
4. Done!

### Method 2: Run Python Script Directly

```bash
python iris_standalone_installer.py
```

## What It Does

```
Step 1: Check prerequisites
  ✓ Git found
  ✓ Python found

Step 2: Download IRIS
  ► Cloning IRIS repository...
  ✓ IRIS repository cloned

Step 3: Run IRIS installer
  (runs install.py with animated progress)

╔════════════════════════════════════════════════════╗
║                                                    ║
║          I N S T A L L A T I O N   C O M P L E T E ║
║                    ( •‿• )                         ║
║                                                    ║
╚════════════════════════════════════════════════════╝

Next: Start Claude Code and run /startIris
```

## Default Install Location

```
%USERPROFILE%\IRIS
```

Example: `C:\Users\YourName\IRIS`

## Requirements (Auto-Checked)

- **Git** — https://git-scm.com/download/win
- **Python 3.11+** — https://www.python.org/downloads/

## Sharing the Installer

The .exe is portable and self-contained:

1. Build once: `python build_installer.py`
2. Share `dist/IRIS-Installer.exe` (via file share, USB, email)
3. Users run it → IRIS installs automatically

## Security Note

This installer:
- Clones from official GitHub repo (https://github.com/JuanWiegmann/IRIS)
- Runs install.py from that repo
- No network requests to external servers (except GitHub)

Users can inspect `iris_standalone_installer.py` source before building.

## Troubleshooting

**"Git not found"**
→ Install Git: https://git-scm.com/download/win

**"Python not found"**
→ Install Python 3.11+: https://www.python.org/downloads/

**"Clone timeout"**
→ Check network connection / firewall

**Build fails**
→ Ensure PyInstaller installed: `pip install pyinstaller`

## Technical Details

- **Script:** `iris_standalone_installer.py` (Python 3.11+)
- **Builder:** `build_installer.py` (uses PyInstaller)
- **UI:** ANSI colors, retro console boxes
- **Animation:** Threaded dot animation (prevents freeze perception)
- **Size:** ~10-15 MB (includes Python runtime)
