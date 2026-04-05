# Phase 1: Foundation & Safety - Research

**Researched:** 2026-04-05
**Domain:** Python CLI tool -- path detection, backup integrity, atomic file I/O
**Confidence:** HIGH

## Summary

Phase 1 建立 Claude Code i18n 引擎的安全基础设施：路径自动检测、不可变备份管理器、原子文件写入和 CLI 命令框架。这些组件是所有后续功能（替换引擎、提取器等）的根基。

核心发现：(1) 当前 v3.0 的备份文件 `cli.bak.en.js` 包含 12,224 个中文字符，确认备份污染是真实且严重的问题；(2) Volta 安装路径解析有特殊挑战 -- `shutil.which('claude')` 返回 Volta shim（Mach-O 二进制），必须通过 `volta which claude` 或 `bin/claude` 的 `resolve()` 才能定位到实际的 `cli.js`；(3) Python 标准库的 `os.replace()` 比 `os.rename()` 更适合跨平台原子写入，但两者在同一文件系统上行为一致；(4) `tempfile` 默认临时目录在本项目环境中与目标文件在同一文件系统上，但不应依赖此条件，应在目标目录创建临时文件以保证原子性。

**Primary recommendation:** 使用 `pathlib.Path.resolve()` + 多策略级联（env var -> config -> volta which -> npm root -> 常见路径）实现路径检测；备份管理器使用 SHA-256 分块校验 + CJK 字符扫描 + chmod 444 实现不可变保证。

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PATH-01 | Engine auto-detects CLI installation path via `which claude` symlink resolution | 多策略级联检测：shutil.which -> Path.resolve() -> volta which -> npm root。Volta 场景需要特殊处理（shim 是 Mach-O 二进制，不是 symlink 到 cli.js） |
| PATH-02 | Engine supports explicit path via environment variable `CLAUDE_I18N_CLI_DIR` | 最高优先级策略，在所有自动检测之前检查 |
| PATH-03 | Engine supports config file `~/.claude/i18n.json` with custom `cli_path` | 第二优先级，json.load() 读取 |
| PATH-04 | Engine validates detected path exists and contains `cli.js` + `package.json` | 验证函数：检查两个文件存在且 package.json 的 name 字段为 `@anthropic-ai/claude-code` |
| PATH-05 | Engine reports clear error message when CLI not found | 所有策略失败时输出错误信息，列出已尝试的路径和安装指引 |
| BAK-01 | First apply creates backup from pristine cli.js (no Chinese characters present) | shutil.copy2() + CJK 扫描验证 + SHA-256 计算 |
| BAK-02 | Backup creation computes SHA-256 hash stored in `.backup.hash` | hashlib.sha256() + 8KB 分块读取，.hash 文件存储在备份同目录 |
| BAK-03 | Every restore/apply validates backup hash before use; mismatch triggers re-extraction | 先读 .hash 文件，再计算备份文件 SHA-256，不匹配则删除旧备份重新创建 |
| BAK-04 | Backup purity check: scan for CJK characters, reject if found (>0 CJK chars) | re.findall(r'[\u4e00-\u9fff]', content)，13MB 文件扫描 <0.5 秒 |
| BAK-05 | Atomic write for all file operations (write to temp, then os.rename) | tempfile.NamedTemporaryFile(delete=False, dir=target_dir) + os.replace() |
| BAK-06 | Backup file set read-only after creation (chmod 444) | os.chmod(path, stat.S_IRUSR \| stat.S_IRGRP \| stat.S_IROTH)，已验证 macOS 上写入会触发 PermissionError |
| BAK-07 | Restore command returns cli.js to 100% pure English with zero Chinese characters | shutil.copy2(backup, cli_file) + 恢复后 CJK 扫描验证 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pathlib.Path` | Python 3.8+ | 路径操作，symlink 解析 | 面向对象路径 API，resolve() 跟随 symlink，跨平台 |
| `shutil` | Python 3.8+ | 文件复制（copy2）、which 命令查找 | copy2 保留元数据，which 定位可执行文件 |
| `hashlib` | Python 3.8+ | SHA-256 校验和 | 分块计算（8KB chunks），内存友好 |
| `os` | Python 3.8+ | 原子写入（os.replace）、chmod、环境变量 | os.replace() 原子替换文件，os.chmod() 设置只读 |
| `tempfile` | Python 3.8+ | 安全临时文件 | 在目标目录创建临时文件，保证同一文件系统 |
| `stat` | Python 3.8+ | 文件权限常量 | S_IRUSR/S_IRGRP/S_IROTH 组合为 0o444 |
| `re` | Python 3.8+ | CJK 字符扫描 | `[\u4e00-\u9fff]` 匹配 CJK 统一汉字 |
| `json` | Python 3.8+ | 配置文件读写 | json.load/dump，ensure_ascii=False |
| `argparse` | Python 3.8+ | CLI 子命令路由 | add_subparsers() 实现 apply/restore/extract/status/version |
| `subprocess` | Python 3.8+ | 调用 volta which / npm root | subprocess.run([list], capture_output=True, timeout=5) |
| `sys` | Python 3.8+ | 退出码、标准输出/错误 | sys.exit(0/1)，stdout/stderr 分离 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` | Python 3.8+ | 读取 package.json 验证包名 | 路径验证时检查 name 字段 |
| `typing` | Python 3.8+ | 类型注解（Optional, Tuple 等） | 代码可读性，Python 3.8+ 支持 typing.Optional |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `os.replace()` | `os.rename()` | rename 在 POSIX 同文件系统上原子，但 replace 在跨平台和目标已存在时更安全。**推荐 os.replace()** |
| `shutil.which()` | `subprocess.run(['which', ...])` | shutil.which 是纯 Python 实现，无子进程开销，但只能找 PATH 上的命令 |
| `tempfile` in target dir | `tempfile` in system temp | 系统 temp 在当前环境碰巧同文件系统，但不应依赖。**在目标目录创建临时文件** |

