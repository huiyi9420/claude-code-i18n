# Stack Research

**Domain:** CLI i18n tool -- post-build localization of a 13MB minified JavaScript file using enhanced regex
**Researched:** 2026-04-05
**Confidence:** HIGH (standard library choices) / MEDIUM (performance optimization libraries)

---

## Recommended Stack

### Core Language & Runtime

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.8+ (target) | 主引擎语言 | 用户已安装 Python；现有代码库为 Python；正则表达式和字符串处理是 Python 的强项。3.8 是合理的最低版本——提供 walrus operator、positional-only params、`=` f-string。不用坚持 3.6 兼容（3.6 已 EOL，且缺少 `re` 模块的 variable-length lookbehind 在某些场景的优化）。开发环境为 3.14.3，但代码不应使用 3.8 以上语法特性。 |
| **Node.js** | 系统已安装 (22.x) | `node --check` 语法验证 | 替换后验证 JS 语法完整性。用户已安装 Node.js（Claude Code 依赖 Node）。不需要特定版本，`--check` flag 在所有 Node 版本都支持。 |

**置信度:** HIGH -- Python 是既定决策（PROJECT.md），Node.js 是必须依赖（Claude Code 本身需要 Node）。

### Core Standard Library (零外部依赖)

这是本项目的关键设计原则：**不引入任何外部 Python 依赖**。以下标准库模块构成整个引擎。

| Module | Python Version | Purpose | Why This Choice |
|--------|---------------|---------|-----------------|
| **`re`** | 3.8+ | 正则表达式引擎，字符串扫描与匹配 | 核心引擎。支持 lookbehind/lookahead/word boundary。对于本项目模式（800-6000 条翻译 x 13MB 文件），标准 `re` 足够快——瓶颈在 I/O 而非正则引擎。不需要 `regex` 第三方库（额外依赖、与 `re` API 不完全兼容、无显著性能优势）。预编译所有 pattern（`re.compile()`）在循环内重用。 |
| **`json`** | 3.8+ | 读写翻译映射表、skip-words、状态输出 | 标准 JSON 解析。13MB 的 JS 文件不需要 JSON 解析，但 ~80KB 的 zh-CN.json 和 skip-words.json 用标准 `json.load()`/`json.dump()` 即可。`ensure_ascii=False` 保证中文正确输出。 |
| **`pathlib.Path`** | 3.8+ | 文件路径操作 | 面向对象的路径操作，跨平台。用于 CLI 路径检测、备份管理、文件读写。比 `os.path` 更简洁、更 Pythonic。 |
| **`shutil`** | 3.8+ | 文件复制（备份创建/恢复） | `shutil.copy2()` 保留元数据。用于创建纯净英文备份和恢复操作。13MB 文件复制耗时 <0.1 秒，无需优化。 |
| **`hashlib`** | 3.8+ | SHA-256 校验和（备份完整性验证） | 分块读取文件计算 SHA-256（8KB chunks），验证备份未被污染。比完整文件读入内存更高效。用于备份创建时生成校验和、恢复前验证完整性。 |
| **`subprocess`** | 3.8+ | 调用 `node --check` 验证 JS 语法 | `subprocess.run(["node", "--check", path], capture_output=True, text=True, timeout=10)`。`capture_output=True` 避免输出泄露；`timeout=10` 防止挂起。不要用 `shell=True`（安全隐患 + timeout 不可靠）。 |
| **`argparse`** | 3.8+ | CLI 子命令路由 | 标准库，零依赖。当前 `localize.py` 用 `sys.argv` 手动解析（line 338-349），重写后用 `argparse` 的 `add_subparsers()` 实现正式的子命令结构（apply/restore/extract/status/coverage/version）。不需要 Click/Typer——本项目只有 6 个子命令，无复杂参数，argparse 完全够用。引入 Click 会增加一个外部依赖却无明显收益。 |
| **`os`** | 3.8+ | 原子文件写入（`os.rename`）、环境变量读取 | `os.rename()` 在 POSIX 上是原子操作，用于"写临时文件 -> 验证 -> rename 到目标"模式。`os.environ` 用于读取 `CLAUDE_I18N_PATH` 等环境变量覆盖。 |
| **`tempfile`** | 3.8+ | 安全的临时文件创建 | `tempfile.NamedTemporaryFile()` 用于 apply 流程中的"先写到临时文件，验证通过后再 rename"模式。 |
| **`sys`** | 3.8+ | 标准输出/错误输出、退出码 | 结构化 JSON 输出到 stdout，错误信息到 stderr。`sys.exit(0/1)` 返回标准退出码。 |

