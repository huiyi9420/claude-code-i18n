"""JavaScript syntax verification for Claude Code i18n engine.

Uses Node.js --check flag to validate JavaScript syntax after translations
are applied. Handles edge cases: missing file, node not installed, timeout.

APPLY-07: node --check validates JS syntax after replacements.
APPLY-08: Syntax failure should trigger automatic rollback to backup.
"""

import subprocess
from pathlib import Path


def verify_syntax(js_path: Path, timeout: int = 10) -> dict:
    """Verify JavaScript syntax with node --check.

    Args:
        js_path: Path to the JavaScript file to validate.
        timeout: Maximum seconds to wait for node --check (default 10).

    Returns:
        dict with:
        - ok: True if syntax is valid, False otherwise
        - error: None on success, error description string on failure
    """
    if not js_path.exists():
        return {"ok": False, "error": f"file not found: {js_path}"}

    try:
        r = subprocess.run(
            ["node", "--check", str(js_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if r.returncode == 0:
            return {"ok": True, "error": None}
        return {"ok": False, "error": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "node --check timed out"}
    except FileNotFoundError:
        return {"ok": False, "error": "node not found -- is Node.js installed?"}