**Installation:**
```bash
# 无需安装 -- 全部 Python 标准库
# 开发测试需要:
pip install pytest
```

## Architecture Patterns

### Recommended Project Structure (Phase 1 涉及部分)
```
scripts/
├── i18n/                          # 主引擎包
│   ├── __init__.py
│   ├── cli.py                     # CLI 入口，argparse 子命令路由
│   ├── config/
│   │   ├── __init__.py
│   │   ├── paths.py               # Path Resolver -- 多策略路径检测
│   │   └── constants.py           # 常量（包名、文件名模式等）
│   ├── io/
│   │   ├── __init__.py
│   │   ├── backup.py              # Backup Manager -- 不可变备份保证
│   │   └── file_io.py             # 原子写入工具
│   └── commands/                  # 子命令骨架（Phase 1 只建立框架）
│       ├── __init__.py
│       └── restore.py             # restore 命令（Phase 1 实现）
└── localize.py                    # 向后兼容入口（重定向到 i18n/cli.py）
```

### Pattern 1: 多策略级联路径检测 (Cascading Path Resolution)

**What:** 按优先级依次尝试 5 种策略定位 cli.js，任一成功即返回。
**When:** 每次引擎需要访问 cli.js 或备份时调用。

```python
# Source: 实测验证的路径解析策略
def find_cli_install_dir() -> Tuple[Optional[Path], str]:
    """
    Returns: (package_dir, method_used) or (None, 'not_found')
    
    Priority:
    1. CLAUDE_I18N_CLI_DIR env var
    2. ~/.claude/i18n.json config file
    3. Volta: 'volta which claude' -> bin/claude -> resolve() -> cli.js
    4. npm global: npm root -g -> node_modules/@anthropic-ai/claude-code/
    5. Common hardcoded paths (fallback)
    """
    pkg_name = '@anthropic-ai/claude-code'
    home = Path.home()

    # Strategy 1: Environment variable
    env_dir = os.environ.get('CLAUDE_I18N_CLI_DIR')
    if env_dir:
        p = Path(env_dir)
        if _validate_cli_dir(p):
            return p, 'env_var'

    # Strategy 2: Config file
    config_path = home / '.claude' / 'i18n.json'
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding='utf-8'))
        custom = config.get('cli_path')
        if custom and _validate_cli_dir(Path(custom)):
            return Path(custom), 'config_file'

    # Strategy 3: Volta
    volta = shutil.which('volta')
    if volta:
        r = subprocess.run(['volta', 'which', 'claude'],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            # bin/claude is symlink to lib/.../cli.js
            resolved = Path(r.stdout.strip()).resolve()
            if resolved.name == 'cli.js' and _validate_cli_dir(resolved.parent):
                return resolved.parent, 'volta'

    # Strategy 4: npm global
    r = subprocess.run(['npm', 'root', '-g'],
                       capture_output=True, text=True, timeout=5)
    if r.returncode == 0:
        npm_root = Path(r.stdout.strip())
        cli_dir = npm_root / pkg_name
        if _validate_cli_dir(cli_dir):
            return cli_dir, 'npm_global'

    # Strategy 5: Common paths
    common = [
        home / f'.volta/tools/image/packages/{pkg_name}/lib/node_modules/{pkg_name}',
        Path('/usr/local/lib/node_modules') / pkg_name,
        Path('/opt/homebrew/lib/node_modules') / pkg_name,
    ]
    for p in common:
        if _validate_cli_dir(p):
            return p, 'common_path'

    return None, 'not_found'

def _validate_cli_dir(p: Path) -> bool:
    """Verify directory contains valid Claude Code installation."""
    if not p.is_dir():
        return False
    cli_js = p / 'cli.js'
    pkg_json = p / 'package.json'
    if not cli_js.exists() or not pkg_json.exists():
        return False
    try:
        meta = json.loads(pkg_json.read_text(encoding='utf-8'))
        return meta.get('name') == '@anthropic-ai/claude-code'
    except (json.JSONDecodeError, OSError):
        return False
```