**置信度:** HIGH -- 全部是 Python 标准库，稳定可靠，无版本兼容性问题。

### 为什么不使用外部 Python 库

| 不用 | 原因 | 如果要用，什么时候 |
|------|------|-------------------|
| `click` / `typer` | 额外依赖，argparse 够用，本项目子命令简单 | 如果未来需要交互式 prompt、tab completion、彩色输出 |
| `regex` (PyPI) | 标准 `re` 已支持本项目所有需要的特性（lookbehind/lookahead/word boundary） | 如果需要 fuzzy matching、Unicode grapheme clusters、无限嵌套 |
| `pyahocorasick` | Aho-Corasick 多模式匹配，Phase 2 可能需要 | 当翻译条目超过 2000 条且性能成为瓶颈时再引入 |
| `chardet` / `charset-normalizer` | 目标文件编码已知为 UTF-8，不需要检测 | 如果需要处理未知编码的文件 |
| `rich` | 彩色终端输出，增加依赖 | 如果需要彩色进度条、表格输出（当前 JSON 输出够用） |
| `pydantic` | 翻译映射表验证，增加重依赖 | 映射表结构简单，手动验证即可 |

**置信度:** HIGH -- "零外部依赖"策略基于以下理由：(1) 用户群体是非技术或半技术用户，减少安装失败风险；(2) 核心功能全部可用标准库实现；(3) 13MB 文件处理不需要 numpy/pandas 级别的性能优化。

---

## Performance Strategy (Built on Standard Library)

### 大文件处理策略

本项目处理 13MB minified JS 文件。关键性能决策：

| 操作 | 策略 | 理由 |
|------|------|------|
| **读取 cli.js** | `Path.read_text(encoding="utf-8")` 一次性读入内存 | 13MB 在现代机器上只占 ~50MB Python 字符串内存，完全可接受。不需要 mmap 或分块读取——我们是对整个文件做全局字符串替换，不是流式处理。 |
| **写入 cli.js** | 写临时文件 -> 验证 -> `os.rename()` 原子替换 | 13MB 写入 <0.5 秒。原子写入保证安全性（崩溃不丢数据）。 |
| **正则匹配** | 预编译 pattern + 逆序替换 | `re.compile()` 预编译所有 pattern（800-6000 条）。逆序替换（`reversed(matches)`）避免偏移重算。 |
| **SHA-256 校验** | `hashlib.sha256()` + 8KB chunked 读取 | 不需要读整个文件到内存计算哈希。分块读取 + `update()` 流式计算。13MB 文件哈希计算 <0.5 秒。 |
| **node --check** | `subprocess.run(timeout=10)` | 单次调用，13MB 文件语法检查约 2-5 秒。设置 10 秒超时防止挂起。 |

### 性能预算 (基于 PROJECT.md: 30 秒内完成)

```
操作                        预估耗时
──────────────────────────────────────
读取 cli.js (13MB)          ~0.3s
加载 zh-CN.json (~80KB)     ~0.01s
预编译 ~6000 个 regex       ~0.5s
逆序替换 ~6000 条翻译       ~15-20s (主要瓶颈)
写入临时文件                ~0.3s
node --check 验证           ~3-5s
os.rename() 原子替换        ~0.01s
──────────────────────────────────────
总计                        ~20-26s (在 30s 预算内)
```

**置信度:** MEDIUM -- 替换阶段的耗时需要实测。6000 条翻译 x 13MB 字符串的 `re.finditer()` 循环是主要不确定性。如果超预算，Phase 2 引入 Aho-Corasick 多模式匹配优化。

### Phase 2 性能优化选项 (如果需要)

