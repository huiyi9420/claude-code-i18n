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
# Volta 安装（引擎检测路径）
cli_dir=$(dirname "$(find ~/.volta/tools/image/packages/@anthropic-ai/claude-code -name "cli.js" -path "*/lib/node_modules/*" 2>/dev/null | head -1)")
# npm 全局安装
[ -z "$cli_dir" ] && cli_dir=$(dirname "$(find /usr/local/lib/node_modules/@anthropic-ai/claude-code -name "cli.js" 2>/dev/null | head -1)")
```

**重要：Volta 双路径同步**

Volta 实际执行的 CLI 位于 `~/.volta/tools/image/node/<version>/lib/node_modules/@anthropic-ai/claude-code/cli.js`，
但引擎只检测 `packages/` 路径。每次 apply 后必须将翻译后的 cli.js 复制到实际执行路径：

```bash
# 检测 Volta 执行路径
volta_exec_path=$(dirname "$(find ~/.volta/tools/image/node -name "cli.js" -path "*/@anthropic-ai/claude-code/*" 2>/dev/null | head -1)")

# 同步翻译后的 cli.js（apply 后必须执行）
cp "$cli_dir/cli.js" "$volta_exec_path/cli.js" && chmod 755 "$volta_exec_path/cli.js"
```

### 参数 -> 行为映射

| 参数 | 行为 |
|------|------|
| 无 / apply | 一键汉化（检测版本->提取->翻译->应用->验证） |
| restore | 恢复英文原文 |
| status | 查看汉化状态 |
| auto-update | 自我进化：自动提取->规则翻译->合并->应用（一键完成） |
| coverage | 查看翻译覆盖率报告 |
| scan-skills | 扫描已安装技能，报告哪些描述需要汉化 |
| translate-skills | 翻译指定技能的描述 |

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
- **短字符串现在安全支持翻译**：引擎使用 quote-boundary regex（只匹配引号内的字符串），不会误改代码逻辑
- **加载动词列表**（如 Marinating、Pondering、Sock-hopping 等）翻译为"XX中"格式
- **React 拼接字符串**（如 `"Claude Code","'","ll be able to..."`) 需特别关注，翻译被拆分的的部分
- **翻译值中不得包含未转义的 ASCII 双引号**（`"`），必须使用中文引号 `「」` 或中文全角引号代替

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

#### 步骤 5.5：Volta 双路径同步（关键！）

引擎修改 `packages/` 路径下的 cli.js，但 Volta 实际从 `node/<version>/` 路径执行。
**必须同步，否则汉化不生效：**

```bash
# 检测 Volta 实际执行路径
volta_exec=$(dirname "$(find ~/.volta/tools/image/node -name "cli.js" -path "*/@anthropic-ai/claude-code/*" 2>/dev/null | head -1)")
if [ -n "$volta_exec" ] && [ "$volta_exec" != "$cli_dir" ]; then
    cp "$cli_dir/cli.js" "$volta_exec/cli.js"
    chmod 755 "$volta_exec/cli.js"
    echo "已同步到 Volta 执行路径: $volta_exec"
fi
```

#### 步骤 6：后处理补丁（已集成到引擎）

Hook 消息替换、`_8` 键盘提示组件补丁（去掉 chord 显示、action 值翻译）、信任对话框 React 拼接修复、`"Press "` 中文化等后处理补丁已集成到 `apply` 命令中，**无需手动执行**。

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

#### 步骤 10：技能描述汉化（可选）

询问用户是否需要扫描并汉化已安装的技能/工具描述。如果用户确认：

1. 扫描技能描述：
```bash
python3 ~/.claude/scripts/engine.py scan-skills
```

2. 如果有英文描述，输出待翻译列表：
```bash
python3 ~/.claude/scripts/engine.py translate-skills --list
```

3. 对输出的英文描述逐条翻译为中文（遵循同样的翻译原则）

4. 将翻译结果保存为 JSON 文件并应用：
```bash
python3 ~/.claude/scripts/engine.py translate-skills --apply /tmp/skill-translations.json
```

JSON 格式为：
```json
[
  {"name": "skill-name", "path": "/path/to/SKILL.md", "description": "English desc", "translated": "中文描述"}
]
```

5. 汇报结果：已翻译数量、跳过数量

---

### scan-skills 流程

```bash
python3 ~/.claude/scripts/engine.py scan-skills
```

扫描 `~/.claude/skills/` 和 `~/.claude/plugins/marketplaces/` 下的所有 SKILL.md 文件，输出 JSON 报告：
- `summary`: 总数、中文数、英文数、按来源分组统计
- `skills`: 每个技能的名称、路径、描述、语言标识（zh/en）、来源

---

### translate-skills 流程

```bash
# 输出待翻译列表
python3 ~/.claude/scripts/engine.py translate-skills --list [--source all] [--skill name1,name2]

# 应用翻译
python3 ~/.claude/scripts/engine.py translate-skills --apply translations.json
```

`--source` 支持的值：`all`（默认）、`user_skills`、`ecc_plugin`、`minimax_plugin`、`official_plugin`

**工作流程：**
1. `--list` 输出英文描述列表
2. AI 逐条翻译
3. 生成翻译 JSON 文件
4. `--apply` 批量写入 SKILL.md 的 frontmatter description 字段

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
| 汉化后 CLI 界面仍是英文 | 检查 Volta 双路径同步（步骤 5.5），确保 `node/<version>/` 路径已更新 |
| 语法验证失败 | 自动回滚，检查翻译值中是否有未转义的双引号 |
| 找不到 cli.js | 检查 Volta/npm 安装路径，或设置 `CLAUDE_I18N_CLI_DIR` 环境变量 |
| 想恢复英文 | 执行 `/auto-i18n restore`，恢复后也需同步双路径 |

### 引擎架构（v3.1）

**三级替换策略（所有级别使用安全匹配）：**
- **Long（>20 chars）**：全局 `str.replace`，精确匹配
- **Medium（11-20 chars）**：quote-boundary regex `(?<=[\'"])en(?=[\'"])`，只匹配引号内的字符串
- **Short（<=10 chars）**：同样使用 quote-boundary regex，安全翻译 UI 标签（如"No, exit"）

**安全性保障：**
- 替换后 `node --check` 验证语法（在 /tmp 中验证，避免 macOS 路径问题）
- 语法失败自动回滚到备份
- 备份使用 SHA-256 校验和验证完整性
