#!/usr/bin/env python3
"""
Claude Code CLI 汉化引擎 v3.0

子命令:
  apply    - 应用中文汉化
  restore  - 恢复英文原文
  extract  - 提取新的可翻译字符串（JSON 格式输出）
  status   - 输出当前汉化状态（JSON 格式）
  version  - 输出当前 CLI 版本
"""

import json, re, sys, shutil, subprocess
from pathlib import Path

# ─── 路径 ─────────────────────────────────────────────
CLI_DIR   = Path("/Users/zhaolulu/.volta/tools/image/packages/@anthropic-ai/claude-code/lib/node_modules/@anthropic-ai/claude-code")
CLI_FILE  = CLI_DIR / "cli.js"
BACKUP    = CLI_DIR / "cli.bak.en.js"
PKG_JSON  = CLI_DIR / "package.json"
SCRIPTS   = Path(__file__).parent
LANG_FILE = SCRIPTS / "zh-CN.json"
SKIP_FILE = SCRIPTS / "skip-words.json"

# ─── 需要跳过的短字符串（太通用，会误伤代码逻辑）────
SKIP_WORDS = {
    "Yes","No","Error","Warning","Success","Failed",
    "Cancel","Continue","Skip","Retry","Stop","Ready",
    "Accept","Deny","Reject","Total","Usage",
    "Session","Settings","Running","Stop","Save","Load",
    "Open","Close","Back","Next","Prev","Home","End",
    "Start","Clear","Reset","Apply","Submit","Enter",
    "Edit","Delete","Copy","Paste","Cut","Undo","Redo",
    "On","Off","OK","Help","Exit","Quit","Main",
}

# ─── 用于判断"非 UI 字符串"的黑名单关键词 ─────────
NOISE_KW = [
    # 第三方库内部
    "azure","msal","oauth2?","grpc","protobuf","aws ","amazon","google cloud",
    "websocket","sec-websocket","rsv[123]","opcode","mask must","fin must",
    "acquiretoken","loggerprovider","meterprovider",
    "codegen","bigint","base64значение","xmlзначение",
    "www-authenticate","managed identity","instance metadata",
    "edms_","edoc_","access_rights","cloud instance discovery",
    "formdata","multipart","telemetry","semantic conventions",
    "suppressed","disposal","disposable","bridge client","payload length",
    "block sequence","anchor","yaml","redirect uri","credential source",
    "subject token","signature verification","pkcs","asn.1",
    "rfc-3339","int64 buffer","private member","fips","dualstack","dualstack",
    "s3 ","ec2 ","iam ","lambda ","cloudfront","route53",
    "dynamodb","kinesis","sns ","sqs ","elasticache",
    "protocol buffer","httprequest","x-amz-",
    "rfc 3986","rfc 6749","rfc 723",
    # 编程语言/协议关键字
    "\\.proto","utf-8","cors","content-type",
    # 无关内容
    "christmas carol","game of thrones","ted talk","yoga class",
    "soccer match","marathon","transatlantic","world cup",
    "inform 7","jboss","arcgis","bigquery",
]

NOISE_RE = re.compile("|".join(NOISE_KW), re.IGNORECASE)

# ─── UI 字符串指示关键词（权重从高到低）──────────────
# 分两组：强信号（Claude 核心）和弱信号（通用 UI）
STRONG_INDICATORS = [
    "claude code","claude.md","claude ",".claude",
    "anthropic","plan mode","yolo mode","auto mode","fast mode",
    "extended thinking","context window",
    "bypass permission","permission mode","sandbox",
    "mcp server","mcp tool","mcp ",
    "agent type","agent tool","agent idle","agent abort",
    "worktree","subagent",
    "accept terms","help improve claude",
    "auto-allow","autoallow",
]
WEAK_INDICATORS = [
    "permission","allow","deny","approve","reject",
    "agent","tool","skill","hook","plugin",
    "commit","branch","merge","pull request",
    "please","cannot","must be","is required","confirm",
    "loading","saving","processing","idle",
    "not found","already exist","unable to",
    "session","model","token","cost",
    "config","setting","marketplace",
    "install","uninstall","enable","disable",
    "new version","update available",
]


# ═══════════════════════════════════════════════════════
#  子命令实现
# ═══════════════════════════════════════════════════════

def cmd_version():
    """输出当前 cli.js 版本"""
    if PKG_JSON.exists():
        with open(PKG_JSON) as f:
            v = json.load(f).get("version", "unknown")
        print(v)
    else:
        print("unknown")


