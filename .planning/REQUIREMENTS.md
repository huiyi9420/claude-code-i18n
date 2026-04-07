# Requirements: Claude Code i18n v3.1 — 翻译增强

**Defined:** 2026-04-07
**Milestone:** v3.1
**Core Value:** 用户运行一条命令，Claude Code CLI 的全部用户可见界面变成准确、自然的中文，版本更新后自动适配。

## v3.1 Requirements

### Coverage — 翻译覆盖率提升

- [x] **COV-01**: 翻译条目数 ≥ 2,500（当前 1,301），覆盖用户可见的高频 UI 字符串
- [x] **COV-02**: 总体翻译覆盖率 ≥ 80%（当前 48.0%，按 coverage 命令统计）
- [x] **COV-03**: 用户高频可见字符串覆盖率 ≥ 95%（score ≥ 2 的候选全部翻译）
- [ ] **COV-04**: CI 翻译覆盖率回归检测 — PR 不允许覆盖率低于主分支

### Context — 上下文感知翻译

- [x] **CTX-01**: 翻译映射表支持上下文标签（同一英文在不同组件可有不同中文翻译）
- [x] **CTX-02**: 替换引擎解析上下文标签，按优先级选择翻译（精确上下文 > 全局默认）
- [x] **CTX-03**: extract 命令标注候选字符串的组件来源（file/section/function 级别）
- [x] **CTX-04**: 翻译质量验证机制 — 自动检测中英混杂、同义不一致、格式占位符丢失

## Out of Scope

| Feature | Reason |
|---------|--------|
| Aho-Corasick 引擎 | 翻译条目 <3000 时标准 re 足够，性能非瓶颈 |
| 多语言支持（日/韩） | 当前仅中文，架构已预留 |
| 翻译管理后台/Web UI | 规模不需要 |
| 自动 AI 翻译（LLM API） | 质量控制需要人工审核，且违反零外部依赖约束 |
| prefix_suffix_match 规则 | v3.0 验证质量极差，已弃用 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COV-01 | Phase 5 | Complete |
| COV-02 | Phase 5 | Complete |
| COV-03 | Phase 5 | Complete |
| COV-04 | Phase 6 | Pending |
| CTX-01 | Phase 4 | Complete |
| CTX-02 | Phase 4 | Complete |
| CTX-03 | Phase 4 | Complete |
| CTX-04 | Phase 5 | Complete |

**Coverage:**
- v3.1 requirements: 8 (2 categories)
- Mapped to phases: 8/8 (100%)

---
*Requirements defined: 2026-04-07*
*Traceability updated: 2026-04-07 — Roadmap created*
