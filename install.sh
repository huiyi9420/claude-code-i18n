#!/usr/bin/env bash
# install.sh — Claude Code i18n Engine Installer
#
# Copies engine, translation map, skip words, and skill command to ~/.claude/
# Checks for Python 3 and Node.js availability.
#
# Usage: bash install.sh

set -euo pipefail

# --- Configuration ---
CLAUDE_DIR="${HOME}/.claude"
TARGET_DIR="${CLAUDE_DIR}/scripts/i18n"
SKILL_DIR="${CLAUDE_DIR}/commands/zcf"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Colors ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; exit 1; }

echo -e "${BLUE}[1/4]${NC} 检查环境..."

# Check Python 3 (INST-03)
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python ${PY_VERSION}"
else
    error "Python 3 未安装。请先安装: https://www.python.org/downloads/"
fi

# Check Node.js (INST-03)
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    info "Node.js ${NODE_VERSION}"
else
    error "Node.js 未安装（语法验证需要）。请先安装 Node.js"
fi

# Check Claude Code CLI
if command -v claude &>/dev/null; then
    info "Claude Code CLI 已安装"
else
    warn "Claude Code CLI 未找到。安装后汉化才能生效: npm install -g @anthropic-ai/claude-code"
fi

# --- Installation (INST-01) ---

echo -e "${BLUE}[2/4]${NC} 安装汉化引擎..."

mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/io"
mkdir -p "${TARGET_DIR}/core"
mkdir -p "${TARGET_DIR}/filters"
mkdir -p "${TARGET_DIR}/commands"

# Copy engine modules
cp "${SCRIPT_DIR}/scripts/i18n/__init__.py" "${TARGET_DIR}/"
cp "${SCRIPT_DIR}/scripts/i18n/cli.py" "${TARGET_DIR}/"
cp "${SCRIPT_DIR}/scripts/i18n/config/__init__.py" "${TARGET_DIR}/config/"
cp "${SCRIPT_DIR}/scripts/i18n/config/constants.py" "${TARGET_DIR}/config/"
cp "${SCRIPT_DIR}/scripts/i18n/config/paths.py" "${TARGET_DIR}/config/"
cp "${SCRIPT_DIR}/scripts/i18n/io/__init__.py" "${TARGET_DIR}/io/"
cp "${SCRIPT_DIR}/scripts/i18n/io/backup.py" "${TARGET_DIR}/io/"
cp "${SCRIPT_DIR}/scripts/i18n/io/file_io.py" "${TARGET_DIR}/io/"
cp "${SCRIPT_DIR}/scripts/i18n/io/translation_map.py" "${TARGET_DIR}/io/"
cp "${SCRIPT_DIR}/scripts/i18n/core/__init__.py" "${TARGET_DIR}/core/"
cp "${SCRIPT_DIR}/scripts/i18n/core/scanner.py" "${TARGET_DIR}/core/"
cp "${SCRIPT_DIR}/scripts/i18n/core/replacer.py" "${TARGET_DIR}/core/"
cp "${SCRIPT_DIR}/scripts/i18n/core/verifier.py" "${TARGET_DIR}/core/"
cp "${SCRIPT_DIR}/scripts/i18n/core/version.py" "${TARGET_DIR}/core/"
cp "${SCRIPT_DIR}/scripts/i18n/filters/__init__.py" "${TARGET_DIR}/filters/"
cp "${SCRIPT_DIR}/scripts/i18n/filters/noise_filter.py" "${TARGET_DIR}/filters/"
cp "${SCRIPT_DIR}/scripts/i18n/filters/ui_indicator.py" "${TARGET_DIR}/filters/"
cp "${SCRIPT_DIR}/scripts/i18n/commands/__init__.py" "${TARGET_DIR}/commands/"
cp "${SCRIPT_DIR}/scripts/i18n/commands/apply.py" "${TARGET_DIR}/commands/"
cp "${SCRIPT_DIR}/scripts/i18n/commands/extract.py" "${TARGET_DIR}/commands/"
cp "${SCRIPT_DIR}/scripts/i18n/commands/status.py" "${TARGET_DIR}/commands/"
cp "${SCRIPT_DIR}/scripts/i18n/commands/restore.py" "${TARGET_DIR}/commands/"

# Copy engine entry point
mkdir -p "${CLAUDE_DIR}/scripts"
cp "${SCRIPT_DIR}/scripts/engine.py" "${CLAUDE_DIR}/scripts/"

info "引擎模块已安装到 ${TARGET_DIR}"

echo -e "${BLUE}[3/4]${NC} 安装翻译数据和技能命令..."

# Copy translation data
cp "${SCRIPT_DIR}/scripts/zh-CN.json" "${TARGET_DIR}/"
cp "${SCRIPT_DIR}/scripts/skip-words.json" "${TARGET_DIR}/"
info "翻译映射表已安装"

# Copy skill command (INST-02)
mkdir -p "${SKILL_DIR}"
cp "${SCRIPT_DIR}/commands/zcf/i18n.md" "${SKILL_DIR}/"
info "技能命令已安装到 ${SKILL_DIR}/i18n.md"

# --- Verify ---

echo -e "${BLUE}[4/4]${NC} 验证安装..."

# Check critical files exist
MISSING=0
for f in \
    "${TARGET_DIR}/cli.py" \
    "${TARGET_DIR}/config/paths.py" \
    "${TARGET_DIR}/config/constants.py" \
    "${TARGET_DIR}/io/backup.py" \
    "${TARGET_DIR}/io/file_io.py" \
    "${TARGET_DIR}/core/replacer.py" \
    "${TARGET_DIR}/core/scanner.py" \
    "${TARGET_DIR}/core/verifier.py" \
    "${TARGET_DIR}/core/version.py" \
    "${TARGET_DIR}/commands/apply.py" \
    "${TARGET_DIR}/commands/extract.py" \
    "${TARGET_DIR}/commands/status.py" \
    "${TARGET_DIR}/commands/restore.py" \
    "${TARGET_DIR}/zh-CN.json" \
    "${TARGET_DIR}/skip-words.json" \
    "${SKILL_DIR}/i18n.md"; do
    if [ ! -f "$f" ]; then
        warn "缺失: $f"
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -eq 0 ]; then
    info "所有文件验证通过"
else
    warn "${MISSING} 个文件缺失"
fi

echo ""
echo -e "${GREEN}安装完成！${NC}"
echo ""
echo "使用方法:"
echo "  /zcf:i18n           一键汉化"
echo "  /zcf:i18n restore   恢复英文"
echo "  /zcf:i18n status    查看状态"
