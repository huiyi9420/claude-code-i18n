"""Tests for BackupManager (BAK-01 ~ BAK-04, BAK-06, BAK-07)."""

import hashlib
import os
import stat
from pathlib import Path

import pytest

from scripts.i18n.config.constants import BACKUP_NAME, HASH_NAME
from scripts.i18n.io.backup import BackupManager


@pytest.fixture
def pristine_cli_dir(tmp_path):
    """Create a CLI dir with pure-English cli.js (no CJK)."""
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()
    (cli_dir / 'cli.js').write_text(
        'var e={title:"Claude Code",msg:"Permission denied"};'
        'function run(){console.log("Running")}',
        encoding='utf-8',
    )
    (cli_dir / 'package.json').write_text(
        '{"name":"@anthropic-ai/claude-code","version":"2.1.92"}',
        encoding='utf-8',
    )
    return cli_dir


@pytest.fixture
def cjk_cli_dir(tmp_path):
    """Create a CLI dir with Chinese-polluted cli.js."""
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()
    (cli_dir / 'cli.js').write_text(
        'var e={title:"Claude \u4ee3\u7801",msg:"\u6743\u9650\u88ab\u62d2\u7edd"};',
        encoding='utf-8',
    )
    (cli_dir / 'package.json').write_text(
        '{"name":"@anthropic-ai/claude-code","version":"2.1.92"}',
        encoding='utf-8',
    )
    return cli_dir


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file (helper for test assertions)."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


class TestCreatePristineBackup:
    """BAK-01: First apply creates backup from pristine cli.js."""

    def test_create_pristine_backup(self, pristine_cli_dir):
        """From pristine cli.js, ensure_backup creates backup with matching content."""
        mgr = BackupManager(pristine_cli_dir)
        result = mgr.ensure_backup()

        assert result['ok'] is True
        assert result['action'] == 'created'

        backup = pristine_cli_dir / BACKUP_NAME
        assert backup.exists()
        assert backup.read_text(encoding='utf-8') == (
            pristine_cli_dir / 'cli.js'
        ).read_text(encoding='utf-8')

    def test_existing_valid_backup(self, pristine_cli_dir):
        """Already valid backup + hash file returns existing_valid."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()  # Create first

        result = mgr.ensure_backup()  # Second call
        assert result['ok'] is True
        assert result['action'] == 'existing_valid'

    def test_polluted_backup_renamed(self, pristine_cli_dir):
        """Existing CJK-polluted backup is renamed to .polluted.js."""
        backup = pristine_cli_dir / BACKUP_NAME
        backup.write_text(
            'var polluted = "\u6c61\u67d3\u7684\u5185\u5bb9";',
            encoding='utf-8',
        )

        mgr = BackupManager(pristine_cli_dir)
        result = mgr.ensure_backup()

        assert result['ok'] is True
        assert result['action'] == 'created'

        # Old polluted backup should be renamed
        polluted = pristine_cli_dir / 'cli.bak.polluted.js'
        assert polluted.exists()
        assert '\u6c61\u67d3' in polluted.read_text(encoding='utf-8')

        # New backup should be clean
        new_backup = pristine_cli_dir / BACKUP_NAME
        assert '\u6c61\u67d3' not in new_backup.read_text(encoding='utf-8')


class TestSha256Hash:
    """BAK-02: SHA-256 hash computation and storage."""

    def test_sha256_hash_created(self, pristine_cli_dir):
        """Backup creation stores SHA-256 hash in hash file."""
        mgr = BackupManager(pristine_cli_dir)
        result = mgr.ensure_backup()

        hash_file = pristine_cli_dir / HASH_NAME
        assert hash_file.exists()

        stored_hash = hash_file.read_text(encoding='utf-8').strip()
        assert len(stored_hash) == 64  # SHA-256 hex digest

        # Verify it matches actual file hash
        backup = pristine_cli_dir / BACKUP_NAME
        expected_hash = _sha256_file(backup)
        assert stored_hash == expected_hash


class TestHashVerification:
    """BAK-03: Hash verification before restore."""

    def test_hash_verification_before_restore(self, pristine_cli_dir):
        """Restore succeeds when hash matches."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()

        result = mgr.restore()
        assert result['ok'] is True
        assert result['action'] == 'restored'

    def test_hash_mismatch_triggers_error(self, pristine_cli_dir):
        """Tampered hash file causes restore to return hash_mismatch error."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()

        # Tamper with hash file
        hash_file = pristine_cli_dir / HASH_NAME
        hash_file.write_text('0' * 64, encoding='utf-8')

        result = mgr.restore()
        assert result['ok'] is False
        assert result['error'] == 'hash_mismatch'


class TestCjkPurityCheck:
    """BAK-04: CJK character purity check."""

    def test_cjk_purity_check_reject(self, cjk_cli_dir):
        """cli.js with Chinese characters returns source_not_pristine error."""
        mgr = BackupManager(cjk_cli_dir)
        result = mgr.ensure_backup()

        assert result['ok'] is False
        assert result['error'] == 'source_not_pristine'

    def test_cjk_purity_check_accept(self, pristine_cli_dir):
        """cli.js without CJK characters passes purity check."""
        mgr = BackupManager(pristine_cli_dir)
        result = mgr.ensure_backup()

        assert result['ok'] is True
        assert 'error' not in result


class TestReadonlyProtection:
    """BAK-06: Backup file set read-only after creation."""

    def test_readonly_protection(self, pristine_cli_dir):
        """Backup file is chmod 444 after creation."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()

        backup = pristine_cli_dir / BACKUP_NAME
        mode = backup.stat().st_mode
        # Check write bits are all off
        assert not (mode & stat.S_IWUSR)
        assert not (mode & stat.S_IWGRP)
        assert not (mode & stat.S_IWOTH)

        # Attempting to write should raise PermissionError
        with pytest.raises(PermissionError):
            open(backup, 'w')

    def test_make_writable_restores_permission(self, pristine_cli_dir):
        """_make_writable restores write permission."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()

        backup = pristine_cli_dir / BACKUP_NAME
        assert not (backup.stat().st_mode & stat.S_IWUSR)

        mgr._make_writable(backup)
        assert backup.stat().st_mode & stat.S_IWUSR


class TestRestore:
    """BAK-07: Restore returns cli.js to pure English."""

    def test_restore_purity(self, pristine_cli_dir):
        """After adding Chinese to cli.js, restore produces zero CJK content."""
        mgr = BackupManager(pristine_cli_dir)
        mgr.ensure_backup()

        # "Localize" cli.js by adding Chinese
        cli_js = pristine_cli_dir / 'cli.js'
        cli_js.write_text(
            'var e={title:"Claude \u4ee3\u7801"};'
            'console.log("\u4f60\u597d\u4e16\u754c");',
            encoding='utf-8',
        )

        result = mgr.restore()
        assert result['ok'] is True

        # cli.js should have zero CJK characters
        content = cli_js.read_text(encoding='utf-8')
        import re
        cjk = re.compile(r'[\u4e00-\u9fff]')
        assert not cjk.search(content), 'cli.js still contains CJK after restore'

    def test_restore_no_backup_error(self, pristine_cli_dir):
        """Restore without backup returns no_backup error."""
        mgr = BackupManager(pristine_cli_dir)
        result = mgr.restore()

        assert result['ok'] is False
        assert result['error'] == 'no_backup'
