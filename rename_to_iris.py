"""
IRIS Rename Script
==================

Renames entire KIM project to IRIS:
- All text references (KIM → IRIS, kim → iris)
- File names
- Folder names
- Config paths
- Variable names

Usage:
    python rename_to_iris.py
"""

import os
import re
import shutil
from pathlib import Path


# Text replacements (order matters!)
REPLACEMENTS = [
    # Full caps
    ('KIM', 'IRIS'),
    # Lowercase
    ('kim', 'iris'),
    # Title case
    ('Kim', 'Iris'),
    # Paths
    ('~/.kim', '~/.iris'),
    ('.kim/', '.iris/'),
    # Config keys
    ('"kim"', '"iris"'),
    ("'kim'", "'iris'"),
    # Skills
    ('startKim', 'startIris'),
    ('/startKim', '/startIris'),
    # Variables
    ('kim_', 'iris_'),
]

# Files to rename
FILE_RENAMES = [
    ('.claude/hooks/kim_profile_check.py', '.claude/hooks/iris_profile_check.py'),
    ('.claude/skills/startKim', '.claude/skills/startIris'),
]

# Folders to rename (after all processing)
FOLDER_RENAME = ('KIM', 'IRIS')


def replace_in_file(file_path: Path):
    """Replace all KIM references in a file."""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply replacements
        modified = content
        for old, new in REPLACEMENTS:
            modified = modified.replace(old, new)

        # Write back if changed
        if modified != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)
            return True
        return False
    except Exception as e:
        print(f"  ⚠ Error in {file_path}: {e}")
        return False


def rename_files_and_folders(root: Path):
    """Rename files and folders containing 'kim'."""
    renamed = []

    # Rename specific files first
    for old_rel, new_rel in FILE_RENAMES:
        old_path = root / old_rel
        new_path = root / new_rel

        if old_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
            renamed.append((old_rel, new_rel))
            print(f"  ✓ Renamed: {old_rel} → {new_rel}")

    return renamed


def main():
    # Fix Windows console encoding
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print()
    print("=" * 45)
    print("  RENAMING KIM → IRIS")
    print("=" * 45)
    print()

    root = Path(__file__).parent

    # Step 1: Update text in all files
    print("Step 1: Updating text in files...")

    file_patterns = ['*.py', '*.md', '*.json', '*.txt']
    updated_count = 0

    for pattern in file_patterns:
        for file_path in root.rglob(pattern):
            # Skip this script itself
            if file_path.name == 'rename_to_iris.py':
                continue

            # Skip node_modules, .git, etc.
            if any(part.startswith('.') and part != '.claude' for part in file_path.parts):
                continue

            if replace_in_file(file_path):
                updated_count += 1

    print(f"  ✓ Updated {updated_count} files")
    print()

    # Step 2: Rename specific files/folders
    print("Step 2: Renaming files and folders...")
    renamed = rename_files_and_folders(root)
    print()

    # Step 3: Instructions for manual folder rename
    print("Step 3: Final folder rename")
    print(f"  ⚠ You must manually rename the parent folder:")
    print(f"     {root.parent / 'KIM'} → {root.parent / 'IRIS'}")
    print()
    print("  Commands:")
    print(f"     cd {root.parent}")
    print(f"     mv KIM IRIS")
    print()

    # Summary
    print()
    print("=" * 45)
    print("  RENAME COMPLETE!")
    print("=" * 45)
    print()
    print("Summary:")
    print(f"  • Updated {updated_count} files")
    print(f"  • Renamed {len(renamed)} files/folders")
    print()
    print("Next steps:")
    print("  1. Rename parent folder (see above)")
    print("  2. Run: python install.py")
    print("  3. Test: /startIris in Claude Code")
    print()


if __name__ == "__main__":
    main()
