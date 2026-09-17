import sys
import json

try:
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
    
    # Files protected from accidental modifications
    protected_targets = ["conftest.py", ".env"]
    
    if any(target in file_path for target in protected_targets):
        sys.stderr.write(f"\n[BLOCKED BY HOOK] Modification to protected file '{file_path}' is denied.\n")
        sys.exit(1)
except Exception:
    pass

sys.exit(0)