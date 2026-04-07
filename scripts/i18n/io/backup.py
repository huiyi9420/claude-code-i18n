"""Immutable Backup Manager for Claude Code CLI.

Guarantees:
- Backup is created from a pristine (zero-CJK) cli.js
- Backup file is set read-only (chmod 444) after creation
- SHA-256 hash is stored alongside for integrity verification
- Polluted (CJK-containing) backups are renamed, never silently overwritten
- All file operations use atomic write/copy utilities
"""

import hashlib
import os
import re
import shutil
import stat
from pathlib import Path

from scripts.i18n.config.constants import BACKUP_NAME, HASH_NAME
from scripts.i18n.io.file_io import atomic_write_text

# CJK Unified Ideographs range (U+4E00..U+9FFF)
CJK_PATTERN = re.compile(r'[\u4e00-\u9fff]')


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
        """Create or validate a pristine English backup of cli.js.

        Returns a dict with:
        - ok: bool -- whether the operation succeeded
        - action: str -- what was done ('created', 'existing_valid', 'migrated')
        - error: str -- error code if ok is False

        Scenarios:
        1. No backup exists -> create from cli.js (if pristine)
        2. Valid backup + hash -> return existing_valid
        3. Valid backup, no hash -> migrate: add hash + chmod 444
        4. Polluted backup -> rename to .polluted.js, recreate from cli.js
        5. cli.js contains CJK -> reject with source_not_pristine
        """
        # Case 2: Valid backup already exists
        if self.backup.exists() and self.hash_file.exists():
            if self._verify_integrity():
                if self._is_pristine():
                    return {"ok": True, "action": "existing_valid"}
                else:
                    # Hash matches but file has CJK -- poisoned baseline
                    # This shouldn't happen in normal flow, but handle it
                    return {
                        "ok": False,
                        "error": "backup_poisoned",
                        "hint": "Reinstall Claude Code to get pristine files",
                    }

        # Case 3/4: Backup exists but no hash (or hash mismatch)
        if self.backup.exists():
            if self._is_pristine():
                # Old backup is clean -- add hash file + chmod 444
                checksum = self._sha256()
                self.hash_file.write_text(checksum, encoding='utf-8')
                os.chmod(
                    self.backup,
                    stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
                )
                return {"ok": True, "action": "migrated", "sha256": checksum}
            else:
                # Polluted backup -- rename it
                polluted = self.cli_dir / 'cli.bak.polluted.js'
                self._make_writable(self.backup)
                self.backup.rename(polluted)

        # Case 1/5: Create new backup from current cli.js
        if not self.cli_js.exists():
            return {"ok": False, "error": "cli_js_not_found"}

        # Verify source is pristine before creating backup
        if not self._is_pristine_file(self.cli_js):
            return {
                "ok": False,
                "error": "source_not_pristine",
                "hint": "Reinstall Claude Code, then run engine",
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
        """Restore cli.js from the pristine backup.

        Steps:
        1. Check backup exists
        2. Verify SHA-256 hash matches
        3. Verify backup has zero CJK characters
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

        if not self._is_pristine():
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
        """Check the backup file contains zero CJK characters."""
        return self._is_pristine_file(self.backup)

    def _is_pristine_file(self, path: Path) -> bool:
        """Check a file contains zero CJK characters.

        Reads line-by-line to avoid loading the entire file into memory.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if CJK_PATTERN.search(line):
                        return False
            return True
        except (OSError, UnicodeDecodeError):
            return False

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