| Library | Purpose | When to Consider | Trade-off |
|---------|---------|-----------------|-----------|
| **`pyahocorasick`** | Aho-Corasick 多模式匹配，单次扫描找到所有翻译目标 | 翻译条目 >2000 且 apply 超过 30 秒 | 增加 C 扩展依赖，但性能提升可达 10-50x（单遍扫描 vs 逐条匹配） |
| **`mmap`** | 内存映射文件，避免读整个文件到 Python 堆 | 如果文件增长到 >50MB | 当前 13MB 不需要。mmap 对字符串替换场景收益有限（替换改变长度需要新写文件） |

---

## Translation Map Format

### 当前格式 (zh-CN.json, v4.2.0)

```json
{
  "_meta": {
    "name": "Claude Code 中文汉化",
    "version": "4.2.0",
    "cli_version": "2.1.92"
  },
  "translations": {
    "Accept edits": "接受编辑",
    "Bypass Permissions": "绕过权限"
  }
}
```

### 重写后格式 (支持上下文感知)

```json
{
  "_meta": {
    "name": "Claude Code 中文汉化",
    "version": "5.0.0",
    "cli_version": "2.1.92"
  },
  "translations": {
    "Accept edits": {
      "zh": "接受编辑",
      "scope": "global",
      "tier": "long"
    },
    "Error": {
      "zh": "错误",
      "scope": "quoted-only",
      "context": "ui-message",
      "tier": "short",
      "max_replacements": 30
    }
  }
}
```

**格式决策理由：**
- 保持 JSON 格式（可读、可编辑、标准库原生支持）
- 向后兼容：如果值是字符串（非对象），按 v4 格式处理
- `scope` 和 `tier` 可以由引擎自动推断（长/中/短），但允许手动覆盖
- `context` 标签为 Phase 2 上下文感知翻译预留

**置信度:** HIGH -- JSON 是正确选择（PROJECT.md 已确认）。结构化格式设计基于 PITFALLS.md 中的上下文感知需求。

---

## Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **`pytest`** | 单元测试 + 集成测试 | 仅开发时依赖，不分发给用户。用 `tests/fixtures/` 存放模拟的 cli.js 片段。`conftest.py` 提供 fixture。不需要 `unittest`——pytest 更简洁、fixture 更强大、参数化测试更好用。 |
| **`node` (system)** | `node --check` 语法验证 | 系统已安装 Node 22.x。集成测试中调用。 |
| **`shellcheck`** | 检查安装脚本（如果有 .sh 文件） | 可选，CI 中使用。 |

### pytest 项目结构

```
tests/
├── conftest.py              # 共享 fixtures（模拟 cli.js 片段、临时目录）
├── unit/
│   ├── test_scanner.py      # String Scanner 单元测试
│   ├── test_replacer.py     # Replacement Engine 单元测试
│   ├── test_verifier.py     # Verification Engine 单元测试
│   ├── test_backup.py       # Backup Manager 单元测试
│   ├── test_paths.py        # Path Resolver 单元测试
│   └── test_filters.py      # Noise Filter + UI Indicator 单元测试
├── integration/
│   ├── test_apply.py        # 完整 apply 流程测试
│   ├── test_restore.py      # 完整 restore 流程测试
│   ├── test_extract.py      # 完整 extract 流程测试
│   └── test_roundtrip.py    # apply -> restore 往返测试
└── fixtures/
    ├── sample_cli.js        # 模拟的 cli.js 片段（含各种字符串模式）
    ├── sample_zh_cn.json    # 测试用翻译映射表
    └── sample_skip.json     # 测试用跳过列表
```

