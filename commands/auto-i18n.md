---
description: 'Claude Code CLI 中文汉化（一键应用/更新/恢复/自我进化）'
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

$ARGUMENTS

## Claude Code CLI 汉化工具

你是 Claude Code CLI 的中文汉化助手。根据参数执行操作，**无参数时执行一键汉化**。

### 路径约定

| 项目 | 路径 |
|------|------|
| 汉化引擎 | `~/.claude/scripts/engine.py` |
| 翻译映射表 | `~/.claude/scripts/i18n/zh-CN.json` |
| 跳过词表 | `~/.claude/scripts/i18n/skip-words.json` |
| 自动翻译词典 | `~/.claude/scripts/i18n/auto-translate-dict.json` |
| 提取快照 | `~/.claude/scripts/i18n/extract-snapshot.json` |

### CLI 安装路径检测

```bash
# Volta 安装
cli_dir=$(dirname "$(find ~/.volta/tools/image/packages/@anthropic-ai/claude-code -name "cli.js" -path "*/lib/node_modules/*" 2>/dev/null | head -1)")
# npm 全局安装
[ -z "$cli_dir" ] && cli_dir=$(dirname "$(find /usr/local/lib/node_modules/@anthropic-ai/claude-code -name "cli.js" 2>/dev/null | head -1)")
```

### 参数 -> 行为映射

| 参数 | 行为 |
|------|------|
| 无 / apply | 一键汉化（检测版本->提取->翻译->应用->验证） |
| restore | 恢复英文原文 |
| status | 查看汉化状态 |
| auto-update | 自我进化：自动提取->规则翻译->合并->应用（一键完成） |
| coverage | 查看翻译覆盖率报告 |

---

### 一键汉化流程（无参数 / apply）

完整执行以下步骤，**中间遇到错误立即停止并告知用户**：

#### 步骤 0：版本变更检测（关键！）

```bash
# 获取当前 CLI 版本
current_version=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

# 获取映射表记录的版本
lang_version=$(python3 -c "import json; print(json.load(open('$HOME/.claude/scripts/i18n/zh-CN.json')).get('_meta',{}).get('cli_version',''))" 2>/dev/null)

# 检查是否有备份
backup_exists=$(test -f "$cli_dir/cli.bak.en.js" && echo "yes" || echo "no")
```

**版本变更处理逻辑：**

1. **版本相同 + 已有备份** -> 跳到步骤 2（正常汉化）
2. **版本不同 + 有旧备份** -> 删除旧备份，重新汉化
   ```bash
   rm -f "$cli_dir/cli.bak.en.js"
   ```
3. **版本不同 + 无备份** -> 直接从新版本创建备份
4. **版本相同 + 无备份** -> 正常汉化（apply 会自动创建备份）

版本变更时告知用户："检测到 CLI 版本从 {旧版本} 更新到 {新版本}，将重新汉化"

更新映射表的 `_meta.cli_version` 为当前版本。

#### 步骤 1：获取当前状态

```bash
python3 ~/.claude/scripts/engine.py status
python3 ~/.claude/scripts/engine.py version
```

记录 `version` 和 `localized` 状态。

#### 步骤 2：提取新字符串

```bash
python3 ~/.claude/scripts/engine.py extract
```

解析输出 JSON，取 `strong` 数组中的字符串。

#### 步骤 3：AI 翻译

对提取出的新字符串（`strong` 列表），逐条翻译为中文：

**翻译原则：**
- 简洁、符合中文习惯
- 保留变量占位符如 `{0}`、`%s`、`${var}` 不翻译
- 保留命令名如 `/login`、`/config` 不翻译
- 保留专有名词如 `MCP`、`API`、`Git` 不翻译
- 技术术语保留英文或用通用中文译法
- **短字符串（<10字符）需谨慎，只在明确是 UI 文本时才翻译**
- **加载动词列表**（如 Marinating、Pondering、Sock-hopping 等）翻译为"XX中"格式
- **React 拼接字符串**（如 `"Claude Code","'","ll be able to..."`) 需特别关注，翻译被拆分的部分