### Pattern 2: 不可变备份管理器 (Immutable Backup Manager)

**What:** 备份文件创建后设为只读，每次使用前验证 SHA-256 和 CJK 纯净性。
**When:** apply 和 restore 操作之前。

```python
# Source: PITFALLS.md Pattern 2 + 实测验证
import hashlib
import stat
from pathlib import Path

BACKUP_SUFFIX = '.bak.en.js'
HASH_SUFFIX = '.backup.hash'

def create_pristine_backup(cli_js: Path, backup: Path) -> dict:
    """Create an immutable, verified backup from pristine cli.js."""
    hash_file = backup.with_suffix(HASH_SUFFIX)

    # If backup already exists and is valid, skip
    if backup.exists() and hash_file.exists():
        if _verify_backup_integrity(backup, hash_file):
            return {"ok": True, "action": "existing_backup_valid"}

    # If backup exists but is polluted, rename it
    if backup.exists():
        if not _is_pristine(backup):
            polluted = backup.with_suffix('.polluted.js')
            _make_writable(backup)
            backup.rename(polluted)

    # Create new backup
    shutil.copy2(cli_js, backup)

    # Purity check
    if not _is_pristine(backup):
        backup.unlink()
        return {"ok": False, "error": "Source cli.js contains CJK characters"}

    # Compute SHA-256
    checksum = _sha256_file(backup)
    hash_file.write_text(checksum, encoding='utf-8')

    # Set read-only (chmod 444)
    os.chmod(backup, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    return {"ok": True, "action": "created", "sha256": checksum}

def _sha256_file(path: Path) -> str:
    """Compute SHA-256 checksum using 8KB chunks."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def _is_pristine(path: Path) -> bool:
    """Check file contains zero CJK characters."""
    # Read in chunks to avoid loading entire 13MB into memory for scanning
    pattern = re.compile(r'[\u4e00-\u9fff]')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if pattern.search(line):
                return False
    return True

def _verify_backup_integrity(backup: Path, hash_file: Path) -> bool:
    """Verify backup SHA-256 matches stored hash."""
    if not hash_file.exists():
        return False
    expected = hash_file.read_text(encoding='utf-8').strip()
    actual = _sha256_file(backup)
    return expected == actual

def _make_writable(path: Path) -> None:
    """Restore write permission for file operations."""
    current = path.stat().st_mode
    os.chmod(path, current | stat.S_IWUSR)
```

### Pattern 3: 原子文件写入 (Atomic File Write)

**What:** 先写入临时文件，验证通过后原子替换目标文件。
**When:** 所有修改 cli.js 的操作。

