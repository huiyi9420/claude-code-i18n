#!/usr/bin/env python3
"""Claude Code i18n Engine - CLI Entry Point.

Usage:
    python scripts/engine.py <command>

Commands:
    status   Show current i18n status
    restore  Restore original English CLI
    version  Show CLI version
    apply    Apply Chinese localization (Phase 2)
    extract  Extract translatable strings (Phase 2)
"""

import sys
from pathlib import Path

# Add project root to sys.path for imports (scripts.i18n.*)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.i18n.cli import main

if __name__ == '__main__':
    main()
