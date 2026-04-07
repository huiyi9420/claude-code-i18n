# Phase 3: Integration & Quality - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 03-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 03-integration-quality
**Areas discussed:** 翻译覆盖率验证, zh-CN.json 补充策略, 发布标准定义

---

## 翻译覆盖率验证

| Option | Description | Selected |
|--------|-------------|----------|
| 集成到 apply 后输出 | 在 apply 命令中追加覆盖率统计 | |
| 独立 coverage 命令 | 新增 coverage 子命令，专门输出覆盖率表格 | ✓ |
| 手动判断 | 用 extract 命令自行判断 | |

**User's choice:** 独立 coverage 命令
**Notes:** 输出格式为终端友好的表格形式，不是纯 JSON。覆盖率目标暂不定死，先有量化能力。

## zh-CN.json 补充策略

| Option | Description | Selected |
|--------|-------------|----------|
| Extract + 人工筛选 | extract 扫描 → 人工筛选翻译 | |
| Extract + 自动翻译 + 审核 | extract → auto-translate → 自动写入 → 后续验证 | ✓ |
| 纯手动添加 | 发现缺什么手动加什么 | |

**User's choice:** Extract + 自动翻译 + 审核
**Notes:** 自动写入 zh-CN.json，后续通过 coverage 命令验证效果。

### 补充范围

| Option | Description | Selected |
|--------|-------------|----------|
| 当前版本补全 | 补全当前 CLI + coverage 命令 | |
| 当前 + CI 自动化 | 一步到位含 CI 流水线 | ✓ (后改为 A) |

**Initial choice:** B (当前 + CI)
**Revised to:** A (当前补全) — 用户在 CI 平台选择时回退，最终锁定当前补全 + coverage

## 发布标准定义

| Option | Description | Selected |
|--------|-------------|----------|
| 测试通过 + 覆盖率 >= 80% | 193+ 测试全通过 | ✓ |
| coverage 命令可用 | 新增命令输出可量化覆盖率表格 | ✓ |
| 端到端往返验证 | apply → verify → restore → verify 在真实 CLI 通过 | ✓ |
| 安装脚本验证 | install.sh 在干净环境执行成功 | ✓ |

**User's choice:** 全部四项
**Notes:** 四项都是必须满足的发布门槛。

## Claude's Discretion

- coverage 命令的表格列设计
- 自动翻译词典的更新策略
- 测试用例具体设计

## Deferred Ideas

- CI 流水线搭建 — 留到 v2 (COV/CI/SMART 系列)
- 覆盖率阈值锁定 — 先量化再定目标
- 多语言支持 — 当前仅中文

---

*Phase: 03-integration-quality*
*Discussion completed: 2026-04-07*
