# Claude Code CLI 中文汉化工具

一键将 Claude Code CLI 终端界面汉化为中文，支持版本更新后自动提取新字符串并翻译。

## 功能特性

- **一键汉化** — `/zcf:i18n` 一条命令完成提取、翻译、应用、验证全流程
- **版本自适应** — Claude Code 更新后自动提取新增 UI 字符串
- **AI 智能翻译** — 由 Claude 自动翻译新发现的英文字符串
- **安全替换** — 三级替换策略 + 语法验证 + 失败自动回滚
- **可逆操作** — 随时恢复英文原文

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/zhaolulu/claude-code-i18n.git
cd claude-code-i18n

# 运行安装脚本
bash install.sh
```

### 使用

在 Claude Code 中使用 `/zcf:i18n` 命令：

| 命令 | 功能 |
|------|------|
| `/zcf:i18n` | 一键汉化（提取→翻译→应用→验证） |
| `/zcf:i18n apply` | 应用已有翻译 |
| `/zcf:i18n restore` | 恢复英文原文 |
| `/zcf:i18n status` | 查看汉化状态 |

### 手动使用（不依赖技能命令）

```bash
# 应用汉化
python3 scripts/localize.py apply

# 恢复英文
python3 scripts/localize.py restore

# 查看状态
python3 scripts/localize.py status

# 提取新字符串
python3 scripts/localize.py extract
```

## 项目结构

```
claude-code-i18n/
├── README.md                  # 本文件
├── install.sh                 # 安装脚本
├── command/
│   └── i18n.md                # Claude Code 技能命令定义
└── scripts/
    ├── localize.py            # 汉化引擎 v3.0
    ├── zh-CN.json             # 中英翻译映射表
    └── skip-words.json        # 用户跳过的字符串列表
```

## 工作原理

### 替换策略

汉化引擎根据字符串长度采用不同替换策略，最大限度避免误替换代码内部逻辑：

| 长度 | 策略 | 说明 |
|------|------|------|
| > 20 字符 | 全局替换 | 精度高，误伤概率极低 |
| 10-20 字符 | 引号上下文替换 | 只替换引号内的出现 |
| < 10 字符 | 边界感知替换 | 限制替换数量上限 |

### 安全机制

- 每次应用前自动备份英文原文（`cli.bak.en.js`）
- 应用后执行 `node --check` 语法验证
- 验证失败自动回滚到英文原文
- 跳过通用短词（Yes/No/Error 等）避免破坏逻辑

### 版本更新流程

当 Claude Code 更新后：

1. `localize.py extract` 从英文备份中提取新的用户可见字符串
2. 使用强/弱信号关键词过滤，只保留真正的 UI 文本
3. AI 自动翻译并更新 `zh-CN.json` 映射表
4. 应用新的翻译并验证

## 自定义翻译

编辑 `scripts/zh-CN.json` 中的 `translations` 字段即可添加或修改翻译：

```json
{
  "_meta": { ... },
  "translations": {
    "English text": "中文翻译",
    ...
  }
}
```

## 系统要求

- macOS / Linux
- Python 3.6+
- Node.js（用于语法验证）
- Claude Code CLI（通过 Volta 安装）

## 默认路径

汉化引擎默认查找以下路径：

```
~/.volta/tools/image/packages/@anthropic-ai/claude-code/lib/node_modules/@anthropic-ai/claude-code/cli.js
```

如安装路径不同，需修改 `scripts/localize.py` 中的 `CLI_DIR` 变量。

## License

MIT
