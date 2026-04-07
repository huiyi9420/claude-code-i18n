# Claude Code auto-i18n

一键将 Claude Code CLI 终端界面汉化为中文。CLI 更新后执行 `/auto-i18n` 即可自动重新汉化。

## 功能特性

- **一键汉化** — `/auto-i18n` 完成提取、翻译、应用、验证全流程
- **自我进化** — CLI 更新后 `/auto-i18n auto-update` 自动适配新版本
- **规则引擎** — 内置 170+ 词典条目 + UI 模板 + 动词模式自动翻译
- **安全替换** — 三级替换策略 + Hook 替换 + 语法验证 + 失败自动回滚
- **可逆操作** — `/auto-i18n restore` 随时恢复英文原文

## 快速开始

### 安装

```bash
git clone https://github.com/huiyi9420/claude-code-i18n.git
cd claude-code-i18n
bash install.sh
```

### 使用

在 Claude Code 中输入：

| 命令 | 功能 |
|------|------|
| `/auto-i18n` | 一键汉化（提取→翻译→应用→验证） |
| `/auto-i18n auto-update` | CLI 更新后自动重新汉化 |
| `/auto-i18n restore` | 恢复英文原文 |
| `/auto-i18n status` | 查看汉化状态 |

### 命令行（不依赖技能命令）

```bash
python3 ~/.claude/scripts/engine.py apply       # 应用汉化
python3 ~/.claude/scripts/engine.py auto-update  # 自我进化
python3 ~/.claude/scripts/engine.py restore      # 恢复英文
python3 ~/.claude/scripts/engine.py status       # 查看状态
python3 ~/.claude/scripts/engine.py extract      # 提取新字符串
```

## 工作原理

### 架构

```
备份(cli.bak.en.js) → 扫描候选字符串 → 规则自动翻译 → AI 翻译剩余
    → 三级替换(长/中/短) → Hook 替换 → 语法验证 → 写入 cli.js
```

### 替换策略

| 长度 | 策略 | 说明 |
|------|------|------|
| > 20 字符 | 全局替换 | 精度高，误伤概率极低 |
| 10-20 字符 | 引号上下文替换 | 只替换引号内的出现 |
| < 10 字符 | 边界感知替换 | 限制替换数量上限 + skip words |

### 自我进化流程

`auto-update` 一键编排：

1. 版本变更检测（自动重建备份）
2. 从纯净备份扫描新字符串
3. 与上次快照 diff（新增/变更/移除）
4. 规则引擎自动翻译高置信度字符串
5. 低置信度字符串标记人工审核
6. 合并翻译映射表
7. 应用汉化 + Hook 替换
8. `node --check` 语法验证（失败自动回滚）

## 项目结构

```
claude-code-i18n/
├── commands/
│   └── auto-i18n.md          # Claude Code 技能命令
├── scripts/
│   ├── engine.py              # CLI 入口
│   ├── zh-CN.json             # 中英翻译映射表
│   ├── skip-words.json        # 跳过词列表
│   ├── auto-translate-dict.json # 自动翻译词典
│   └── i18n/                  # 引擎模块
│       ├── cli.py             # argparse 子命令路由
│       ├── config/            # 常量、路径检测
│       ├── io/                # 备份、文件IO、翻译映射、快照
│       ├── core/              # 扫描、替换、验证、Hook、自动翻译
│       ├── filters/           # 噪声过滤、UI 指示器
│       └── commands/          # apply/extract/status/restore/auto-update
├── tests/                     # pytest 测试套件
├── install.sh                 # 安装脚本
└── README.md
```

## 自定义翻译

编辑 `~/.claude/scripts/i18n/zh-CN.json` 的 `translations` 字段：

```json
{
  "_meta": { "version": "4.0.0", "cli_version": "2.1.92" },
  "translations": {
    "English text": "中文翻译"
  }
}
```

## 系统要求

- macOS / Linux
- Python 3.8+
- Node.js（语法验证需要）
- Claude Code CLI

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| CLI 更新后汉化失效 | `/auto-i18n auto-update` |
| 想恢复英文 | `/auto-i18n restore` |
| 找不到 cli.js | 设置 `export CLAUDE_I18N_CLI_DIR=/path/to/cli/dir` |
| 语法验证失败 | 自动回滚，查看 hooks.py 中的替换规则 |

## 贡献

欢迎提交 PR！主要贡献方式：

1. **翻译改进** — 修改 `scripts/zh-CN.json` 中的翻译
2. **词典扩展** — 添加 `scripts/auto-translate-dict.json` 中的短语
3. **Bug 修复** — 提交 issue 或 PR

开发：`python3 -m pytest tests/ -v` 运行测试套件（192 测试，87% 覆盖率）

## License

MIT
