# Phase 4: 上下文感知架构 - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

翻译映射表和替换引擎支持同一英文字符串在不同组件中拥有不同中文翻译，用户运行汉化后各界面组件的翻译更准确自然。具体包括：
1. 映射表支持上下文标签（同一英文多翻译）
2. 替换引擎按上下文优先级选择翻译
3. extract 输出包含组件来源信息
4. v3.0 格式向后兼容

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
所有实现选择由 Claude 自行决定 — 纯基础设施阶段。使用 ROADMAP 阶段目标、成功标准和代码库约定来指导决策。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目上下文
- `.planning/PROJECT.md` — 项目愿景、约束
- `.planning/REQUIREMENTS.md` — v3.1 需求（CTX-01, CTX-02, CTX-03）
- `.planning/ROADMAP.md` — Phase 4 目标和成功标准

### 核心代码（必须理解）
- `scripts/i18n/io/translation_map.py` — 翻译映射表加载/保存（当前仅支持字符串值和带 "zh" 键的字典值）
- `scripts/i18n/core/replacer.py` — 三级替换引擎（当前无上下文感知）
- `scripts/i18n/core/scanner.py` — 字符串扫描器（当前无组件来源信息）
- `scripts/i18n/commands/apply.py` — apply 命令入口
- `scripts/i18n/commands/extract.py` — extract 命令入口
- `scripts/zh-CN.json` — 当前翻译映射表（~1,301 条，纯字符串值）

### 测试
- `tests/unit/` — 现有单元测试
- `tests/conftest.py` — 测试 fixtures

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `translation_map.py` — 已有 v4(字符串) 和 v5(带 "zh" 键) 双格式支持，可扩展 v6 格式
- `replacer.py` — 三级分类（long/medium/short）和逆序替换逻辑已稳定
- `scanner.py` — 信号评分系统可用于扩展组件来源检测

### Established Patterns
- 翻译映射表格式：`{"meta": {...}, "translations": {"en": "zh" | {"zh": "zh_value"}}}`
- 命令实现：`scripts/i18n/commands/` 下独立模块
- JSON 输出：`output_json()` / `output_error()` 统一格式
- 测试模式：`tests/unit/test_xxx.py`

### Integration Points
- translation_map.py 需要扩展以支持带上下文标签的翻译条目
- replacer.py 需要接收上下文信息并按优先级选择翻译
- scanner.py 需要识别字符串在 cli.js 中的组件来源位置

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 04-context-aware-arch*
*Context auto-generated: 2026-04-07*
