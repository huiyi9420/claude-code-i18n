# Roadmap: Claude Code i18n 完全重写

## Overview

对 Claude Code CLI 汉化工具进行完全重写。三个阶段依次交付：(1) 安全基础层 -- 确保备份纯净、路径正确、原子写入，解决 v3.0 最严重的备份污染问题；(2) 核心引擎 -- 三级替换策略、字符串提取、版本检测，实现安全的一键汉化/恢复；(3) 集成与质量 -- 安装脚本、完整测试覆盖、交付可部署的重写版本。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Safety** - 备份管理器、路径检测、原子写入、CLI 框架 -- 解决备份污染这一最严重问题
- [ ] **Phase 2: Core Engine** - 三级替换引擎、提取器、验证器、版本检测、状态命令 -- 实现核心汉化/恢复能力
- [ ] **Phase 3: Integration & Quality** - 安装脚本、单元测试、集成测试 -- 交付可部署的完整重写版本

## Phase Details

### Phase 1: Foundation & Safety
**Goal**: 用户可以在任何安装方式下安全地创建和恢复纯净英文备份，备份零中文污染且不可被意外篡改
**Depends on**: Nothing (first phase)
**Requirements**: PATH-01, PATH-02, PATH-03, PATH-04, PATH-05, BAK-01, BAK-02, BAK-03, BAK-04, BAK-05, BAK-06, BAK-07
**Success Criteria** (what must be TRUE):
  1. 用户运行 `python engine.py status` 能自动检测到 Claude Code CLI 安装路径并输出 JSON 格式的状态信息
  2. 用户首次汉化时，工具自动从 cli.js 创建纯净英文备份（零中文字符），备份文件为只读且附带 SHA-256 校验文件
  3. 用户运行 `python engine.py restore` 后，cli.js 恢复为 100% 纯英文（零中文字符残留），且恢复前自动校验备份哈希
  4. 当 CLI 未安装或路径无效时，用户看到清晰的错误信息和安装指引（非 Python traceback）
  5. 所有文件写入操作均为原子性（断电或中断不会留下损坏文件）
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md -- Path Resolver: 5 级级联路径检测 (env/config/volta/npm/common) + 路径验证 + 常量定义 + 单元测试
- [ ] 01-02-PLAN.md -- Backup Manager: 不可变备份管理器 + SHA-256 校验 + CJK 纯净性检查 + 原子写入工具 + 单元测试
- [ ] 01-03-PLAN.md -- CLI Framework + Restore: argparse 子命令路由 + restore/status/version 命令 + engine.py 入口 + 单元测试

### Phase 2: Core Engine
**Goal**: 用户运行一条命令即可安全地将 Claude Code CLI 界面汉化为中文，替换后语法正确、失败自动回滚，且能从纯净源提取新的可翻译字符串
**Depends on**: Phase 1
**Requirements**: APPLY-01, APPLY-02, APPLY-03, APPLY-04, APPLY-05, APPLY-06, APPLY-07, APPLY-08, APPLY-09, APPLY-10, EXTRACT-01, EXTRACT-02, EXTRACT-03, EXTRACT-04, EXTRACT-05, EXTRACT-06, VER-01, VER-02, VER-03, VER-04, STATUS-01, STATUS-02, STATUS-03, STATUS-04, MAP-01, MAP-02, MAP-03, MAP-04, PLAT-01, PLAT-02, PLAT-03
**Success Criteria** (what must be TRUE):
  1. 用户运行 `python engine.py apply` 后，cli.js 中的长字符串和中等字符串被准确替换为中文，替换完成输出 JSON 格式的结果（替换数/跳过数/失败数）
  2. 每次替换后自动执行 `node --check` 验证，语法错误时自动从纯净备份回滚，用户看到明确的错误报告
  3. 用户运行 `python engine.py extract` 获得新版本 cli.js 中的可翻译字符串候选列表（JSON 格式，含评分和出现次数），列表中不包含任何中文字符或代码标识符
  4. 当 Claude Code 更新后（版本号变化），工具自动检测版本变更、删除旧备份并从新 cli.js 重新创建纯净备份，向用户报告版本变化（旧版本号 -> 新版本号）
  5. 用户运行 `python engine.py status` 能看到当前 CLI 版本、汉化状态、翻译条目数、备份完整性的 JSON 输出
**Plans**: TBD

Plans:
- [ ] 02-01: Translation Map + Scanner -- JSON 映射表加载/校验 + 字符串扫描器（信号评分 + 噪声过滤）
- [ ] 02-02: Replacement Engine -- 三级替换策略（长/中/短）+ 逆序替换 + Hook 精确替换
- [ ] 02-03: Verification + Version -- node --check 验证 + 回滚 + 版本检测 + 版本变更处理
- [ ] 02-04: Extract + Status Commands -- extract 命令 + status/version 命令 + 跨平台支持

### Phase 3: Integration & Quality
**Goal**: 用户可以通过安装脚本一键部署汉化工具，且工具经过完整测试覆盖，达到可发布质量
**Depends on**: Phase 2
**Requirements**: INST-01, INST-02, INST-03, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. 用户运行 `bash install.sh` 后，引擎、翻译映射表、跳过词表、技能命令全部安装到 `~/.claude/` 目录，安装前自动检查 Python 3 和 Node.js 是否可用
  2. 安装后用户通过技能命令（zcf/i18n.md）能调用完整的汉化/恢复/提取/状态功能，技能命令描述与引擎实际能力一致
  3. 路径解析、备份管理、字符串扫描、替换引擎、提取命令均有对应单元测试，总测试覆盖率 >= 80%
  4. 完整的 apply -> verify -> restore -> verify 往返测试通过，确认汉化和恢复的端到端正确性
**Plans**: TBD

Plans:
- [ ] 03-01: Installation Script -- install.sh + 技能命令同步 + 环境检查
- [ ] 03-02: Unit Tests -- 路径/备份/扫描/替换/提取各模块单元测试
- [ ] 03-03: Integration Tests + Coverage -- 端到端往返测试 + 覆盖率验证

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Safety | 0/3 | Planning complete | - |
| 2. Core Engine | 0/4 | Not started | - |
| 3. Integration & Quality | 0/3 | Not started | - |
