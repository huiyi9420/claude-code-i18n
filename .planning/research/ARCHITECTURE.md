# Architecture Research

**Domain:** CLI i18n / minified JavaScript string replacement tool
**Researched:** 2026-04-05
**Confidence:** HIGH (core architecture) / MEDIUM (具体性能参数需实测验证)

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                          │
│                    (localize.py / install.sh)                    │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ apply    │ restore  │ extract  │ status   │ coverage            │
│ command  │ command  │ command  │ command  │ command             │
├──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                      Command Router Layer                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  String Scanner  │  │ Replacement      │  │ Verification  │  │
│  │  (Extractor)     │  │ Engine           │  │ Engine        │  │
│  │                  │  │                  │  │               │  │
│  │ - Regex scanner  │  │ - Tiered replace │  │ - node --check│  │
│  │ - Quote context  │  │ - Offset tracker │  │ - Round-trip  │  │
│  │ - Noise filter   │  │ - Length delta   │  │ - Diff audit  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │
│           │                     │                     │          │
├───────────┴─────────────────────┴─────────────────────┴──────────┤
│                        Core Services Layer                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Translation Map  │  │ Path Resolver    │  │ Backup Manager│  │
│  │ (zh-CN.json)     │  │ (auto-detect)    │  │ (clean I/O)   │  │
│  │ - context tags   │  │ - volta/npm/     │  │ - integrity   │  │
│  │ - skip lists     │  │   global/local   │  │ - checksum    │  │
│  │ - version lock   │  │ - env vars       │  │ - zero-pollute│  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                       Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ cli.js   │  │ backup   │  │ zh-CN    │  │ skip-words       │ │
│  │ (target) │  │ (pristine│  │ .json    │  │ .json            │ │
│  │          │  │  English)│  │ (map)    │  │ (exclusion list) │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decision: AST vs Regex

### Verdict: 增强型 Regex + 字符串字面量上下文感知 (不用 AST)

**原因：**

1. **AST 在 13MB minified 文件上不可行**
   - Acorn（最快的 JS parser）处理 13MB minified 文件预计耗时 5-15 秒，内存消耗约 5-10x 文件大小（65-130MB 的 AST）
   - Babel parser 更慢，且 AST 不兼容其他工具
   - Tree-sitter 在 32KB 以上文件就有已知问题，1.6MB JSON 需 1.2 秒，13MB JS 无法保证稳定
   - 每次替换后需重新 parse 验证，反复解析开销不可接受

2. **我们不需要理解代码结构** -- 只需要定位并替换引号内的字符串字面量
   - AST 提供的信息（变量作用域、控制流、函数边界）对我们无用
   - 我们只需要知道：这个字符串在不在引号内？前面/后面的上下文是什么？

3. **regex 可以精确匹配引号上下文**
   - `(?<=")...(?=")` 精确定位双引号字符串
   - 配合 lookbehind/lookahead 实现上下文约束
   - Python `re` 模块支持这些高级特性（Python 3.6+）

**置信度：HIGH -- 基于多个 parser benchmark 和 minified JS 处理实践得出。**

## Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| **CLI Entry Point** | 用户交互入口，参数解析，子命令路由 | Python argparse / 简单 sys.argv 解析 |
| **Path Resolver** | 自动检测 cli.js 安装路径（Volta/npm/global） | 检查环境变量 + `which` + 常见路径枚举 |
| **Backup Manager** | 创建/恢复/验证纯净英文备份 | shutil.copy2 + SHA-256 校验和 + 汉化检测 |
| **String Scanner (Extractor)** | 从 cli.js 提取可翻译字符串候选 | 正则提取 + 噪声过滤 + UI 指标评分 |
| **Translation Map** | 管理 en->zh 映射关系，上下文标签 | JSON 文件 + context 字段 + 版本锁定 |
| **Replacement Engine** | 执行安全替换，处理长度变化 | 分级策略（长/中/短）+ 偏移追踪 + 长度 delta |
| **Verification Engine** | 替换后验证 JS 语法完整性 | `node --check` + 可选 round-trip 验证 |
| **Coverage Reporter** | 计算并报告翻译覆盖率 | 统计已翻译/未翻译/跳过占比 |

## Recommended Project Structure