**跳过规则：** 遇到以下情况不翻译，记入 skip-words.json：
- 看起来是代码标识符/类名/方法名
- 是第三方库的内部日志
- 是协议/标准的技术描述
- 不确定是否为用户可见的 UI 文本
- 代码逻辑状态值（如 `status: "running"`、`"completed"`、`"failed"`）

**特别注意：不可翻译的状态值**
以下字符串是 JavaScript 状态机的逻辑判断值，**绝对不能翻译**，否则会破坏功能：
- `"running"`、`"pending"`、`"completed"`、`"failed"`、`"killed"`、`"idle"`、`"starting"`、`"stopped"`
- `"in_process_teammate"`、`"local_bash"`、`"local_agent"`、`"remote_agent"`、`"dream"`、`"local_workflow"`、`"monitor_mcp"`
- `"leader"`、`"foreground"`（作为 action 值时）

#### 步骤 4：更新映射表

将新翻译合并到 `~/.claude/scripts/i18n/zh-CN.json`：
- 读取现有 JSON
- 在 `translations` 对象末尾追加新条目
- 更新 `_meta.cli_version` 为当前版本
- 更新 `_meta.version` 递增
- 写入文件

将跳过的字符串记入 `~/.claude/scripts/i18n/skip-words.json` 的 `skip` 数组。

#### 步骤 5：应用汉化

```bash
python3 ~/.claude/scripts/engine.py apply
```

解析输出的 JSON，确认 `ok: true`。

#### 步骤 6：Hook UI 消息汉化（已集成到引擎）

Hook 相关的替换已集成到 `apply` 命令中，**无需手动执行**。

#### 步骤 7：语法验证

```bash
node --check "$cli_js"
```

如果验证失败，立即恢复：
```bash
python3 ~/.claude/scripts/engine.py restore
```

#### 步骤 8：功能验证

```bash
claude -p "回复两个字：成功" 2>&1
```

确认输出包含"成功"且无报错。

#### 步骤 9：汇报结果

向用户展示：
- 当前 CLI 版本
- 版本变更（如有）
- 新提取的字符串数量
- 新翻译数量 / 跳过数量
- 总替换处数
- 语法验证结果
- 功能测试结果
- 提醒：请重启 Claude Code 查看效果

---

### auto-update 流程（自我进化）

```bash
python3 ~/.claude/scripts/engine.py auto-update
```

一键完成：版本检测 -> 提取新字符串 -> 规则自动翻译 -> 合并映射表 -> 应用汉化 -> Hook 替换 -> 语法验证。

适用于 CLI 更新后重新汉化的场景。输出 JSON 报告包含：
- `version`: 旧/新版本及变更状态
- `extraction`: 候选字符串数量及 diff
- `translation`: 自动翻译数、需审核数
- `apply`: 替换统计
- `review_items`: 需人工审核的条目

---

### restore 流程

```bash
python3 ~/.claude/scripts/engine.py restore
```

确认恢复成功后告知用户。

---

### status 流程

```bash
python3 ~/.claude/scripts/engine.py status
```

以表格形式展示：
- CLI 版本
- 汉化状态（已汉化/未汉化）
- 映射表条目数
- 映射表对应的 CLI 版本
- 备份文件状态

---

### coverage 流程

```bash
python3 ~/.claude/scripts/engine.py coverage
```

输出翻译覆盖率表格和 JSON 数据，显示已翻译/未翻译/跳过的条目数量和百分比，按字符串长度（长>20/中10-20/短<10）分组显示覆盖率。

---

### 故障排除

| 问题 | 解决方案 |
|------|---------|
| CLI 更新后汉化失效 | 执行 `/auto-i18n auto-update` 自动重新汉化 |
| 语法验证失败 | 自动回滚，检查 Hook 替换规则（hooks.py） |
| 找不到 cli.js | 检查 Volta/npm 安装路径，或设置 `CLAUDE_I18N_CLI_DIR` 环境变量 |
| 想恢复英文 | 执行 `/auto-i18n restore` |