```python
# Source: WebSearch 验证的最佳实践
import tempfile
import os
from pathlib import Path

def atomic_write(target: Path, content: str) -> None:
    """
    Write content to target file atomically.
    
    Key points:
    - Create temp file in SAME DIRECTORY as target (guarantees same filesystem)
    - os.replace() is atomic on POSIX when same filesystem
    - If process crashes during write, target remains unchanged
    """
    # MUST create temp file in target directory for same-filesystem guarantee
    fd, tmp_path = tempfile.mkstemp(
        dir=target.parent,
        prefix='.tmp_',
        suffix='.js'
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, target)  # Atomic on POSIX same-filesystem
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

**重要细节：**
- 使用 `tempfile.mkstemp()` 而非 `NamedTemporaryFile(delete=False)`，因为 mkstemp 直接返回文件描述符，更底层更可控
- `dir=target.parent` 确保临时文件与目标文件在同一文件系统，这是 `os.replace()` 原子性的前提
- `os.replace()` 优于 `os.rename()`：在 POSIX 上行为相同，但在跨平台场景更安全（总是替换目标）
- 前缀 `.tmp_` 使临时文件成为隐藏文件（减少用户困惑）

### Pattern 4: argparse CLI 框架

**What:** 使用 argparse 的 subparsers 实现子命令路由。
**When:** CLI 入口点。

```python
# Source: Python 官方文档 + STACK.md
import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='engine',
        description='Claude Code i18n Engine'
    )
    sub = parser.add_subparsers(dest='command', help='Available commands')

    # Phase 1 commands
    sub.add_parser('status', help='Show current i18n status')
    sub.add_parser('restore', help='Restore original English CLI')
    sub.add_parser('version', help='Show CLI version')

    # Phase 2 commands (skeleton only in Phase 1)
    sub.add_parser('apply', help='Apply Chinese localization')
    sub.add_parser('extract', help='Extract translatable strings')

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    COMMANDS = {
        'status': cmd_status,
        'restore': cmd_restore,
        'version': cmd_version,
        # Phase 2:
        'apply': cmd_apply,
        'extract': cmd_extract,
    }
    COMMANDS[args.command]()
