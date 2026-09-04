"""Quick verification that IRIS is globally registered."""
import json
import os
import subprocess
import sys
from pathlib import Path

config_path = Path(os.getenv('APPDATA')) / 'Claude' / 'claude_desktop_config.json'

print("=" * 60)
print("IRIS GLOBAL SETUP VERIFICATION")
print("=" * 60)
print()

# Check 1: Config exists
print("[1/3] Checking global Claude config...")
if config_path.exists():
    print(f"  [OK] Found: {config_path}")
else:
    print(f"  [ERROR] Not found: {config_path}")
    sys.exit(1)

# Check 2: IRIS registered
print()
print("[2/3] Checking IRIS registration...")
config = json.load(open(config_path, 'r', encoding='utf-8'))
if 'mcpServers' in config and 'iris' in config['mcpServers']:
    iris_config = config['mcpServers']['iris']
    print(f"  [OK] IRIS is registered")
    print(f"  Command: {iris_config['command']}")
    print(f"  Working dir: {iris_config['cwd']}")
else:
    print("  [ERROR] IRIS not found in mcpServers")
    sys.exit(1)

# Check 3: Server starts
print()
print("[3/3] Testing IRIS server startup...")
iris_dir = Path(iris_config['cwd'])
try:
    proc = subprocess.Popen(
        [iris_config['command'], '-m', 'src.server'],
        cwd=iris_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    import time
    time.sleep(2)

    if proc.poll() is None:
        print("  [OK] Server started successfully")
        proc.terminate()
        proc.wait(timeout=3)
    else:
        stdout, stderr = proc.communicate()
        print(f"  [ERROR] Server failed: {stderr[:200]}")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Test failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("[SUCCESS] IRIS is globally configured!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Restart Claude Code (completely close and reopen)")
print("  2. Open Claude Code from ANY folder")
print("  3. Ask: 'What MCP tools are available?'")
print("  4. You should see: get_context, log_output, check_draft")
print()
