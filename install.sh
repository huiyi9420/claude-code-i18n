#!/usr/bin/env bash
# install.sh — Claude Code auto-i18n Installer
#
# Installs the Chinese localization engine and /auto-i18n skill command.
# Checks for Python 3 and Node.js availability.
#
# Usage: bash install.sh

set -euo pipefail

# --- Configuration ---
CLAUDE_DIR="${HOME}/.claude"
TARGET_DIR="${CLAUDE_DIR}/scripts/i18n"
COMMAND_FILE="${CLAUDE_DIR}/commands/auto-i18n.md"
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

# Check Python 3
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python ${PY_VERSION}"
else
    error "Python 3 未安装。请先安装: https://www.python.org/downloads/"
fi

# Check Node.js
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

# Detect legacy zcf:i18n and warn
LEGACY_CMD="${CLAUDE_DIR}/commands/zcf/i18n.md"
if [ -f "${LEGACY_CMD}" ]; then
    warn "检测到旧版 /zcf:i18n 命令。建议手动删除: rm ${LEGACY_CMD}"
    warn "新版命令为 /auto-i18n"
fi

# --- Install Engine ---

echo -e "${BLUE}[2/4]${NC} 安装汉化引擎..."

mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/io"
mkdir -p "${TARGET_DIR}/core"
mkdir -p "${TARGET_DIR}/filters"
mkdir -p "${TARGET_DIR}/commands"

# Copy engine modules
for f in __init__.py cli.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/${f}" "${TARGET_DIR}/"
done

for f in __init__.py constants.py paths.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/config/${f}" "${TARGET_DIR}/config/"
done

for f in __init__.py backup.py file_io.py translation_map.py extract_snapshot.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/io/${f}" "${TARGET_DIR}/io/"
done

for f in __init__.py scanner.py replacer.py verifier.py version.py hooks.py auto_translate.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/core/${f}" "${TARGET_DIR}/core/"
done

for f in __init__.py noise_filter.py ui_indicator.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/filters/${f}" "${TARGET_DIR}/filters/"
done

for f in __init__.py apply.py extract.py status.py restore.py auto_update.py; do
    cp "${SCRIPT_DIR}/scripts/i18n/commands/${f}" "${TARGET_DIR}/commands/"
done

# Copy engine entry point
mkdir -p "${CLAUDE_DIR}/scripts"
cp "${SCRIPT_DIR}/scripts/engine.py" "${CLAUDE_DIR}/scripts/"

info "引擎模块已安装到 ${TARGET_DIR}"

# --- Install Data & Command ---

echo -e "${BLUE}[3/4]${NC} 安装翻译数据和技能命令..."

# Copy translation data
cp "${SCRIPT_DIR}/scripts/zh-CN.json" "${TARGET_DIR}/"
cp "${SCRIPT_DIR}/scripts/skip-words.json" "${TARGET_DIR}/"
cp "${SCRIPT_DIR}/scripts/auto-translate-dict.json" "${TARGET_DIR}/"
info "翻译数据已安装"

# Copy skill command
mkdir -p "$(dirname "${COMMAND_FILE}")"
cp "${SCRIPT_DIR}/commands/auto-i18n.md" "${COMMAND_FILE}"
info "技能命令已安装到 ${COMMAND_FILE}"

# --- Verify ---

echo -e "${BLUE}[4/4]${NC} 验证安装..."

MISSING=0
for f in \
    "${TARGET_DIR}/cli.py" \
    "${TARGET_DIR}/config/paths.py" \
    "${TARGET_DIR}/config/constants.py" \
    "${TARGET_DIR}/io/backup.py" \
    "${TARGET_DIR}/io/file_io.py" \
    "${TARGET_DIR}/io/translation_map.py" \
    "${TARGET_DIR}/io/extract_snapshot.py" \
    "${TARGET_DIR}/core/replacer.py" \
    "${TARGET_DIR}/core/scanner.py" \
    "${TARGET_DIR}/core/verifier.py" \
    "${TARGET_DIR}/core/version.py" \
    "${TARGET_DIR}/core/hooks.py" \
    "${TARGET_DIR}/core/auto_translate.py" \
    "${TARGET_DIR}/commands/apply.py" \
    "${TARGET_DIR}/commands/extract.py" \
    "${TARGET_DIR}/commands/status.py" \
    "${TARGET_DIR}/commands/restore.py" \
    "${TARGET_DIR}/commands/auto_update.py" \
    "${TARGET_DIR}/zh-CN.json" \
    "${TARGET_DIR}/skip-words.json" \
    "${TARGET_DIR}/auto-translate-dict.json" \
    "${CLAUDE_DIR}/scripts/engine.py" \
    "${COMMAND_FILE}"; do
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
echo "  /auto-i18n              一键汉化"
echo "  /auto-i18n restore      恢复英文"
echo "  /auto-i18n status       查看状态"
echo "  /auto-i18n auto-update  CLI 更新后自动重新汉化"