```
scripts/
├── i18n/                     # 主引擎包
│   ├── __init__.py
│   ├── cli.py                # CLI 入口，argparse 子命令
│   ├── commands/             # 子命令实现
│   │   ├── __init__.py
│   │   ├── apply.py          # 汉化命令
│   │   ├── restore.py        # 恢复命令
│   │   ├── extract.py        # 提取命令
│   │   ├── status.py         # 状态命令
│   │   └── coverage.py       # 覆盖率报告命令
│   ├── core/                 # 核心引擎（纯逻辑，无 I/O）
│   │   ├── __init__.py
│   │   ├── scanner.py        # 字符串扫描器（提取候选）
│   │   ├── replacer.py       # 替换引擎（分级策略）
│   │   ├── verifier.py       # 验证引擎（语法检查）
│   │   └── offset_tracker.py # 偏移追踪器（处理替换导致的位移）
│   ├── config/               # 配置与路径管理
│   │   ├── __init__.py
│   │   ├── paths.py          # Path Resolver（自动检测安装路径）
│   │   └── constants.py      # 常量定义
│   ├── io/                   # I/O 操作层
│   │   ├── __init__.py
│   │   ├── backup.py         # 备份管理器（纯净备份保证）
│   │   ├── file_io.py        # 文件读写（大文件优化）
│   │   └── translation_map.py # 翻译映射表 I/O
│   └── filters/              # 过滤器
│       ├── __init__.py
│       ├── noise_filter.py   # 第三方库噪声过滤
│       └── ui_indicator.py   # UI 指标评分
├── data/                     # 翻译数据文件
│   ├── zh-CN.json            # 翻译映射表（带上下文标签）
│   └── skip-words.json       # 跳过列表
├── tests/                    # 测试
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── fixtures/             # 测试用的 cli.js 片段
└── localize.py               # 向后兼容入口（重定向到 i18n/cli.py）
```

### Structure Rationale

