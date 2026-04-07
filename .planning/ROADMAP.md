# Roadmap: Claude Code i18n

## Milestones

- ✅ **v3.0 完全重写** — Phases 1-3 (shipped 2026-04-07) → [详情](milestones/v3.0-ROADMAP.md)
- 📋 **v3.1 翻译增强** — Phases 4-6 (active)

## Phases

- [ ] **Phase 4: 上下文感知架构** — 翻译映射表支持上下文标签，替换引擎按上下文优先级选择翻译，extract 标注组件来源
- [ ] **Phase 5: 翻译扩充与质量保障** — 翻译条目扩充至 2,500+，覆盖率 80%+，高频 95%+，质量验证机制
- [ ] **Phase 6: CI 覆盖率回归检测** — PR 不允许翻译覆盖率低于主分支

## Phase Details

### Phase 4: 上下文感知架构

**Goal**: 翻译映射表和替换引擎支持同一英文字符串在不同组件中拥有不同中文翻译，用户运行汉化后各界面组件的翻译更准确自然

**Depends on**: Phase 3（v3.0 完成，三级替换引擎已就绪）

**Requirements**: CTX-01, CTX-02, CTX-03

**Success Criteria**（完成后必须为真）:
1. 翻译映射表 zh-CN.json 中可以为同一个英文字符串定义多个带上下文标签的翻译条目（如 `"Error"` 在 `/tools` 组件中翻译为"工具错误"，在 `/auth` 组件中翻译为"认证错误"）
2. 运行 `apply` 命令时，替换引擎根据 cli.js 中字符串的位置上下文（文件区块/函数范围）优先选择精确匹配的上下文翻译，无精确匹配时回退到全局默认翻译
3. 运行 `extract` 命令时，每个候选字符串的输出包含其所在组件来源信息（file 区块标识、section 名称、函数名），帮助人工翻译时理解上下文
4. 现有的无上下文标签翻译条目（v3.0 格式）无需修改即可正常工作（向后兼容）

**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — 翻译映射表 v6 格式扩展 + 上下文检测模块
- [ ] 04-02-PLAN.md — 上下文感知替换引擎
- [ ] 04-03-PLAN.md — extract 组件来源标注

### Phase 5: 翻译扩充与质量保障

**Goal**: 用户运行汉化后，Claude Code 界面的可见文本 80% 以上被翻译为中文，高频交互文本几乎全部翻译，且翻译质量经过自动化验证

**Depends on**: Phase 4（上下文感知架构就绪，可高效翻译高频字符串）

**Requirements**: COV-01, COV-02, COV-03, CTX-04

**Success Criteria**（完成后必须为真）:
1. 翻译映射表包含 2,500 条及以上翻译条目（从当前 1,301 条大幅扩充）
2. 运行 `coverage` 命令显示总体翻译覆盖率 >= 80%
3. 运行 `coverage` 命令显示高频可见字符串（score >= 2）的翻译覆盖率 >= 95%
4. 翻译质量验证机制能自动检测并报告三类问题：中英混杂的翻译条目、同一英文对应多个不一致的中文翻译、格式占位符（如 `%s`, `{0}`, `${var}`）在翻译中丢失
5. 运行 `apply` 命令后 Claude Code 的日常使用界面（提示词、状态消息、错误提示、操作反馈）全部显示中文

**Plans**: 3 plans

Plans:
- [ ] 04-01-PLAN.md — 翻译映射表 v6 格式扩展 + 上下文检测模块
- [ ] 04-02-PLAN.md — 上下文感知替换引擎
- [ ] 04-03-PLAN.md — extract 组件来源标注

### Phase 6: CI 覆盖率回归检测

**Goal**: 每次 PR 提交自动检测翻译覆盖率是否下降，防止代码变更意外导致覆盖率回退

**Depends on**: Phase 5（覆盖率达标后才有回归基线）

**Requirements**: COV-04

**Success Criteria**（完成后必须为真）:
1. CI 流水线中新增翻译覆盖率检查步骤，自动运行 `coverage` 命令获取当前覆盖率
2. PR 提交时如果翻译覆盖率低于主分支基线，CI 检查失败并给出明确的覆盖率对比报告
3. 覆盖率检查结果以 JSON 格式输出，可供 CI 解析和展示
4. CI 中翻译覆盖率检查在 60 秒内完成（不影响整体 CI 效率）

**Plans**: 3 plans

Plans:
- [ ] 04-01-PLAN.md — 翻译映射表 v6 格式扩展 + 上下文检测模块
- [ ] 04-02-PLAN.md — 上下文感知替换引擎
- [ ] 04-03-PLAN.md — extract 组件来源标注

## Coverage Map

| Requirement | Phase | Status |
|-------------|-------|--------|
| COV-01 | Phase 5 | Pending |
| COV-02 | Phase 5 | Pending |
| COV-03 | Phase 5 | Pending |
| COV-04 | Phase 6 | Pending |
| CTX-01 | Phase 4 | Pending |
| CTX-02 | Phase 4 | Pending |
| CTX-03 | Phase 4 | Pending |
| CTX-04 | Phase 5 | Pending |

**Coverage:** 8/8 requirements mapped (100%)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Safety | v3.0 | 3/3 | Complete | 2026-04-05 |
| 2. Core Engine | v3.0 | 4/4 | Complete | 2026-04-05 |
| 3. Integration & Quality | v3.0 | 3/3 | Complete | 2026-04-07 |
| 4. 上下文感知架构 | v3.1 | 0/? | Not started | - |
| 5. 翻译扩充与质量保障 | v3.1 | 0/? | Not started | - |
| 6. CI 覆盖率回归检测 | v3.1 | 0/? | Not started | - |

---

_This roadmap is consumed by `/gsd:plan-phase` for phase decomposition._
_Last updated: 2026-04-07_