**测试策略关键点：**
- `test/fixtures/sample_cli.js` 是手工构造的 ~10KB 文件，包含所有需要测试的字符串模式（长/中/短字符串、噪声字符串、模板字符串、单引号/双引号混合）
- 单元测试不依赖真实 13MB cli.js 文件
- 集成测试可用真实 cli.js（如果存在），但标记为 `@pytest.mark.integration` 可跳过
- 目标覆盖率 >= 80%（PROJECT.md 要求）

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| 主语言 | Python | Node.js/Bun | 已有 Python 代码库；用户已安装 Python；正则处理是 Python 强项。用 Node 重写意味着完全重新实现，且正则 API 无优势。 |
| 正则引擎 | `re` (stdlib) | `regex` (PyPI) | 标准 `re` 满足所有需求（lookbehind/lookahead/word boundary）。`regex` 提供的额外特性（fuzzy matching、`()\K`、Unicode 字符属性）本项目不需要。增加一个外部依赖无收益。 |
| 正则引擎 | `re` (stdlib) | `pyahocorasick` | Phase 1 不需要。Phase 2 性能不够时再引入。Aho-Corasick 只能做精确匹配，不支持正则约束（如 lookbehind），需要与 `re` 配合使用。 |
| CLI 框架 | `argparse` | `click` / `typer` | 只有 6 个简单子命令，无复杂参数类型、无交互式输入。argparse 零依赖。Click 增加依赖无收益。Typer 依赖 Click 更重。 |
| 文件 I/O | `Path.read_text()` | `mmap` | 13MB 直接读入内存完全可接受。mmap 的优势在 >100MB 文件的随机访问场景。本项目的操作模式（全局字符串替换）需要完整文件内容，mmap 无优势。 |
| 哈希算法 | `hashlib.sha256` | `hashlib.blake2b` | blake2b 更快，但 SHA-256 是通用校验和标准，所有平台/工具都能验证。性能差异在 13MB 文件上可忽略。 |
| 测试框架 | `pytest` | `unittest` | pytest 的 fixture、参数化测试、简洁断言语法更适合本项目。unittest 样板代码多、fixture 不灵活。pytest 是 2025 Python 测试事实标准。 |
| 翻译格式 | JSON | YAML / TOML / .po | JSON 是标准库原生支持、所有文本编辑器可直接编辑、无缩进敏感问题。YAML 需要额外依赖。.po 格式过于复杂。TOML 对嵌套结构支持有限。 |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **AST parser (acorn/babel/esprima/tree-sitter)** | 13MB minified JS 文件上不可行。AST 解析耗时 5-15 秒，内存消耗 65-130MB（AST 是源文件的 5-10x）。每次替换后需重新 parse。已验证不可行（ARCHITECTURE.md）。 | 增强型 regex + 引号上下文匹配 |
| **`sed` / `awk` 做字符串替换** | sed 对 UTF-8 中文处理不可靠；不支持 lookbehind/lookahead；无长度变化后的偏移追踪；错误处理原始。当前代码的"步骤 6 sed 裸替换"已被确认为反模式（PITFALLS.md）。 | Python `re` + `str.replace()` |
| **`str.replace()` 对短字符串全局替换** | `"Error"` 全局替换会命中代码逻辑中的字符串比较，破坏运行时行为。PITFALLS.md Pitfall 3 详细记录。 | 三级替换策略：长字符串精确替换，中/短字符串用 regex 引号边界约束 |
| **`shell=True` in subprocess** | `subprocess.run(cmd, shell=True)` 在 timeout 时只杀 shell 进程，子进程成为孤儿。安全问题（命令注入）。 | `subprocess.run([list], capture_output=True, timeout=10)` |
| **直接覆盖写 cli.js** | 崩溃导致文件损坏，用户无法恢复 CLI。PITFALLS.md Pitfall 11。 | 写临时文件 -> node --check 验证 -> `os.rename()` 原子替换 |
| **从已汉化的 cli.js 提取字符串** | 中文文本被误认为"新字符串"，污染翻译映射表。PITFALLS.md Pitfall 1 + Anti-Pattern 1。 | 始终从纯净备份 (cli.bak.en.js) 提取 |
| **mmap 做字符串替换** | mmap 映射的文件大小是固定的，替换操作改变字符串长度后需要新写文件。mmap 的随机访问优势在全局替换场景无用武之地。 | `Path.read_text()` 一次性读入 + 字符串操作 + 原子写入 |

---

## Stack Patterns by Variant

**如果翻译条目增长到 2000+ 且 apply 耗时超过 30 秒：**
- 引入 `pyahocorasick` 做多模式匹配（单次扫描找到所有匹配位置）
- 用 Aho-Corasick 找位置，`re` 做 context 验证
- 预期性能提升 5-10x

