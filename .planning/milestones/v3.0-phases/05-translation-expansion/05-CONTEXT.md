# Phase 5: 翻译扩充与质量保障 - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning
**Mode:** Claude's Discretion

<domain>
## Phase Boundary

将翻译条目从 1,301 扩充至 2,500+，翻译覆盖率从 48% 提升到 80%+，高频可见字符串覆盖率 95%+，并建立翻译质量验证机制。具体包括：
1. 大量新增策展翻译条目（目标 +1,200 条）
2. 翻译质量验证工具（检测中英混杂、同义不一致、格式占位符丢失）
3. 利用上下文感知架构提高高频字符串覆盖率
4. 验证 apply 后 Claude Code 日常使用界面全部显示中文

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
所有实现选择由 Claude 自行决定 — 用户明确表示"你决定即可"。使用 ROADMAP 阶段目标、成功标准和代码库约定来指导决策。

### 翻译扩充策略（Claude 决定）
- 优先翻译 score≥2 的高频可见字符串（达到 95% 覆盖）
- 长字符串翻译聚焦用户可见 UI 文本，跳过低频内部错误消息
- 使用 extract 命令提取未翻译候选，人工策展翻译
- UI 模板匹配（auto_translate.py 的 UI_TEMPLATES）质量可接受，可用于辅助筛选
- prefix_suffix_match 已验证质量差，不使用

### 质量验证（Claude 决定）
- 新增独立 `validate` 命令用于翻译质量验证
- 检测三类问题：中英混杂、同义不一致、格式占位符丢失
- 不在 apply 时实时检测（避免影响替换性能）
- 输出 JSON 格式报告，可被 CI 集成

### 高频字符串定义（Claude 决定）
- 沿用现有 scanner.py 的信号评分系统
- score≥2 即为"高频可见"
- 不调整评分标准

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目上下文
- `.planning/PROJECT.md` — 项目愿景、约束、翻译现状
- `.planning/REQUIREMENTS.md` — v3.1 需求（COV-01~04, CTX-04）
- `.planning/ROADMAP.md` — Phase 5 目标和成功标准

### 核心代码（必须理解）
- `scripts/zh-CN.json` — 当前翻译映射表（1,301 条，纯字符串格式）
- `scripts/i18n/core/scanner.py` — 字符串扫描器（评分系统 + 上下文检测）
- `scripts/i18n/core/auto_translate.py` — 规则引擎（UI_TEMPLATES 质量可接受，prefix_suffix_match 已弃用）
- `scripts/i18n/io/translation_map.py` — 翻译映射表 I/O（v4/v5/v6 格式支持）
- `scripts/i18n/core/context_detector.py` — 上下文检测模块（10 种功能区块）
- `scripts/i18n/core/replacer.py` — 上下文感知替换引擎
- `scripts/i18n/commands/coverage.py` — 覆盖率命令（按长度分类统计）
- `scripts/i18n/commands/extract.py` — 提取命令（含组件来源标注）

### 测试
- `tests/unit/` — 现有单元测试
- `tests/conftest.py` — 测试 fixtures

### 已验证的决策
- `.planning/phases/04-context-aware-arch/04-CONTEXT.md` — Phase 4 上下文感知架构决策

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `auto_translate.py` — UI_TEMPLATES 规则（22 个模板）质量可接受，可用于辅助翻译生成
- `scanner.py` — 信号评分系统（score 1-5），score≥2 为高频可见字符串
- `extract.py` — 提取未翻译候选并标注组件来源（Phase 4 新增）
- `coverage.py` — 按长度分类统计覆盖率（long/medium/short）
- `context_detector.py` — 10 种功能区块检测（tools, auth, mcp, git 等）

### Established Patterns
- 翻译映射表格式：v4 字符串为主，v6 上下文格式已支持但尚无条目使用
- 命令实现：`scripts/i18n/commands/` 下独立模块
- JSON 输出：`output_json()` / `output_error()` 统一格式
- 策展翻译：手动逐条编辑 zh-CN.json，质量远高于规则引擎

### Integration Points
- `zh-CN.json` 需要新增 1,200+ 条翻译条目
- `validate` 命令需要读取翻译映射表并执行质量检查
- `coverage.py` 需要在翻译扩充后验证覆盖率达标

### 翻译现状
- 长字符串(>20): 826 已翻译 / ~1,418 未翻译
- 中字符串(10-20): 384 已翻译 (100%)
- 短字符串(<10): 84 已翻译 (92.3%)
- 总覆盖率: 48.0% (1,301/2,719)
- 目标: 2,500+ 条 / 80%+ 覆盖率

</code_context>

<specifics>
## Specific Ideas

No specific requirements — user deferred all decisions to Claude. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 05-translation-expansion*
*Context gathered: 2026-04-07*
