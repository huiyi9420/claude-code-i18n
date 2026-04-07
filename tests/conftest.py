"""Shared test fixtures for Claude Code i18n engine tests."""

import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def mock_cli_dir(tmp_path):
    """Create a temporary directory mimicking a valid Claude Code CLI installation.

    Copies sample_cli.js as cli.js and sample_package.json as package.json.
    Returns the directory Path.
    """
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()

    shutil.copy2(FIXTURES_DIR / 'sample_cli.js', cli_dir / 'cli.js')
    shutil.copy2(FIXTURES_DIR / 'sample_package.json', cli_dir / 'package.json')

    return cli_dir


@pytest.fixture
def mock_volta():
    """Mock subprocess.run to simulate 'volta which claude' output.

    Returns a factory function that accepts the cli_dir Path.
    Usage: mock_volta(cli_dir) activates the mock.
    """
    def _mock(cli_dir):
        cli_js = cli_dir / 'cli.js'

        def _run_side_effect(cmd, **kwargs):
            result = MagicMock()
            if cmd == ['volta', 'which', 'claude']:
                result.returncode = 0
                result.stdout = str(cli_js) + '\n'
                result.stderr = ''
            else:
                result.returncode = 1
                result.stdout = ''
                result.stderr = 'command not found'
            return result

        return patch('subprocess.run', side_effect=_run_side_effect)

    return _mock


@pytest.fixture
def mock_npm_root():
    """Mock subprocess.run to simulate 'npm root -g' output.

    Returns a factory function that accepts the parent directory Path
    (where node_modules/@anthropic-ai/claude-code should exist).
    Usage: mock_npm_root(parent_dir) activates the mock.
    """
    def _mock(parent_dir):
        def _run_side_effect(cmd, **kwargs):
            result = MagicMock()
            if cmd == ['npm', 'root', '-g']:
                result.returncode = 0
                result.stdout = str(parent_dir) + '\n'
                result.stderr = ''
            else:
                result.returncode = 1
                result.stdout = ''
                result.stderr = ''
            return result

        return patch('subprocess.run', side_effect=_run_side_effect)

    return _mock


@pytest.fixture
def clean_env():
    """Ensure CLAUDE_I18N_CLI_DIR environment variable is not set."""
    key = 'CLAUDE_I18N_CLI_DIR'
    original = os.environ.pop(key, None)
    yield
    if original is not None:
        os.environ[key] = original
    else:
        os.environ.pop(key, None)
