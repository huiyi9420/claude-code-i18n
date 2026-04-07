---
phase: 03-integration-quality
plan: 02
subsystem: install-ci
tags: [install-script, skill-command, ci, github-actions]
dependency_graph:
  requires: [03-01]
  provides: [INST-01, INST-02, INST-03, D-05]
  affects: [install.sh, commands/auto-i18n.md, .github/workflows/ci.yml]
tech_stack:
  added: [github-actions]
  patterns: [bash-testing, ci-matrix]
key_files:
  created:
    - .github/workflows/ci.yml
    - tests/test_install.sh
    - scripts/i18n/commands/coverage.py
    - tests/unit/test_coverage_cmd.py
  modified:
    - install.sh
    - commands/auto-i18n.md
    - scripts/i18n/cli.py
decisions:
  - install.sh 使用 for 循环列出命令模块，新增 coverage.py
  - CI 使用 Python 3.10/3.12/3.14 矩阵测试
  - 安装脚本测试使用纯 bash（无额外依赖）
  - coverage 命令在 install.sh 之前完成（03-01 依赖）
metrics:
  duration: 16m
  completed: 2026-04-07T06:56:30Z
  tasks: 2
  files: 7
  tests: 198
---

# Phase 03 Plan 02: 安装脚本 + CI Summary

覆盖命令安装集成 + 技能命令同步 + GitHub Actions CI 流水线

## 执行结果

### Task 1: 更新 install.sh + auto-i18n.md

**Commit:** 29cca64

**变更:**
- install.sh: 在命令模块复制列表中添加 coverage.py（第 91 行）
- install.sh: 在验证文件列表中添加 coverage.py 检查（第 140 行）
- auto-i18n.md: 参数映射表添加 coverage 行
- auto-i18n.md: 添加 coverage 流程说明段落
- tests/test_install.sh: 19 项测试（语法检查、文件存在、变量定义、coverage 集成）

### Task 2: 搭建 GitHub Actions CI

**Commit:** 0958d90

**变更:**
- .github/workflows/ci.yml: CI workflow 文件
- 触发条件: push 到 main/master + PR
- Python 矩阵: 3.10, 3.12, 3.14
- Node.js 22 用于语法验证环境
- 步骤: pytest 测试套件 + install.sh 语法检查

## 前置依赖: 03-01 Coverage 子命令

由于 03-01 计划未执行，先完成了 coverage 子命令的实现:

**Commit:** 5c5e289

**变更:**
- scripts/i18n/commands/coverage.py: 翻译覆盖率报告命令
- scripts/i18n/cli.py: 注册 coverage 子命令到 CLI 框架
- tests/unit/test_coverage_cmd.py: 5 个单元测试
- format_coverage_table: 终端友好纯文本表格输出
- 按长度分类: long(>20) / medium(10-20) / short(<10)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 先执行 03-01 创建 coverage.py**
- **Found during:** Task 1 准备阶段
- **Issue:** install.sh 需要 coverage.py 但 03-01 未执行，文件不存在
- **Fix:** 按 03-01 计划实现了 coverage 子命令（coverage.py + CLI 注册 + 单元测试）
- **Files modified:** scripts/i18n/commands/coverage.py, scripts/i18n/cli.py, tests/unit/test_coverage_cmd.py
- **Commit:** 5c5e289

**2. [Rule 1 - Bug] 测试 JSON 提取失败**
- **Found during:** coverage 命令测试
- **Issue:** cmd_coverage() 先输出表格再输出 JSON，导致 json.loads() 失败
- **Fix:** 测试使用 _extract_json() 辅助函数定位顶层 JSON 对象
- **Files modified:** tests/unit/test_coverage_cmd.py
- **Commit:** 5c5e289

## Verification

全部 5 项验证通过:
1. bash -n install.sh 语法通过
2. grep "coverage.py" install.sh 确认 coverage 模块被安装
3. grep "coverage" commands/auto-i18n.md 确认技能命令同步
4. test -f .github/workflows/ci.yml CI 文件存在
5. bash tests/test_install.sh 安装脚本测试通过 (19/19)

全部 198 个测试通过，无退化。

## Known Stubs

无。所有功能均已完整实现。
