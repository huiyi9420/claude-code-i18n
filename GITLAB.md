# Claude Code 自动中文汉化

> 🇨🇳 Claude Code CLI 一键中文汉化工具。自动提取、自动翻译、自动应用，安全可逆。

本仓库是 [GitHub](https://github.com/huiyi9420/claude-code-i18n) 的镜像，欢迎 Star 和 Fork。

## 功能

- ✅ 一键完成全流程：检测 → 提取 → 翻译 → 应用 → 验证
- ✅ 自动适配新版本：CLI 更新后 `/auto-i18n auto-update` 一键搞定
- ✅ 安全替换：三级策略 + 语法验证 + 失败自动回滚
- ✅ 完全可逆：`/auto-i18n restore` 随时恢复英文
- ✅ Volta 兼容：自动双路径同步
- ✅ 265+ 单元测试，87% 覆盖率

## 快速安装

```bash
git clone https://gitlab.com/你的用户名/claude-auto-i18n.git
cd claude-auto-i18n
bash install.sh
```

## 使用

重启 Claude Code 后：

| 命令 | 功能 |
|------|------|
| `/auto-i18n` | 一键汉化 |
| `/auto-i18n auto-update` | CLI 更新后重新汉化 |
| `/auto-i18n restore` | 恢复英文 |
| `/auto-i18n status` | 查看状态 |

## 详细文档

完整文档请看 [README.md](./README.md)

## 许可证

MIT License
