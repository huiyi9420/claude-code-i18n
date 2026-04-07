#!/usr/bin/env bash
# test_install.sh — 安装脚本轻量测试
#
# 验证 install.sh 的基本正确性，不实际安装到 ~/.claude/。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_SH="${PROJECT_DIR}/install.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $*"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $*"; }

echo "=== 安装脚本测试 ==="
echo ""

# --- 测试 1: bash 语法检查 ---
echo "[1/4] bash 语法检查..."
if bash -n "${INSTALL_SH}" 2>/dev/null; then
    pass "install.sh 语法正确"
else
    fail "install.sh 语法错误"
fi

# --- 测试 2: 命令模块文件存在 ---
echo "[2/4] 检查命令模块文件..."

# 从 install.sh 提取包含 coverage.py 的 for 循环（命令模块行）
COMMAND_LINE=$(grep 'coverage\.py.*; do' "${INSTALL_SH}" | head -1)
COMMAND_MODULES=$(echo "${COMMAND_LINE}" | sed 's/.*for f in //' | sed 's/; do//')

for module in ${COMMAND_MODULES}; do
    src="${PROJECT_DIR}/scripts/i18n/commands/${module}"
    if [ -f "${src}" ]; then
        pass "命令模块存在: commands/${module}"
    else
        fail "命令模块缺失: commands/${module}"
    fi
done

# 检查引擎入口
if [ -f "${PROJECT_DIR}/scripts/engine.py" ]; then
    pass "引擎入口存在: scripts/engine.py"
else
    fail "引擎入口缺失: scripts/engine.py"
fi

# 检查翻译数据文件
for data_file in zh-CN.json skip-words.json auto-translate-dict.json; do
    src="${PROJECT_DIR}/scripts/${data_file}"
    if [ -f "${src}" ]; then
        pass "数据文件存在: ${data_file}"
    else
        fail "数据文件缺失: ${data_file}"
    fi
done

# 检查技能命令
if [ -f "${PROJECT_DIR}/commands/auto-i18n.md" ]; then
    pass "技能命令存在: commands/auto-i18n.md"
else
    fail "技能命令缺失: commands/auto-i18n.md"
fi

# --- 测试 3: 关键变量定义 ---
echo "[3/4] 检查关键变量..."

if grep -q 'TARGET_DIR=' "${INSTALL_SH}"; then
    pass "TARGET_DIR 变量已定义"
else
    fail "TARGET_DIR 变量未定义"
fi

if grep -q 'COMMAND_FILE=' "${INSTALL_SH}"; then
    pass "COMMAND_FILE 变量已定义"
else
    fail "COMMAND_FILE 变量未定义"
fi

if grep -q 'python3' "${INSTALL_SH}"; then
    pass "Python 3 检查存在"
else
    fail "Python 3 检查缺失"
fi

if grep -q 'node' "${INSTALL_SH}"; then
    pass "Node.js 检查存在"
else
    fail "Node.js 检查缺失"
fi

# --- 测试 4: coverage.py 集成 ---
echo "[4/4] 检查 coverage.py 集成..."

if grep -q 'coverage\.py' "${INSTALL_SH}"; then
    pass "coverage.py 出现在 install.sh 中"
else
    fail "coverage.py 未出现在 install.sh 中"
fi

if grep -q 'coverage' "${PROJECT_DIR}/commands/auto-i18n.md"; then
    pass "coverage 出现在 auto-i18n.md 中"
else
    fail "coverage 未出现在 auto-i18n.md 中"
fi

# --- 结果汇总 ---
echo ""
echo "=== 测试结果 ==="
TOTAL=$((PASS + FAIL))
echo "  通过: ${PASS}/${TOTAL}"
echo "  失败: ${FAIL}/${TOTAL}"

if [ "${FAIL}" -gt 0 ]; then
    echo ""
    echo "FAILED: ${FAIL} 个测试未通过"
    exit 1
else
    echo ""
    echo "ALL PASSED"
    exit 0
fi
