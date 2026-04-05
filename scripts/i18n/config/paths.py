"""Path Resolver for Claude Code CLI installation.

Implements 5-level cascading detection:
1. CLAUDE_I18N_CLI_DIR environment variable (highest priority)
2. ~/.claude/i18n.json config file
3. Volta: 'volta which claude' -> resolve() -> cli.js
4. npm global: 'npm root -g' + package name
5. Common hardcoded paths (fallback)
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from scripts.i18n.config.constants import PKG_NAME


def find_cli_install_dir() -> Tuple[Optional[Path], str]:
    """Find Claude Code CLI installation directory.

    Returns:
        (package_dir, method_used) on success, or (None, 'not_found') on failure.
        method_used is one of: 'env_var', 'config_file', 'volta', 'npm_global',
        'common_path', 'not_found'.
    """
    home = Path.home()

    # Strategy 1: Environment variable
    env_dir = os.environ.get('CLAUDE_I18N_CLI_DIR')
    if env_dir:
        p = Path(env_dir)
        if validate_cli_dir(p):
            return p, 'env_var'

    # Strategy 2: Config file
    config_path = home / '.claude' / 'i18n.json'
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            custom = config.get('cli_path')
            if custom and validate_cli_dir(Path(custom)):
                return Path(custom), 'config_file'
        except (json.JSONDecodeError, OSError):
            pass

    # Strategy 3: Volta
    if shutil.which('volta'):
        try:
            r = subprocess.run(
                ['volta', 'which', 'claude'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                resolved = Path(r.stdout.strip()).resolve()
                if resolved.name == 'cli.js' and validate_cli_dir(resolved.parent):
                    return resolved.parent, 'volta'
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Strategy 4: npm global
    try:
        r = subprocess.run(
            ['npm', 'root', '-g'],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            npm_root = Path(r.stdout.strip())
            cli_dir = npm_root / PKG_NAME
            if validate_cli_dir(cli_dir):
                return cli_dir, 'npm_global'
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Strategy 5: Common paths
    common_paths = [
        home / '.volta/tools/image/packages/{}/lib/node_modules/{}'.format(PKG_NAME, PKG_NAME),
        Path('/usr/local/lib/node_modules') / PKG_NAME,
        Path('/opt/homebrew/lib/node_modules') / PKG_NAME,
    ]
    for p in common_paths:
        if validate_cli_dir(p):
            return p, 'common_path'

    return None, 'not_found'


def validate_cli_dir(p: Path) -> bool:
    """Verify directory is a valid Claude Code installation.

    Checks:
    - p is a directory
    - p/cli.js exists
    - p/package.json exists
    - package.json 'name' field equals PKG_NAME
    """
    if not p.is_dir():
        return False
    cli_js = p / 'cli.js'
    pkg_json = p / 'package.json'
    if not (cli_js.exists() and pkg_json.exists()):
        return False
    try:
        meta = json.loads(pkg_json.read_text(encoding='utf-8'))
        return meta.get('name') == PKG_NAME
    except (json.JSONDecodeError, OSError):
        return False