- **i18n/commands/**: 每个子命令独立文件，职责单一，便于单独测试和维护
- **i18n/core/**: 核心逻辑与 I/O 分离 -- replacer 和 scanner 不关心文件从哪来，只处理字符串。这使得单元测试可以不依赖真实 13MB 文件
- **i18n/io/**: 所有文件操作集中管理，备份完整性保证集中在此层
- **i18n/filters/**: 过滤逻辑独立，噪声关键词列表和 UI 指标可以独立演化
- **tests/fixtures/**: 存放 cli.js 的模拟片段，避免测试依赖真实安装

## Architectural Patterns

### Pattern 1: 三级替换策略 (Tiered Replacement)

**What:** 根据字符串长度分三个等级，使用不同精度的替换策略。
**When:** 替换 minified JS 中的字符串时，必须平衡覆盖率与安全性。
**Trade-offs:** 长字符串安全但覆盖少；短字符串覆盖广但风险高。

```
Level 1: 长字符串 (>20 chars)
  -> 精确全文替换 content.replace(en, zh)
  -> 风险: 极低（长字符串几乎不可能误匹配）
  -> 无需上下文约束

Level 2: 中等字符串 (10-20 chars)
  -> 引号边界约束 (?<=[\"'])...(?=[\"'])
  -> 风险: 低（确保只在字符串字面量内替换）
  -> 不跨引号替换

Level 3: 短字符串 (<10 chars)
  -> 引号 + 词边界 + 频率上限
  -> (?<=[\"'\\s>])\\b...\\b(?=[\"'\\s<])
  -> 风险: 中等（需配合 skip-words 白名单）
  -> 每个短字符串最多替换 N 次（cap=50）
  -> 必须在 skip-words.json 白名单中才执行
```

### Pattern 2: 备份完整性保证 (Pristine Backup Guarantee)

**What:** 备份文件在创建时验证纯净性，restore 后再次验证。
**When:** 任何涉及修改用户文件的场景。
**Trade-offs:** 增加少量 I/O 开销，但保证 restore 功能可靠。

```python
# 备份创建流程
def create_pristine_backup(cli_path, backup_path):
    # 1. 检查是否已存在备份
    if backup_path.exists():
        # 2. 验证现有备份是否纯净（不含中文字符）
        if is_pristine_english(backup_path):
            return  # 已有纯净备份，无需重复创建
        else:
            # 污染备份 -> 重命名旧备份，创建新的
            backup_path.rename(backup_path.with_suffix('.polluted.js'))

    # 3. 从 cli.js 创建新备份
    shutil.copy2(cli_path, backup_path)

    # 4. 写入校验和
    checksum = sha256_file(backup_path)
    write_checksum(backup_path.with_suffix('.sha256'), checksum)

def is_pristine_english(file_path):
    """检测文件是否包含中文（即是否被污染）"""
    content = file_path.read_text(encoding='utf-8')
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    return chinese_chars == 0
```

### Pattern 3: 偏移追踪 (Offset Tracking)

**What:** 替换操作可能改变字符串长度，后续替换需要追踪累积偏移。
**When:** 使用索引定位替换（如 regex match 对象的 start/end）时。
**Trade-offs:** 比逆序替换稍复杂，但更灵活。

```python
class OffsetTracker:
    """追踪替换操作导致的累积偏移量"""
    def __init__(self):
        self._offsets = []  # [(position, delta), ...]

    def adjust(self, original_pos):
        """将原始位置调整为当前实际位置"""
        adjusted = original_pos
        for pos, delta in self._offsets:
            if pos < original_pos:
                adjusted += delta
        return adjusted

    def record(self, position, delta):
        self._offsets.append((position, delta))
```

**更简单的替代方案：逆序替换** -- 从文件末尾开始替换，这样前面的偏移不受影响。当前 v3.0 代码已经在用 `reversed(matches)` 实现这一点。

**建议：** 保持逆序替换作为主策略，OffsetTracker 作为备选方案记录。逆序替换在当前场景下更简洁。

### Pattern 4: 上下文感知翻译 (Context-Aware Translation Map)

**What:** 翻译映射表支持上下文标签，同一英文在不同场景可有不同翻译。
**When:** 短字符串和中等字符串的翻译尤其需要上下文。
**Trade-offs:** 映射表稍复杂，但大幅减少误替换。

```json
{
  "_meta": { "cli_version": "2.1.92" },
  "translations": {
    "Stop": {
      "zh": "停止",
      "context": "ui-button",
      "scope": "quoted-only"
    },
    "Error": {
      "zh": "错误",
      "context": "ui-message",
      "scope": "quoted-only"
    }
  }
}
```

**scope 字段说明：**
- `global`: 全局替换（长字符串默认）
- `quoted-only`: 仅在引号内替换（中/短字符串默认）
- `context-required`: 需要匹配上下文标签才替换

## Data Flow

### Apply Flow (汉化流程)

```
用户执行 apply
    |
    v
Path Resolver --> 确认 cli.js 路径
    |
    v
Backup Manager --> 创建纯净备份（如不存在）
    |                  |-- 验证备份纯净性（无中文字符）
    |                  |-- 计算 SHA-256 校验和
    v
从备份恢复 cli.js（确保从干净状态开始）
    |
    v
加载 Translation Map (zh-CN.json)
    |
    v
String Scanner --> 读取 cli.js，识别可替换位置
    |                  |-- 长字符串: 精确匹配
    |                  |-- 中字符串: 引号边界匹配
    |                  |-- 短字符串: 词边界 + skip 白名单
    v
Replacement Engine --> 按长度降序执行替换
    |                      |-- 逆序替换避免偏移问题
    |                      |-- 短字符串有频率上限
    v
写入 cli.js
    |
    v
Verification Engine --> node --check 验证语法
    |                       |-- 失败: 从备份回滚 + 报错
    |                       |-- 成功: 继续下一步
    v
Coverage Reporter --> 统计替换结果
    |
    v
输出结果 (JSON)
```

### Restore Flow (恢复流程)

```
用户执行 restore
    |
    v
Backup Manager --> 检查备份是否存在
    |                  |-- 不存在: 报错退出
    |                  |-- 存在: 验证校验和
    v
验证备份纯净性（无中文）
    |
    v
shutil.copy2(backup, cli.js)
    |
    v
输出结果 (JSON)
```

### Extract Flow (提取流程)

```
用户执行 extract
    |
    v
从备份(优先)或 cli.js 读取内容
    |
    v
String Scanner --> 正则提取所有双引号内英文字符串
    |
    v
Noise Filter --> 过滤第三方库噪声（azure/aws/grpc...）
    |
    v
UI Indicator Scorer --> 评估 UI 相关性（强信号/弱信号）
    |
    v
过滤: 已翻译 + 已跳过 + 非自然语言 + 代码片段
    |
    v
按评分排序输出 (JSON)
```

### Key Data Flows

1. **单方向数据流:** 备份文件只能被读取和复制，永远不被修改。cli.js 是唯一被写入的目标文件。这确保了 restore 的可靠性。

2. **Translation Map 驱动:** 替换操作完全由映射表驱动。映射表是声明式的，引擎是通用的。改变翻译只需改 JSON，不需改代码。

3. **验证是门控:** 每次写入 cli.js 后必须通过 `node --check`。这是不可绕过的安全门。

## Component Communication Map

```
                  ┌─────────────┐
                  │   CLI Entry  │
                  └──────┬──────┘
                         │ routes to
          ┌──────────────┼──────────────┐
          v              v              v
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  apply   │   │ restore  │   │ extract  │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         v              v              v
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Scanner  │   │  Backup  │   │ Scanner  │
    │ Replacer │   │  Manager │   │ Filters  │
    │ Verifier │   │          │   │          │
    └────┬─────┘   └──────────┘   └──────────┘
         │
         v
    ┌──────────┐   ┌──────────────┐   ┌──────────┐
    │ Backup   │   │ Translation  │   │  Path    │
    │ Manager  │   │ Map          │   │ Resolver │
    └──────────┘   └──────────────┘   └──────────┘
```

**边界规则：**
- Scanner/Replacer/Verifier 之间不直接通信，由 Command 层协调
- Backup Manager 不关心替换逻辑，只保证备份完整性
- Translation Map 是只读数据源，不被引擎修改
- Path Resolver 是纯计算组件，不执行任何 I/O

## Anti-Patterns

### Anti-Pattern 1: 从已汉化的 cli.js 提取字符串

**What people do:** extract 命令从当前 cli.js（可能已汉化）提取
**Why it's wrong:** 会把中文翻译误认为"新字符串"，污染翻译映射表
**Do this instead:** 始终从纯净备份 (cli.bak.en.js) 提取。当前 v3.0 已经做了这个处理 (`src = BACKUP if BACKUP.exists() else CLI_FILE`)，但备份本身可能被污染。

### Anti-Pattern 2: 在原地替换时重新计算偏移

**What people do:** 替换一个字符串后，重新扫描整个 13MB 文件找下一个
**Why it's wrong:** 13MB 文件的全文扫描 x 800+ 次替换 = 极慢
**Do this instead:** 一次性找到所有匹配位置，逆序替换（从后往前），这样前面的位置不受影响。

### Anti-Pattern 3: 不验证替换后的语法

**What people do:** 替换完直接交付用户使用
**Why it's wrong:** 一个错误的替换（比如截断了引号）会导致 CLI 完全无法启动
**Do this instead:** 每次替换批次后必须 `node --check` 验证。当前 v3.0 已实现，重写时保留。

### Anti-Pattern 4: 短字符串全局无条件替换

**What people do:** "Error" -> "错误" 无差别全局替换
**Why it's wrong:** "Error" 可能出现在变量名、类型名、API 路径中，替换后破坏代码逻辑
**Do this instead:** 短字符串必须：(1) 在 skip-words 白名单中，(2) 有引号边界约束，(3) 有替换次数上限。

### Anti-Pattern 5: 硬编码安装路径

**What people do:** `CLI_DIR = Path("/Users/zhaolulu/.volta/...")`
**Why it's wrong:** 其他用户的安装路径不同，工具无法使用
**Do this instead:** Path Resolver 自动检测 -- 检查 `which claude`，遍历常见安装路径，支持环境变量覆盖。

## Scalability Considerations

| Concern | 当前 (单用户/单版本) | 多版本 | 多语言 |
|---------|---------------------|--------|--------|
| 目标文件大小 | 13MB, 直接读入内存 | 不变 | 不变 |
| 翻译条目 | ~834 条 (当前) | ~6000+ 条（目标） | ~6000+ x N 语言 |
| 替换耗时 | ~5 秒 (估计) | ~15-30 秒 | ~15-30 秒/语言 |
| 内存使用 | ~50MB (13MB 文件 x2) | ~50MB | ~50MB |

### Scaling Priorities

1. **First bottleneck: 翻译条目从 834 增长到 6000+**
   - 当前逐条替换策略在 6000+ 条时可能变慢
   - 解决方案: 批量替换（合并 regex）+ 预编译 pattern
   - 当前实现已按长度降序排序，这是正确的优化方向

2. **Second bottleneck: 多语言支持（如果未来扩展）**
   - 每种语言需要独立的 Translation Map
   - apply 流程需要先 restore 到英文再替换目标语言
   - 架构已为此预留空间（Translation Map 是独立的 JSON 文件）

## Build Order (Component Dependencies)

```
Phase 1: Foundation (无依赖)
  ├── Path Resolver (config/paths.py)
  ├── Constants (config/constants.py)
  └── File I/O utilities (io/file_io.py)

Phase 2: Data Layer (依赖 Phase 1)
  ├── Translation Map I/O (io/translation_map.py)
  └── Backup Manager (io/backup.py)

Phase 3: Core Engine (依赖 Phase 1)
  ├── Noise Filter (filters/noise_filter.py)
  ├── UI Indicator (filters/ui_indicator.py)
  ├── String Scanner (core/scanner.py) -- 依赖 filters
  ├── Replacement Engine (core/replacer.py) -- 依赖 scanner
  └── Verification Engine (core/verifier.py) -- 依赖 paths

Phase 4: Commands (依赖 Phase 2 + 3)
  ├── restore command -- 依赖 Backup Manager
  ├── status command -- 依赖 Path Resolver + Translation Map
  ├── extract command -- 依赖 Scanner + Filters
  ├── apply command -- 依赖 Replacer + Verifier + Backup Manager
  └── coverage command -- 依赖 Scanner + Translation Map

Phase 5: CLI Integration (依赖 Phase 4)
  ├── CLI Entry Point (cli.py)
  └── Backward-compatible localize.py wrapper
```

**关键路径:** Path Resolver -> Backup Manager -> Replacement Engine -> apply command

**Phase 3 内部依赖:** Noise Filter 和 UI Indicator 是 Scanner 的前置条件。Scanner 是 Replacer 的前置条件。Verifier 独立于 Scanner/Replacer，可与它们并行开发。

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Node.js (`node --check`) | subprocess.run() | 语法验证，必须安装 Node.js |
| Claude Code CLI | 文件系统路径 | 读取/修改 cli.js，通过 Path Resolver 定位 |
| Volta / npm | `which` + 路径推断 | 检测 CLI 安装位置 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Command -> Core Engine | 函数调用 | Command 层编排 Core 组件 |
| Core Engine -> I/O Layer | 函数调用 + 返回值 | Core 不直接操作文件，通过 I/O 层 |
| Translation Map -> Core | 只读数据加载 | 启动时一次性加载，运行时不可变 |
| Backup Manager -> File System | 受限写操作 | 只写 backup 文件，且带校验 |

## 现有代码重用评估

| 现有模块 | 重用程度 | 说明 |
|----------|----------|------|
| NOISE_KW / NOISE_RE | 高 | 噪声过滤列表质量好，直接迁移 |
| STRONG_INDICATORS / WEAK_INDICATORS | 高 | UI 指标列表设计合理 |
| 三级替换策略骨架 | 中 | 概念正确，实现需重写（加入偏移追踪、上下文感知） |
| extract 命令逻辑 | 中 | 核心过滤流程可复用，但需从备份提取 |
| cmd_restore | 低 | 需增加纯净性验证 |
| 硬编码路径 | 不重用 | 必须替换为 Path Resolver |

## Sources

- [Acorn vs @babel/parser vs espree 对比 (PkgPulse 2026)](https://www.pkgpulse.com/blog/acorn-vs-babel-parser-vs-espree-javascript-ast-parsers-2026)
- [ECMAScript Parser Benchmark](https://github.com/prantlf/ecmascript-parser-benchmark)
- [Tree-sitter 大文件性能问题 #1277](https://github.com/tree-sitter/tree-sitter/issues/1277)
- [Tree-sitter 32KB 限制 (StackOverflow)](https://stackoverflow.com/questions/79507130/tree-sitter-size-limitation-fails-if-code-is-32kb)
- [Minified JS 指纹分析工具集](https://gist.github.com/0xdevalias/31c6574891db3e36f15069b859065267)
- [AST 反混淆 JavaScript 字符串提取](https://steakenthusiast.github.io/2022/05/22/Deobfuscating-Javascript-via-AST-Manipulation-Various-String-Concealing-Techniques/)
- [Minified JS find & replace 有效性讨论 (StackOverflow)](https://stackoverflow.com/questions/54561755/minified-js-find-and-replace-a-valid-strategy-for-substitution)
- [Esprima 性能和内存问题 #1896](https://github.com/jquery/esprima/issues/1896)
- [V8 Web Tooling Benchmark](https://github.com/v8/web-tooling-benchmark/issues/58)

---
*Architecture research for: CLI i18n tool for minified JavaScript (Claude Code)*
*Researched: 2026-04-05*
