"""Unit tests for Claude Code CLI path resolution.

Covers requirements PATH-01 through PATH-05:
- PATH-01: shutil.which + volta which + Path.resolve() cascading detection
- PATH-02: CLAUDE_I18N_CLI_DIR environment variable override
- PATH-03: ~/.claude/i18n.json config file override
- PATH-04: validate_cli_dir checks cli.js + package.json + name
- PATH-05: (None, 'not_found') return when CLI not found
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.i18n.config.paths import find_cli_install_dir, validate_cli_dir


class TestEnvVarOverride:
    """PATH-02: Environment variable override."""

    def test_env_var_override(self, mock_cli_dir, clean_env):
        """When CLAUDE_I18N_CLI_DIR points to a valid dir, return (path, 'env_var')."""
        os.environ['CLAUDE_I18N_CLI_DIR'] = str(mock_cli_dir)
        result_path, method = find_cli_install_dir()
        assert result_path == mock_cli_dir
        assert method == 'env_var'


class TestConfigFileOverride:
    """PATH-03: Config file override."""

    def test_config_file_override(self, mock_cli_dir, tmp_path, clean_env):
        """When ~/.claude/i18n.json has cli_path, return (path, 'config_file')."""
        config_dir = tmp_path / '.claude'
        config_dir.mkdir()
        config_file = config_dir / 'i18n.json'
        config_file.write_text(
            json.dumps({'cli_path': str(mock_cli_dir)}),
            encoding='utf-8'
        )

        with patch.object(Path, 'home', return_value=tmp_path):
            result_path, method = find_cli_install_dir()

        assert result_path == mock_cli_dir
        assert method == 'config_file'


class TestVoltaDetection:
    """PATH-01: Volta path detection."""

    def test_volta_detection(self, mock_cli_dir, clean_env):
        """When volta is available and 'volta which claude' succeeds, detect via volta."""
        cli_js = mock_cli_dir / 'cli.js'

        def mock_which(name):
            if name == 'volta':
                return '/usr/local/bin/volta'
            return None

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if cmd == ['volta', 'which', 'claude']:
                result.returncode = 0
                result.stdout = str(cli_js) + '\n'
                result.stderr = ''
            else:
                result.returncode = 1
                result.stdout = ''
                result.stderr = ''
            return result

        with patch('shutil.which', side_effect=mock_which), \
             patch('subprocess.run', side_effect=mock_run):
            result_path, method = find_cli_install_dir()

        assert result_path == mock_cli_dir
        assert method == 'volta'


class TestNpmGlobalDetection:
    """PATH-01: npm global path detection."""

    def test_npm_global_detection(self, mock_cli_dir, tmp_path, clean_env):
        """When npm root -g points to a parent containing the package, detect via npm_global."""
        # Create the npm global structure
        node_modules = tmp_path / 'node_modules'
        pkg_dir = node_modules / '@anthropic-ai' / 'claude-code'
        pkg_dir.mkdir(parents=True)

        import shutil
        shutil.copy2(mock_cli_dir / 'cli.js', pkg_dir / 'cli.js')
        shutil.copy2(mock_cli_dir / 'package.json', pkg_dir / 'package.json')

        def mock_which(name):
            return None  # No volta

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if cmd == ['npm', 'root', '-g']:
                result.returncode = 0
                result.stdout = str(node_modules) + '\n'
                result.stderr = ''
            else:
                result.returncode = 1
                result.stdout = ''
                result.stderr = ''
            return result

        with patch('shutil.which', side_effect=mock_which), \
             patch('subprocess.run', side_effect=mock_run):
            result_path, method = find_cli_install_dir()

        assert result_path == pkg_dir
        assert method == 'npm_global'


class TestCommonPathFallback:
    """PATH-01: Common hardcoded path fallback."""

    def test_common_path_fallback(self, mock_cli_dir, clean_env):
        """When all other strategies fail, check common paths."""
        home = mock_cli_dir.parent
        pkg_name = '@anthropic-ai/claude-code'
        expected_path = home / '.volta' / 'tools' / 'image' / 'packages' / pkg_name / 'lib' / 'node_modules' / pkg_name
        expected_path.mkdir(parents=True)

        import shutil
        shutil.copy2(mock_cli_dir / 'cli.js', expected_path / 'cli.js')
        shutil.copy2(mock_cli_dir / 'package.json', expected_path / 'package.json')

        def mock_which(name):
            return None

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stdout = ''
            result.stderr = ''
            return result

        with patch('shutil.which', side_effect=mock_which), \
             patch('subprocess.run', side_effect=mock_run), \
             patch.object(Path, 'home', return_value=home):
            result_path, method = find_cli_install_dir()

        assert result_path == expected_path
        assert method == 'common_path'


class TestNotFound:
    """PATH-05: CLI not found."""

    def test_not_found_error(self, tmp_path, clean_env):
        """When all strategies fail, return (None, 'not_found')."""
        def mock_which(name):
            return None

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stdout = ''
            result.stderr = ''
            return result

        with patch('shutil.which', side_effect=mock_which), \
             patch('subprocess.run', side_effect=mock_run), \
             patch.object(Path, 'home', return_value=tmp_path):
            result_path, method = find_cli_install_dir()

        assert result_path is None
        assert method == 'not_found'


class TestValidateCliDir:
    """PATH-04: Path validation."""

    def test_validate_cli_dir_valid(self, mock_cli_dir):
        """Valid directory with cli.js + package.json + correct name returns True."""
        assert validate_cli_dir(mock_cli_dir) is True

    def test_validate_cli_dir_missing_cli_js(self, mock_cli_dir):
        """Directory missing cli.js returns False."""
        (mock_cli_dir / 'cli.js').unlink()
        assert validate_cli_dir(mock_cli_dir) is False

    def test_validate_cli_dir_missing_package_json(self, mock_cli_dir):
        """Directory missing package.json returns False."""
        (mock_cli_dir / 'package.json').unlink()
        assert validate_cli_dir(mock_cli_dir) is False

    def test_validate_cli_dir_wrong_package_name(self, mock_cli_dir):
        """package.json with wrong name returns False."""
        pkg_json = mock_cli_dir / 'package.json'
        pkg_json.write_text('{"name": "wrong-package", "version": "1.0.0"}', encoding='utf-8')
        assert validate_cli_dir(mock_cli_dir) is False

    def test_validate_cli_dir_not_a_directory(self, tmp_path):
        """A file path (not directory) returns False."""
        a_file = tmp_path / 'not_a_dir'
        a_file.write_text('hello', encoding='utf-8')
        assert validate_cli_dir(a_file) is False

    def test_validate_cli_dir_with_cjk_cli(self, mock_cli_dir):
        """cli.js containing CJK characters still validates True.

        Validation only checks structure and package name, not content purity.
        """
        (mock_cli_dir / 'cli.js').write_text(
            'var e={title:"Claude Code",msg:"\u6743\u9650\u88ab\u62d2\u7edd"};',
            encoding='utf-8'
        )
        assert validate_cli_dir(mock_cli_dir) is True
