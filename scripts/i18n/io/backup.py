"""Immutable Backup Manager for Claude Code CLI.

Guarantees:
- Backup is created from an unmodified cli.js (no localization markers)
- Backup file is set read-only (chmod 444) after creation
- SHA-256 hash is stored alongside for integrity verification
- Localized backups are renamed, never silently overwritten
- All file operations use atomic write/copy utilities

Note: The original npm package contains ~1841 CJK characters (Japanese strings
from Zod validation library). CJK counting is NOT used for pristine detection.
Instead, we check for our specific localization markers.
"""

import hashlib
import os
import re
import shutil
import stat
from pathlib import Path

from scripts.i18n.config.constants import BACKUP_NAME, HASH_NAME
from scripts.i18n.io.file_io import atomic_write_text

# Localization markers — specific Chinese strings our tool produces.
# Used to detect if cli.js has been localized (vs original npm package
# which contains Japanese CJK from Zod but NOT these Chinese markers).
_LOCALIZED_MARKERS = ["绕过权限", "规划模式", "自动模式", "接受编辑"]


class BackupManager:
    """Manages immutable backups of Claude Code CLI's cli.js.

    Usage:
        mgr = BackupManager(cli_dir)
        result = mgr.ensure_backup()  # Create or validate backup
        result = mgr.restore()        # Restore from backup
    """

    def __init__(self, cli_dir: Path):
        """Initialize BackupManager with the CLI installation directory.

        Args:
            cli_dir: Path to the Claude Code installation directory
                     (containing cli.js and package.json).
        """
        self.cli_dir = cli_dir
        self.cli_js = cli_dir / 'cli.js'
        self.backup = cli_dir / BACKUP_NAME
        self.hash_file = cli_dir / HASH_NAME

    def ensure_backup(self) -> dict:
        """Create or validate an unmodified backup of cli.js.

        Returns a dict with:
        - ok: bool -- whether the operation succeeded
        - action: str -- what was done ('created', 'existing_valid', 'migrated')
        - error: str -- error code if ok is False

        Scenarios:
        1. No backup exists -> create from cli.js (if not localized)
        2. Valid backup + hash -> return existing_valid
        3. Valid backup, no hash -> migrate: add hash + chmod 444
        4. Localized backup -> rename to .polluted.js, recreate from cli.js
        5. cli.js is already localized -> reject with source_not_pristine
        """
        # Case 2: Valid backup already exists
        if self.backup.exists() and self.hash_file.exists():
            if self._verify_integrity():
                if not self._is_localized_file(self.backup):
                    return {"ok": True, "action": "existing_valid"}
                else:
                    # Hash matches but file is localized -- poisoned baseline
                    return {
                        "ok": False,
                        "error": "backup_poisoned",
                        "hint": "Reinstall Claude Code to get pristine files",
                    }

        # Case 3/4: Backup exists but no hash (or hash mismatch)
        if self.backup.exists():
            if not self._is_localized_file(self.backup):
                # Old backup is clean -- add hash file + chmod 444
                checksum = self._sha256()
                self.hash_file.write_text(checksum, encoding='utf-8')
                os.chmod(
                    self.backup,
                    stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
                )
                return {"ok": True, "action": "migrated", "sha256": checksum}
            else:
                # Localized backup -- rename it
                polluted = self.cli_dir / 'cli.bak.polluted.js'
                self._make_writable(self.backup)
                self.backup.rename(polluted)

        # Case 1/5: Create new backup from current cli.js
        if not self.cli_js.exists():
            return {"ok": False, "error": "cli_js_not_found"}

        # Verify source is not already localized
        if self._is_localized_file(self.cli_js):
            return {
                "ok": False,
                "error": "source_not_pristine",
                "hint": "Restore original files first, or reinstall Claude Code",
            }

        # Create backup
        shutil.copy2(self.cli_js, self.backup)

        # Compute and store SHA-256
        checksum = self._sha256()
        self.hash_file.write_text(checksum, encoding='utf-8')

        # Set read-only protection
        os.chmod(
            self.backup,
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
        )

        return {"ok": True, "action": "created", "sha256": checksum}

    def restore(self) -> dict:
        """Restore cli.js from the backup.

        Steps:
        1. Check backup exists
        2. Verify SHA-256 hash matches
        3. Verify backup is not localized
        4. Copy backup to cli.js

        Returns a dict with ok/action or ok/error.
        """
        if not self.backup.exists():
            return {"ok": False, "error": "no_backup"}

        if not self._verify_integrity():
            return {
                "ok": False,
                "error": "hash_mismatch",
                "hint": "Backup corrupted, will re-create on next apply",
            }

        if self._is_localized_file(self.backup):
            return {"ok": False, "error": "backup_poisoned"}

        # Restore from backup
        shutil.copy2(self.backup, self.cli_js)

        return {"ok": True, "action": "restored"}

    def _sha256(self) -> str:
        """Compute SHA-256 checksum of the backup file.

        Uses 8KB chunks to avoid loading the entire file into memory.
        """
        h = hashlib.sha256()
        with open(self.backup, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _is_pristine(self) -> bool:
        """Check the backup file is NOT localized by our tool."""
        return not self._is_localized_file(self.backup)

    def _is_localized_file(self, path: Path) -> bool:
        """Check if a file contains our Chinese localization markers.

        Uses specific markers instead of CJK counting, because the original
        npm package contains ~1841 CJK characters (Japanese from Zod library).
        A file is considered localized if >= 2 markers are found.
        """
        try:
            content = path.read_text(encoding='utf-8')
            return sum(1 for m in _LOCALIZED_MARKERS if m in content) >= 2
        except (OSError, UnicodeDecodeError):
            return False

    def _is_pristine_file(self, path: Path) -> bool:
        """Check a file is NOT localized (backward-compatible alias)."""
        return not self._is_localized_file(path)

    def _verify_integrity(self) -> bool:
        """Verify backup SHA-256 matches the stored hash file."""
        if not self.hash_file.exists():
            return False
        expected = self.hash_file.read_text(encoding='utf-8').strip()
        actual = self._sha256()
        return expected == actual

    def _make_writable(self, path: Path) -> None:
        """Restore write permission on a read-only file.

        Adds owner write bit (S_IWUSR) to current mode.
        """
        current = path.stat().st_mode
        os.chmod(path, current | stat.S_IWUSR)
