#!/bin/bash
# Claude Code i18n 安装脚本
# 将汉化工具文件安装到 ~/.claude/ 目录下

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}[1/3]${NC} 安装汉化引擎和翻译表..."
mkdir -p ~/.claude/scripts/i18n
cp "$SCRIPT_DIR/scripts/localize.py" ~/.claude/scripts/i18n/
cp "$SCRIPT_DIR/scripts/zh-CN.json" ~/.claude/scripts/i18n/
cp "$SCRIPT_DIR/scripts/skip-words.json" ~/.claude/scripts/i18n/
chmod +x ~/.claude/scripts/i18n/localize.py
echo -e "  ${GREEN}✓${NC} scripts/i18n/ 已安装"

echo -e "${BLUE}[2/3]${NC} 安装技能命令..."
mkdir -p ~/.claude/commands/zcf
cp "$SCRIPT_DIR/command/i18n.md" ~/.claude/commands/zcf/
echo -e "  ${GREEN}✓${NC} commands/zcf/i18n.md 已安装"

echo -e "${BLUE}[3/3]${NC} 验证安装..."
if python3 ~/.claude/scripts/i18n/localize.py status > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 汉化引擎运行正常"
else
    echo -e "  警告: 汉化引擎状态检查失败，请确认 Claude Code 已安装"
fi

echo ""
echo -e "${GREEN}安装完成！${NC}"
echo ""
echo "使用方法:"
echo "  在 Claude Code 中输入 /zcf:i18n  一键汉化"
echo "  /zcf:i18n restore                恢复英文"
echo "  /zcf:i18n status                 查看状态"
