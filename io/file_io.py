"""Atomic file write utilities for Claude Code i18n engine.

Provides atomic write and copy operations that guarantee no corrupted
files are left behind if the process crashes or is interrupted.

Key design decisions:
- Temp files created in target.parent (same filesystem guarantee)
- tempfile.mkstemp() for low-level control
- os.replace() for cross-platform atomic rename
- BaseException handling to clean up even on KeyboardInterrupt
"""

import os
import shutil
import tempfile
from pathlib import Path


def atomic_write_text(
    target: Path,
    content: str,
    encoding: str = 'utf-8',
) -> None:
    """Write text content to file atomically.

    Writes to a temporary file first, then atomically replaces the target.
    If the process crashes during write, the target remains unchanged.

    Args:
        target: Path to the target file.
        content: Text content to write.
        encoding: Text encoding (default utf-8).
    """
    fd, tmp_path = tempfile.mkstemp(
        dir=target.parent,
        prefix='.tmp_',
        suffix=target.suffix,
    )
    tmp = Path(tmp_path)
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        os.replace(str(tmp), str(target))
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def atomic_copy(src: Path, dst: Path) -> None:
    """Copy file atomically.

    Copies to a temporary file first, then atomically replaces the target.
    Preserves metadata via shutil.copy2.

    Args:
        src: Source file path.
        dst: Destination file path.
    """
    fd, tmp_path = tempfile.mkstemp(
        dir=dst.parent,
        prefix='.tmp_',
        suffix=dst.suffix,
    )
    tmp = Path(tmp_path)
    try:
        os.close(fd)
        shutil.copy2(src, tmp)
        os.replace(str(tmp), str(dst))
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