**如果目标文件增长到 50MB+：**
- 考虑 mmap 读取（但替换仍需要新写文件）
- 考虑分块处理（但 minified JS 的字符串可能跨块边界）
- 更现实的方案：流式读取 + 索引构建 + 批量替换

**如果需要支持其他语言（日文/韩文）：**
- 翻译映射表文件名改为 `ja-JP.json` / `ko-KR.json`
- 引擎代码不变（语言无关的替换逻辑）
- 各语言独立的 Translation Map

---

## Version Compatibility

| Component | Minimum Version | Maximum Tested | Notes |
|-----------|----------------|----------------|-------|
| Python | 3.8 | 3.14.3 | 3.8 提供 walrus operator、positional-only params。不用 3.10+ 语法（match/case、TypeAlias）。不用 3.12+ 语法（type parameter syntax）。 |
| `re` module | Python 3.8+ | 3.14.3 | Variable-length lookbehind 从 3.6 开始支持（`(?<=...)` 内可使用 `*`/`+` 量词）。所有本项目使用的 `re` 特性在 3.8+ 可用。 |
| Node.js | 14.x | 22.x | `node --check` 在所有 Node 版本支持。Claude Code 本身需要 Node 18+，所以 Node 可用性不是问题。 |
| `json` module | Python 3.8+ | 3.14.3 | `json.load()`/`json.dump()` 在所有版本稳定。`ensure_ascii=False` 保证中文正确输出。 |

---

## Installation

```bash
# 无需安装任何 Python 包
# 所有依赖都是 Python 标准库

# 开发依赖（仅开发者需要）
pip install pytest

# 运行测试
pytest tests/ -v

# 运行工具（用户）
python3 scripts/localize.py apply
python3 scripts/localize.py restore
python3 scripts/localize.py extract
python3 scripts/localize.py status
```

---

## Sources

- **Python `re` module documentation** — https://docs.python.org/3/library/re.html — 正则 API 和性能特性验证 (HIGH confidence)
- **Python `hashlib` documentation** — https://docs.python.org/3/library/hashlib.html — SHA-256 分块哈希 API (HIGH confidence)
- **Python `subprocess` documentation** — https://docs.python.org/3/library/subprocess.html — subprocess.run timeout 和 capture_output 参数 (HIGH confidence)
- **Python `argparse` documentation** — https://docs.python.org/3/library/argparse.html — 子命令解析 API (HIGH confidence)
- **Stack Overflow: Is it worth using Python's re.compile?** — https://stackoverflow.com/questions/452104/is-it-worth-using-pythons-re-compile — re.compile() 性能收益评估 (HIGH confidence)
- **Stack Overflow: Speed up re.sub on large strings** — https://stackoverflow.com/questions/73956255/speed-up-re-sub-on-large-strings-representing-large-files-in-python — 大字符串 regex 性能优化 (MEDIUM confidence)
- **Stack Overflow: Memory efficiency of finding strings in large files** — https://stackoverflow.com/questions/50976390/memory-and-computation-efficiency-of-finding-strings-in-large-files-with-python — mmap vs read_text 对比 (MEDIUM confidence)
- **Dasroot: Building CLI Tools with Python (Click, Typer, argparse)** — https://dasroot.net/posts/2025/12/building-cli-tools-python-click-typer-argparse/ — CLI 框架对比 (MEDIUM confidence)
- **pytest documentation: Good Integration Practices** — https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html — 测试项目结构 (HIGH confidence)
- **ARCHITECTURE.md** — 本项目已确认的架构决策：regex 而非 AST (HIGH confidence, project-internal)
- **PITFALLS.md** — 本项目已识别的陷阱和缓解策略 (HIGH confidence, project-internal)
- **localize.py source code** — 当前实现参考 (HIGH confidence, primary source)
- **Blake2b vs SHA-256 comparison** — https://mojoauth.com/compare-hashing-algorithms/sha-256-vs-blake2b — 哈希算法性能对比 (MEDIUM confidence)
- **CPython Issue #105657: hashlib unstable results on large files** — https://github.com/python/cpython/issues/105657 — 已知 hashlib 大文件问题 (MEDIUM confidence, edge case awareness)

---
*Stack research for: CLI i18n tool for minified JavaScript (Claude Code)*
*Researched: 2026-04-05*
