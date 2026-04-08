# Phase 3: Integration & Quality - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

用户可以通过安装脚本一键部署汉化工具，且工具经过完整测试覆盖，达到可发布质量。具体包括：
1. 翻译覆盖率可量化（新增 coverage 命令）
2. 系统性补充缺失翻译条目（extract + 自动翻译 + 写入 + 后续验证）
3. 安装脚本在干净环境验证通过
4. 端到端往返验证（apply → verify → restore → verify）
5. 测试通过 + 代码覆盖率 >= 80%

</domain>

<decisions>
## Implementation Decisions

### 翻译覆盖率验证
- **D-01:** 新增独立 `coverage` 子命令（不是集成到现有命令中）
- **D-02:** coverage 命令输出表格形式（终端友好的人类可读格式，非纯 JSON）
- **D-03:** 覆盖率目标暂不定死 — 先做出来有量化能力，根据实际体验调整阈值

### zh-CN.json 补充策略
- **D-04:** 采用 Extract + 自动翻译 + 写入 + 后续验证流程
  - extract 扫描未翻译字符串候选
  - auto-translate 词典自动翻译
  - 自动写入 zh-CN.json
  - 后续使用 coverage 命令验证效果
- **D-05:** 补充范围：当前版本补全 + CI 自动化（GitHub Actions）
  - 当前补全为优先
  - CI 流水线在本次 Phase 中一并搭建

### 发布标准（全部必须满足）
- **D-06:** 193+ 测试全部通过，代码覆盖率 >= 80%
- **D-07:** coverage 命令可用，输出可量化的翻译覆盖率表格
- **D-08:** 真实 CLI 环境端到端往返验证（apply → verify → restore → verify）
- **D-09:** install.sh 在干净环境执行成功

### Claude's Discretion
- coverage 命令的具体表格列设计
- 自动翻译词典的更新策略细节
- CI workflow 的触发条件和步骤编排
- 具体测试用例设计

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目上下文
- `.planning/PROJECT.md` — 项目愿景、约束、关键技术决策
- `.planning/REQUIREMENTS.md` — 全部 v1 需求定义（Phase 3: INST-01~03, TEST-01~07）
- `.planning/ROADMAP.md` — Phase 3 目标和成功标准
- `.planning/phases/02-core-engine/02-CONTEXT.md` — Phase 2 上下文（引擎架构决策）

### 核心代码
- `scripts/i18n/cli.py` — CLI 框架，subcommand 路由
- `scripts/i18n/commands/` — 现有命令实现（apply, extract, status, restore, auto_update）
- `scripts/i18n/core/scanner.py` — 字符串扫描器
- `scripts/i18n/core/replacer.py` — 三级替换引擎
- `scripts/i18n/core/auto_translate.py` — 自动翻译模块
- `scripts/i18n/io/translation_map.py` — 翻译映射表 I/O
- `scripts/i18n/io/backup.py` — 备份管理器
- `install.sh` — 现有安装脚本

### 测试相关
- `tests/conftest.py` — 测试 fixtures
- `tests/unit/` — 19 个单元测试文件
- `tests/integration/test_roundtrip.py` — 端到端往返测试
- `tests/fixtures/` — 测试样本文件

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/i18n/core/scanner.py` — 字符串扫描逻辑可直接复用于 coverage 计算（统计已翻译/未翻译）
- `scripts/i18n/io/translation_map.py` — 翻译映射表加载逻辑，coverage 需要加载并统计条目
- `scripts/i18n/core/auto_translate.py` — 自动翻译模块已存在（63% 测试覆盖率，需加强）
- `scripts/i18n/commands/extract.py` — extract 命令已实现，可直接用于生成候选列表
- `install.sh` — 安装脚本已存在（4946 字节），需验证是否满足要求

### Established Patterns
- CLI 子命令注册：在 `cli.py` 的 `build_parser()` 中 `sub.add_parser('coverage')`
- 命令实现模式：`scripts/i18n/commands/` 下独立模块，每个命令一个文件
- JSON 输出模式：`output_json()` / `output_error()` 统一格式
- 测试模式：`tests/unit/test_xxx.py` + `tests/integration/`

### Integration Points
- coverage 命令需接入 scanner（扫描候选）+ translation_map（已翻译条目）+ skip_words（跳过词）
- 补充翻译条目需修改 `scripts/zh-CN.json`
- CI 需在 `.github/workflows/` 下创建 workflow 文件
- 安装脚本需同步 `commands/zcf/i18n.md` 技能命令

</code_context>

<specifics>
## Specific Ideas

- 用户反馈：实际使用中有明显未翻译内容，包括启动时界面和思考时的 Tip
- 翻译覆盖率 ≠ 测试覆盖率 — 这是两种完全不同的指标，需独立量化
- auto-translate 模块已有基础，但测试覆盖率仅 63%，需要加强

</specifics>

<deferred>
## Deferred Ideas

- 覆盖率阈值锁定（先量化再定目标）
- CI 自动化回归检测（本次 Phase 包含 GitHub Actions，但完整 CI 体系属于 v2 COV/CI/SMART 系列）
- 多语言支持（日/韩）— 当前仅中文

</deferred>

---

*Phase: 03-integration-quality*
*Context gathered: 2026-04-07*