def cmd_status():
    """输出当前汉化状态 (JSON)"""
    result = {
        "cli_exists": CLI_FILE.exists(),
        "backup_exists": BACKUP.exists(),
        "version": "unknown",
        "localized": False,
        "lang_entries": 0,
    }
    if PKG_JSON.exists():
        with open(PKG_JSON) as f:
            result["version"] = json.load(f).get("version", "unknown")
    if CLI_FILE.exists():
        with open(CLI_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # 检测几个关键中文翻译是否存在
        markers = ["绕过权限", "规划模式", "自动模式", "接受编辑"]
        result["localized"] = sum(1 for m in markers if m in content) >= 2
    if LANG_FILE.exists():
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        result["lang_entries"] = len(data.get("translations", {}))
        result["lang_version"] = data.get("_meta", {}).get("cli_version", "")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_restore():
    """恢复英文原文"""
    if not BACKUP.exists():
        print(json.dumps({"ok": False, "error": "备份文件不存在"}, ensure_ascii=False))
        sys.exit(1)
    shutil.copy2(BACKUP, CLI_FILE)
    print(json.dumps({"ok": True, "action": "restored"}, ensure_ascii=False))


def cmd_apply():
    """应用中文汉化"""
    if not CLI_FILE.exists():
        print(json.dumps({"ok": False, "error": f"cli.js 未找到: {CLI_FILE}"}, ensure_ascii=False))
        sys.exit(1)

    # 从备份恢复干净状态
    if not BACKUP.exists():
        shutil.copy2(CLI_FILE, BACKUP)
    else:
        shutil.copy2(BACKUP, CLI_FILE)

    # 读取
    with open(CLI_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 加载翻译
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    translations = data.get("translations", {})

    # 替换
    stats = {"long": 0, "medium": 0, "short": 0, "skipped": 0}
    items = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

    for en, zh in items:
        if en == zh:
            continue
        if en in SKIP_WORDS:
            stats["skipped"] += 1
            continue

        en_len = len(en)
        if en_len > 20:
            count = content.count(en)
            if count > 0:
                content = content.replace(en, zh)
                stats["long"] += count
        elif en_len > 10:
            pattern = f'(?<=[\'"]){re.escape(en)}(?=[\'"])'
            matches = list(re.finditer(pattern, content))
            if matches:
                for m in reversed(matches):
                    content = content[:m.start()] + zh + content[m.end():]
                stats["medium"] += len(matches)
        else:
            pattern = f'(?<=[\'"\\s\\>])\\b{re.escape(en)}\\b(?=[\'"\\s\\<])'
            matches = list(re.finditer(pattern, content))
            if matches:
                cap = min(len(matches), 50)
                for m in reversed(matches[:cap]):
                    content = content[:m.start()] + zh + content[m.end():]
                stats["short"] += cap

    # 写入
    with open(CLI_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    # 语法验证
    try:
        r = subprocess.run(["node", "--check", str(CLI_FILE)],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            # 回滚
            shutil.copy2(BACKUP, CLI_FILE)
            print(json.dumps({
                "ok": False, "error": f"语法验证失败，已回滚: {r.stderr.strip()}",
                "stats": stats
            }, ensure_ascii=False))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "ok": False, "error": f"验证异常: {e}", "stats": stats
        }, ensure_ascii=False))
        sys.exit(1)

    total = stats["long"] + stats["medium"] + stats["short"]
    print(json.dumps({
        "ok": True,
        "action": "applied",
        "replacements": total,
        "stats": stats,
        "entries": len(translations),
    }, ensure_ascii=False))


def cmd_extract():
    """
    提取 cli.js 中新的、尚未翻译的用户可见英文字符串。
    输出 JSON 格式供技能命令使用。
    """
    src = BACKUP if BACKUP.exists() else CLI_FILE
    if not src.exists():
        print(json.dumps({"ok": False, "error": "cli.js 未找到"}, ensure_ascii=False))
        sys.exit(1)

    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    # 已翻译的 key 集合
    existing = set()
    if LANG_FILE.exists():
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            existing = set(json.load(f).get("translations", {}).keys())

    # 已跳过的 key 集合
    skipped = set()
    if SKIP_FILE.exists():
        with open(SKIP_FILE, "r", encoding="utf-8") as f:
            skipped = set(json.load(f).get("skip", []))

    # 提取所有双引号内的英文字符串
    candidates = re.findall(r'"([A-Z][A-Za-z][^"]{4,120})"', content)

    # 去重
    seen = set()
    new_strings = []

    for s in candidates:
        sl = s.lower().strip()

        # 去重
        if s in seen:
            continue
        seen.add(s)

        # 已翻译或已跳过
        if s in existing or s in skipped:
            continue

        # 必须包含空格（自然语言）
        if " " not in s:
            continue

        # 跳过代码片段
        if any(c in s for c in ["=>","${","===","!==","async ","function ",".prototype.","()"]):
            continue
        if "http://" in sl or "https://" in sl:
            continue
        if s == s.upper() and len(s) > 5:
            continue

        # 噪声过滤
        if NOISE_RE.search(s):
            continue

        # 优先级判定
        is_strong = any(kw in sl for kw in STRONG_INDICATORS)
        is_weak   = any(kw in sl for kw in WEAK_INDICATORS)

        if not is_strong and not is_weak:
            continue

        # 额外过滤：排除看起来像代码标识符的
        if '_' in s and not any(c in s for c in ' .,;:!?'):
            continue

        # 引号内精确出现次数
        count = content.count(f'"{s}"')

        # 评分：强信号 * 1000 + 出现次数
        score = (1000 if is_strong else 0) + count

        new_strings.append({"en": s, "count": count, "score": score,
                            "type": "strong" if is_strong else "weak"})

    # 按分数降序
    new_strings.sort(key=lambda x: x["score"], reverse=True)

    # 分桶输出
    strong = [x for x in new_strings if x["type"] == "strong"]
    weak   = [x for x in new_strings if x["type"] == "weak"]

    print(json.dumps({
        "ok": True,
        "strong_count": len(strong),
        "weak_count": len(weak),
        "existing_entries": len(existing),
        "skipped_entries": len(skipped),
        "strong": strong[:150],
        "weak": weak[:100],
    }, ensure_ascii=False, indent=2))


# ═══════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════

COMMANDS = {
    "version": cmd_version,
    "status":  cmd_status,
    "restore": cmd_restore,
    "apply":   cmd_apply,
    "extract": cmd_extract,
}

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "apply"
    aliases = {
        "en": "restore", "reset": "restore",
        "zh": "apply", "cn": "apply",
    }
    action = aliases.get(action, action)

    if action not in COMMANDS:
        print(f"用法: python3 localize.py [{'|'.join(COMMANDS.keys())}]")
        sys.exit(1)

    COMMANDS[action]()


if __name__ == "__main__":
    main()
