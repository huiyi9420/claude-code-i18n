"""Tests for atomic file write utilities (BAK-05)."""

import os
from pathlib import Path
from unittest.mock import patch

from scripts.i18n.io.file_io import atomic_write_text, atomic_copy


class TestAtomicWriteText:
    """Tests for atomic_write_text function."""

    def test_atomic_write_text_creates_file(self, tmp_path):
        """Calling atomic_write_text(target, 'hello') creates file with content 'hello'."""
        target = tmp_path / 'output.txt'
        atomic_write_text(target, 'hello')
        assert target.exists()
        assert target.read_text(encoding='utf-8') == 'hello'

    def test_atomic_write_text_replaces_existing(self, tmp_path):
        """Writing to existing file atomically replaces content."""
        target = tmp_path / 'output.txt'
        target.write_text('old', encoding='utf-8')
        atomic_write_text(target, 'new')
        assert target.read_text(encoding='utf-8') == 'new'

    def test_atomic_write_text_atomic_on_crash(self, tmp_path):
        """Simulate crash during write -- original file unchanged."""
        target = tmp_path / 'output.txt'
        target.write_text('original', encoding='utf-8')

        with patch('os.replace', side_effect=OSError('simulated crash')):
            try:
                atomic_write_text(target, 'new content')
            except OSError:
                pass

        # Original file must be unchanged
        assert target.read_text(encoding='utf-8') == 'original'

    def test_atomic_write_text_cleanup_on_error(self, tmp_path):
        """On write failure, temp files are cleaned up (no .tmp_ prefix files)."""
        target = tmp_path / 'output.txt'
        target.write_text('original', encoding='utf-8')

        with patch('os.replace', side_effect=OSError('simulated crash')):
            try:
                atomic_write_text(target, 'new')
            except OSError:
                pass

        # No leftover temp files
        tmp_files = list(tmp_path.glob('.tmp_*'))
        assert len(tmp_files) == 0


class TestAtomicCopy:
    """Tests for atomic_copy function."""

    def test_atomic_copy_preserves_content(self, tmp_path):
        """atomic_copy(src, dst) copies content correctly."""
        src = tmp_path / 'source.txt'
        src.write_text('copy me', encoding='utf-8')
        dst = tmp_path / 'dest.txt'

        atomic_copy(src, dst)

        assert dst.exists()
        assert dst.read_text(encoding='utf-8') == 'copy me'

    def test_atomic_copy_temp_in_same_dir(self, tmp_path):
        """Temp file is created in target.parent directory (same filesystem guarantee)."""
        src = tmp_path / 'source.txt'
        src.write_text('data', encoding='utf-8')
        dst = tmp_path / 'dest.txt'

        created_paths = []

        original_mkstemp = __import__('tempfile').mkstemp

        def tracking_mkstemp(*args, **kwargs):
            result = original_mkstemp(*args, **kwargs)
            # args[0] is 'dir' when called positionally, but our code uses kwargs
            created_paths.append({
                'dir': kwargs.get('dir') or (args[0] if args else None),
                'prefix': kwargs.get('prefix', ''),
            })
            return result

        with patch('tempfile.mkstemp', side_effect=tracking_mkstemp):
            atomic_copy(src, dst)

        assert len(created_paths) == 1
        assert str(created_paths[0]['dir']) == str(dst.parent)
        assert created_paths[0]['prefix'] == '.tmp_'