```

### Anti-Patterns to Avoid

- **Anti-Pattern: 在系统临时目录创建临时文件后 os.replace() 到不同文件系统** -- 如果 /tmp 和目标文件在不同文件系统（如 NFS 挂载），os.replace() 会失败或非原子。始终在目标目录创建临时文件。
- **Anti-Pattern: 备份文件创建后不设为只读** -- 任何后续代码的 bug 都可能意外写入备份文件。chmod 444 是最后一道防线。
- **Anti-Pattern: 只检查 SHA-256 不检查 CJK 纯净性** -- SHA-256 只能验证文件未被动过，但不能证明文件是"纯英文"的。如果备份创建时 cli.js 已被汉化，SHA-256 会是一个"被污染的基准"。必须同时做 CJK 扫描。
- **Anti-Pattern: 用 shutil.which('claude').resolve() 直接定位 cli.js** -- 在 Volta 安装场景下，which 返回的是 Mach-O 二进制 shim（不是 symlink 到 cli.js），resolve() 只能得到 volta-shim 路径。必须通过 `volta which claude` 获取实际路径。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 文件校验和 | 自己写的哈希循环 | `hashlib.sha256()` + 8KB 分块 | 标准库实现优化过，分块避免内存问题 |
| 临时文件创建 | 手动构造随机文件名 | `tempfile.mkstemp()` | 安全的文件名生成，避免竞态条件 |
| 原子文件替换 | 先删除再写入 | `os.replace()` | POSIX 保证原子性，先删再写有窗口期风险 |
| 可执行文件查找 | 遍历 PATH 环境变量 | `shutil.which()` | 标准库实现，处理 PATH、权限、扩展名 |
| 文件复制 | 手动读写 | `shutil.copy2()` | 保留元数据（mtime、权限），处理特殊文件 |

**Key insight:** Python 标准库在文件 I/O 和路径操作方面已经非常成熟。本项目零外部依赖的策略在 Phase 1 完全可行。

## Common Pitfalls

### Pitfall 1: Volta Shim 误判 (PATH-01 关键)

**What goes wrong:** `shutil.which('claude')` 返回 `/Users/xxx/.volta/bin/claude`，开发者误以为这就是 cli.js 所在目录的入口。实际上它是 Volta 的 Mach-O 二进制 shim，与 cli.js 无关。
**Why it happens:** Volta 通过 shim 二进制管理 Node 包执行，shim 不是 symlink 而是 native binary。
**How to avoid:** 检测到 Volta 可用时，使用 `volta which claude` 获取实际路径；对该路径调用 `Path.resolve()` 可以得到真正的 cli.js 文件。
**Warning signs:** `which('claude')` 返回的路径的 `resolve()` 结果不是 `.js` 文件。

### Pitfall 2: 备份创建时源文件已污染 (BAK-01 关键)

**What goes wrong:** 用户先运行了旧版 v3.0 的 apply（污染了 cli.js），然后升级到新版引擎。新引擎的首次 apply 会从"已汉化的 cli.js"创建备份，备份从一开始就是脏的。
**Why it happens:** 当前 cli.js 包含 12,224 个中文字符，且旧备份 `cli.bak.en.js` 也包含同样多的中文字符。任何基于当前文件的备份创建都会继承污染。
**How to avoid:** (1) 创建备份时必须做 CJK 扫描，发现中文字符则拒绝创建；(2) 提示用户重新安装 Claude Code 以获取纯净文件；(3) 不依赖已存在的备份，总是验证其纯净性。
**Warning signs:** `_is_pristine()` 返回 False 时，不应继续操作。

### Pitfall 3: 临时文件跨文件系统 (BAK-05 关键)

**What goes wrong:** 在 `/tmp`（或 `/var/folders/...`）创建临时文件，然后 `os.replace()` 到目标目录。如果两者在不同文件系统上，`os.replace()` 可能非原子甚至失败。
**Why it happens:** 在当前开发环境碰巧在同一文件系统（都是 APFS），但在其他环境（NFS、外挂磁盘、Docker volume）可能不同。
**How to avoid:** 始终在目标文件所在目录创建临时文件：`tempfile.mkstemp(dir=target.parent)`。
**Warning signs:** `os.replace()` 抛出 `OSError: Invalid cross-device link`。

### Pitfall 4: chmod 444 后无法更新/删除备份 (BAK-06)

**What goes wrong:** 备份文件设为只读后，后续需要删除（如版本更新）或替换（如重新创建）时被 PermissionError 阻止。
**Why it happens:** chmod 444 移除了写权限，包括所有者的写权限。
**How to avoid:** 在需要修改/删除只读备份前，先调用 `_make_writable(path)` 恢复写权限：`os.chmod(path, current_mode | stat.S_IWUSR)`。
**Warning signs:** `PermissionError` 在尝试操作只读备份时。

### Pitfall 5: os.rename vs os.replace 语义差异

**What goes wrong:** 在 POSIX 上两者行为相同（原子替换目标），但在 Windows 上 `os.rename()` 不会替换已存在的目标文件（会抛异常）。
**Why it happens:** Python 文档明确指出这个跨平台差异。
**How to avoid:** 统一使用 `os.replace()`，它在所有平台都原子替换目标文件。本项目声明兼容 macOS 和 Linux（无 Windows），但代码层面使用 `os.replace()` 是更好的实践。
**Warning signs:** 无直接警告，但 `os.replace()` 是更安全的选择。

### Pitfall 6: SHA-256 分块读取边界

**What goes wrong:** 使用过大的分块（如 1MB）不会造成功能问题但浪费内存；使用过小的分块（如 1 字节）性能极差。
**Why it happens:** 不了解哈希分块更新的最优大小。
**How to avoid:** 使用 8KB（8192 字节）分块。这是 Python io 模块默认缓冲区大小的合理默认值，在性能和内存之间取得平衡。13MB 文件约 1600 次迭代，<0.5 秒完成。

### Pitfall 7: argparse subparsers 的 required 参数

**What goes wrong:** Python 3.3+ 中 `add_subparsers()` 默认 `required=False`，这意味着不提供子命令时不会报错，而是 `args.command` 为 None。
**Why it happens:** Python 文档变更导致的行为差异。
**How to avoid:** 显式设置 `subparsers.required = True`（Python 3.7+），或在 main() 中手动检查 `args.command is None`。

## Code Examples

### 完整路径解析器 (paths.py 骨架)

```python
# Source: 实测验证的路径解析策略
"""Path Resolver for Claude Code CLI installation."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

PKG_NAME = '@anthropic-ai/claude-code'

def find_cli_install_dir() -> Tuple[Optional[Path], str]:
    """Find Claude Code CLI installation directory.
    
    Returns (package_dir, method) or (None, 'not_found').
    """
    home = Path.home()

    # Priority 1: Environment variable
    env_dir = os.environ.get('CLAUDE_I18N_CLI_DIR')
    if env_dir:
        p = Path(env_dir)
        if validate_cli_dir(p):
            return p, 'env_var'

    # Priority 2: Config file
    config_path = home / '.claude' / 'i18n.json'
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            custom = config.get('cli_path')
            if custom and validate_cli_dir(Path(custom)):
                return Path(custom), 'config_file'
        except (json.JSONDecodeError, OSError):
            pass

    # Priority 3: Volta
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

    # Priority 4: npm global
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

    # Priority 5: Common paths
    common_paths = [
        home / f'.volta/tools/image/packages/{PKG_NAME}/lib/node_modules/{PKG_NAME}',
        Path('/usr/local/lib/node_modules') / PKG_NAME,
        Path('/opt/homebrew/lib/node_modules') / PKG_NAME,
    ]
    for p in common_paths:
        if validate_cli_dir(p):
            return p, 'common_path'

    return None, 'not_found'

def validate_cli_dir(p: Path) -> bool:
    """Verify directory is a valid Claude Code installation."""
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
```

### 完整备份管理器 (backup.py 骨架)

```python
# Source: PITFALLS.md + 实测验证
"""Immutable Backup Manager for Claude Code CLI."""

import hashlib
import os
import re
import shutil
import stat
from pathlib import Path
from typing import Optional

BACKUP_NAME = 'cli.bak.en.js'
HASH_NAME = 'cli.backup.hash'
CJK_PATTERN = re.compile(r'[\u4e00-\u9fff]')

class BackupManager:
    def __init__(self, cli_dir: Path):
        self.cli_dir = cli_dir
        self.cli_js = cli_dir / 'cli.js'
        self.backup = cli_dir / BACKUP_NAME
        self.hash_file = cli_dir / HASH_NAME

    def ensure_backup(self) -> dict:
        """Create or validate pristine backup. Returns status dict."""
        # If valid backup exists, done
        if self.backup.exists() and self.hash_file.exists():
            if self._verify_integrity():
                if self._is_pristine():
                    return {"ok": True, "action": "existing_valid"}
                else:
                    # Hash matches but contains CJK -- poisoned baseline
                    return {"ok": False, "error": "backup_poisoned",
                            "hint": "Reinstall Claude Code to get pristine files"}

        # If backup exists but no hash (old format), validate
        if self.backup.exists():
            if self._is_pristine():
                # Old backup is clean -- add hash file
                checksum = self._sha256()
                self.hash_file.write_text(checksum, encoding='utf-8')
                os.chmod(self.backup, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                return {"ok": True, "action": "migrated_old_backup"}
            else:
                # Polluted backup -- rename and recreate
                polluted = self.backup.with_suffix('.polluted.js')
                self._make_writable(self.backup)
                self.backup.rename(polluted)

        # Create new backup from current cli.js
        if not self.cli_js.exists():
            return {"ok": False, "error": "cli_js_not_found"}

        # Verify source is pristine
        if not self._is_pristine_file(self.cli_js):
            return {"ok": False, "error": "source_not_pristine",
                    "hint": "Reinstall Claude Code, then run engine"}

        shutil.copy2(self.cli_js, self.backup)
        checksum = self._sha256()
        self.hash_file.write_text(checksum, encoding='utf-8')
        os.chmod(self.backup, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        return {"ok": True, "action": "created", "sha256": checksum}

    def restore(self) -> dict:
        """Restore cli.js from pristine backup."""
        if not self.backup.exists():
            return {"ok": False, "error": "no_backup"}

        if not self._verify_integrity():
            return {"ok": False, "error": "hash_mismatch",
                    "hint": "Backup corrupted, will re-create on next apply"}

        if not self._is_pristine():
            return {"ok": False, "error": "backup_poisoned"}

        shutil.copy2(self.backup, self.cli_js)
        return {"ok": True, "action": "restored"}

    def _sha256(self) -> str:
        h = hashlib.sha256()
        with open(self.backup, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def _is_pristine(self) -> bool:
        return self._is_pristine_file(self.backup)

    def _is_pristine_file(self, path: Path) -> bool:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if CJK_PATTERN.search(line):
                    return False
        return True

    def _verify_integrity(self) -> bool:
        if not self.hash_file.exists():
            return False
        expected = self.hash_file.read_text(encoding='utf-8').strip()
        return expected == self._sha256()

    def _make_writable(self, path: Path) -> None:
        os.chmod(path, path.stat().st_mode | stat.S_IWUSR)
```

### 原子写入工具 (file_io.py)

```python
# Source: WebSearch 验证的最佳实践
"""Atomic file write utilities."""

import os
import tempfile
from pathlib import Path

def atomic_write_text(target: Path, content: str,
                      encoding: str = 'utf-8') -> None:
    """Write text content to file atomically via temp + replace."""
    fd, tmp_path = tempfile.mkstemp(
        dir=target.parent,
        prefix='.tmp_',
        suffix=target.suffix
    )
    tmp = Path(tmp_path)
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        os.replace(str(tmp), str(target))  # Atomic on POSIX same-fs
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise

def atomic_copy(src: Path, dst: Path) -> None:
    """Copy file atomically via temp + replace."""
    fd, tmp_path = tempfile.mkstemp(
        dir=dst.parent,
        prefix='.tmp_',
        suffix=dst.suffix
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
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.rename()` | `os.replace()` (Python 3.3+) | Python 3.3 | 更安全的跨平台原子替换 |
| 硬编码路径 (v3.0) | 多策略级联检测 | Phase 1 重写 | 支持所有安装方式 |
| 无备份验证 (v3.0) | SHA-256 + CJK 双重验证 | Phase 1 重写 | 根除备份污染 |
| 直接写入 (v3.0) | 原子写入 (tempfile + replace) | Phase 1 重写 | 防止崩溃时文件损坏 |
| 无备份保护 (v3.0) | chmod 444 只读保护 | Phase 1 重写 | 防止意外修改 |

**Deprecated/outdated:**
- `os.rename()` 在跨平台场景已被 `os.replace()` 取代（虽然本项目只支持 POSIX）
- `tempfile.NamedTemporaryFile(delete=False)` 模式已被 `mkstemp()` 模式补充（后者更底层可控）
- Python 3.6 已 EOL，本项目最低支持 3.8（walrus operator、positional-only params 可用）

## Open Questions

1. **备份污染后的自动恢复路径**
   - What we know: 当前 cli.js 和 cli.bak.en.js 都包含 12,224 个 CJK 字符
   - What's unclear: 是否可以自动触发 `npm install -g @anthropic-ai/claude-code` 重新安装，还是只提示用户手动操作
   - Recommendation: Phase 1 只提示用户手动重装，不自动执行 npm install（安全考虑）

2. **多用户/权限场景下的 chmod 444**
   - What we know: macOS 上 chmod 444 正确阻止写入（已验证）
   - What's unclear: 在某些 Linux 发行版上，root 用户是否可以绕过 444 写入
   - Recommendation: 不特殊处理 root 场景，chmod 444 对普通用户足够

3. **Volta 以外的包管理器路径差异**
   - What we know: Volta 路径结构已验证，npm global 路径已验证
   - What's unclear: fnm 和 nvm 的具体路径模式（当前环境未安装）
   - Recommendation: 对 fnm/nvm 使用 common_path 策略枚举常见路径，后续按需补充

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.8+ | 主引擎 | True | 3.14.3 | -- |
| Node.js | 语法验证 (Phase 2) | True | 22.22.0 | -- |
| Volta | 路径检测策略 3 | True | volta-shim | 策略 4/5 降级 |
| npm | 路径检测策略 4 | True | 10.9.4 | 策略 5 降级 |
| pytest | 测试框架 | False | -- | 需要安装 (pip install pytest) |

**Missing dependencies with no fallback:**
- pytest: 需要安装，Phase 1 测试必需

**Missing dependencies with fallback:**
- Volta/npm: 路径检测有 5 级降级策略，任一成功即可

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (需安装) |
| Config file | 无 -- Phase 1 建立 |
| Quick run command | `pytest tests/unit/test_paths.py tests/unit/test_backup.py -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PATH-01 | Volta 路径自动检测 | unit | `pytest tests/unit/test_paths.py::test_volta_detection -x` | False -- Wave 0 |
| PATH-02 | 环境变量覆盖 | unit | `pytest tests/unit/test_paths.py::test_env_var_override -x` | False -- Wave 0 |
| PATH-03 | 配置文件覆盖 | unit | `pytest tests/unit/test_paths.py::test_config_file_override -x` | False -- Wave 0 |
| PATH-04 | 路径验证 (cli.js + package.json) | unit | `pytest tests/unit/test_paths.py::test_validate_cli_dir -x` | False -- Wave 0 |
| PATH-05 | 未找到时清晰错误信息 | unit | `pytest tests/unit/test_paths.py::test_not_found_error -x` | False -- Wave 0 |
| BAK-01 | 首次 apply 创建纯净备份 | unit | `pytest tests/unit/test_backup.py::test_create_pristine_backup -x` | False -- Wave 0 |
| BAK-02 | SHA-256 哈希计算和存储 | unit | `pytest tests/unit/test_backup.py::test_sha256_hash -x` | False -- Wave 0 |
| BAK-03 | 恢复前哈希验证 | unit | `pytest tests/unit/test_backup.py::test_hash_verification -x` | False -- Wave 0 |
| BAK-04 | CJK 纯净性检查 | unit | `pytest tests/unit/test_backup.py::test_cjk_purity_check -x` | False -- Wave 0 |
| BAK-05 | 原子写入 | unit | `pytest tests/unit/test_file_io.py::test_atomic_write -x` | False -- Wave 0 |
| BAK-06 | chmod 444 只读保护 | unit | `pytest tests/unit/test_backup.py::test_readonly_protection -x` | False -- Wave 0 |
| BAK-07 | 恢复后零中文字符 | unit | `pytest tests/unit/test_backup.py::test_restore_purity -x` | False -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_paths.py tests/unit/test_backup.py tests/unit/test_file_io.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` -- 包标记
- [ ] `tests/unit/__init__.py` -- 包标记
- [ ] `tests/unit/test_paths.py` -- 覆盖 PATH-01 ~ PATH-05
- [ ] `tests/unit/test_backup.py` -- 覆盖 BAK-01 ~ BAK-04, BAK-06, BAK-07
- [ ] `tests/unit/test_file_io.py` -- 覆盖 BAK-05 (原子写入)
- [ ] `tests/conftest.py` -- 共享 fixtures (临时目录、模拟 cli.js)
- [ ] `tests/fixtures/sample_cli.js` -- 模拟 cli.js 片段 (~10KB)
- [ ] Framework install: `pip install pytest`

## Sources

### Primary (HIGH confidence)
- Python `os.replace()` 文档 -- https://docs.python.org/3/library/os.html#os.replace -- 原子替换语义验证
- Python `hashlib` 文档 -- https://docs.python.org/3/library/hashlib.html -- SHA-256 分块 API
- Python `tempfile` 文档 -- https://docs.python.org/3/library/tempfile.html -- mkstemp API
- Python `shutil.which()` 文档 -- https://docs.python.org/3/library/shutil.html#shutil.which -- 可执行文件查找
- Python `argparse` 文档 -- https://docs.python.org/3/library/argparse.html -- subparsers API
- `pathlib.Path.resolve()` 文档 -- https://docs.python.org/3/library/pathlib.html -- symlink 解析行为
- ARCHITECTURE.md -- 架构决策：三级替换、备份完整性、偏移追踪
- PITFALLS.md -- 已识别陷阱：备份污染、短字符串、原子写入、硬编码路径
- STACK.md -- 技术栈决策：纯标准库、argparse、hashlib、tempfile
- localize.py -- 当前 v3.0 实现参考

### Secondary (MEDIUM confidence)
- [Stack Overflow: os.link vs os.rename vs os.replace for atomic writes](https://stackoverflow.com/questions/60369291/os-link-vs-os-rename-vs-os-replace-for-writing-atomic-write-files-what) -- os.replace() 跨平台行为
- [CPython Issue #143909: os.rename atomic replace documentation misleading](https://github.com/python/cpython/issues/143909) -- rename 原子性文档争议
- [Python Discussion: atomicwrite in stdlib](https://discuss.python.org/t/adding-atomicwrite-in-stdlib/11899) -- 原子写入模式社区讨论
- [Stack Overflow: Rename temporary file after closing](https://stackoverflow.com/questions/79807460/rename-temporary-file-after-closing-its-file-descriptor-in-python) -- tempfile + rename 模式

### Tertiary (LOW confidence)
- 无 -- 所有核心发现由标准库文档和实测验证支撑

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- 全部 Python 标准库，版本稳定，API 已验证
- Architecture: HIGH -- 路径检测策略已实测验证（Volta 场景），备份管理器模式已验证
- Pitfalls: HIGH -- 备份污染已确认（12,224 CJK 字符），Volta shim 行为已验证，chmod 444 已验证

**Research date:** 2026-04-05
**Valid until:** 2026-05-05 (30 days -- 标准库 API 稳定)
