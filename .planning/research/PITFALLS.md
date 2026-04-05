# Domain Pitfalls: CLI i18n of Minified JavaScript

**Domain:** Post-build localization of a 13MB minified CLI JavaScript file
**Researched:** 2026-04-05
**Confidence:** HIGH (based on direct code analysis + verified domain research)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or broken functionality.

### Pitfall 1: Backup File Pollution (The #1 Architectural Sin)

**What goes wrong:** The "clean English backup" (`cli.bak.en.js`) silently accumulates Chinese characters. Once polluted, `restore` produces a corrupted file that is neither pure English nor fully Chinese. The current codebase already suffers this: the backup contains 12,224 Chinese characters (per PROJECT.md).

**Why it happens:** The backup is created on first run by copying the current `cli.js`. If `cli.js` has already been localized (from a previous run), the backup captures the localized version. Worse: any bug in the backup logic, any race condition, or any partial failure during apply can write Chinese into the backup permanently.

**Consequences:**
- `restore` does not restore pure English -- it restores a chimera
- `extract` reads from the polluted backup and treats Chinese text as source strings
- Users lose trust in the tool; the core value proposition ("一键恢复") is broken
- Recovery requires re-downloading the original package from npm

**Prevention:**
1. Compute a content hash (SHA-256) of the original file at backup creation time
2. Store the hash alongside the backup; verify on every restore
3. Never write to the backup after initial creation -- make it read-only
4. If backup hash does not match, refuse to restore and prompt re-download
5. Verify backup purity: scan for CJK characters before trusting it

**Detection:** Run `grep -c '[\x{4e00}-\x{9fff}]' cli.bak.en.js` -- any count > 0 means pollution.

**Phase mapping:** Phase 1 (Core Engine) -- this must be solved before any translation work begins.

---

### Pitfall 2: False Positives in String Matching (Replacing Code Logic, Not UI Text)

**What goes wrong:** A string like `"Error"` or `"Running"` appears in dozens of places in the minified bundle -- in error handling logic, in internal state machines, in API response parsers, and in user-visible UI text. Naive `str.replace()` hits all of them, corrupting code behavior while translating UI text.

**Why it happens:** The current engine (localize.py line 176-178) uses `content.replace(en, zh)` for long strings with zero context awareness. Even the "safer" medium-string regex (`(?<=[\'"]){re.escape(en)}(?=[\'"])`) only checks that the string is inside quotes -- not whether those quotes represent a UI string vs. a code logic string. The bundle contains ~23,651 capitalized double-quoted strings; ~17,589 of those are code logic, not UI text.

**Consequences:**
- Silent runtime errors: internal state checks compare against translated strings
- API response parsing breaks: error codes get translated
- Debugging becomes impossible: error messages are Chinese in logs meant for developers
- Behavior changes: conditional branches take wrong paths because string comparisons now fail

**Prevention:**
1. Require context markers for every translation entry: specify the structural pattern around the target string (e.g., "must appear after `console.log(`" or "must be in a JSX element")
2. For short strings (<15 chars), require match-on-surrounding-code-pattern, not just the string itself
3. Implement a "dry run with diff" mode that shows every replacement location before applying
4. Use the existing `node --check` validation (already in code) as a minimum gate, but add behavioral validation too
5. Maintain a "context fingerprint" for each translation -- a hash of the 50-100 characters surrounding the string -- and re-verify on each version update

**Detection:** After apply, run targeted tests: execute known CLI commands and verify they still work. Compare function count and variable count before/after -- any change indicates code corruption.

**Phase mapping:** Phase 1 (Core Engine) -- the three-tier strategy (long/medium/short) needs replacement with a context-aware strategy.

---

### Pitfall 3: Short Strings Are Landmines

**What goes wrong:** Strings under 10 characters (like "Error", "Running", "OK", "Save") are the most dangerous category. The current codebase caps short-string replacements at 50 per entry (line 191) and uses word-boundary matching, but these heuristics are insufficient. These words appear as both UI labels and code keywords, with no reliable way to distinguish them via regex alone.

**Why it happens:** The SKIP_WORDS list (45 entries) is a manual blacklist approach. It requires human maintenance and cannot scale. Every new CLI version may introduce new short strings that should or should not be translated. The fundamental problem: word-boundary regex (`\b...\b`) cannot distinguish `console.log("Error: " + msg)` from `<Text>Error</Text>`.

**Consequences:**
- "Error" gets translated in error-handling code that expects English strings
- "Running" gets translated in process status checks
- CLI crashes or enters undefined behavior states
- The cap of 50 replacements per short string is an arbitrary safety limit that either over-replaces (50 is too many) or under-replaces (some valid UI instances beyond 50 are missed)

**Prevention:**
1. Default to NOT translating short strings unless explicitly tagged with a code-context pattern
2. Require every short-string translation to include a "match context" -- a regex pattern for surrounding code
3. Consider abandoning short-string translation entirely for the MVP and deferring to Phase 2+
4. If translating short strings, require per-instance approval (show context to user/developer)

**Detection:** After apply, search for the translated short string in known code patterns (e.g., `catch`, `throw`, `if(...)`) and verify none were translated inside code logic.

**Phase mapping:** Phase 1 (Core Engine) -- short-string strategy must be decided before implementation.

---

### Pitfall 4: Template Literal and Concatenated String Blind Spots

**What goes wrong:** React components in the minified bundle construct UI text via template literals (`` `"Loading " + name` ``) or string concatenation (`"Error: " + message`). These patterns split a single user-visible string across multiple code tokens, making it impossible to match with a single string lookup.

**Why it happens:** Minification further obscures these patterns. A source-level `"Loading " + variable + " files"` becomes `"Loading "+e+" files"` in the bundle. The current engine only looks for exact string matches -- it cannot detect or translate these composite strings. The FormatJS project (formatjs/formatjs#2252) documents this as a known unsolved problem in i18n extraction.

**Consequences:**
- Significant UI text is invisible to the translation engine
- Users see partially translated interfaces: "正在加载 " followed by English text
- Coverage ceiling is inherently limited by single-string matching

**Prevention:**
1. Accept this as a known limitation for Phase 1
2. For Phase 2, build a pattern-matching engine that detects `"prefix" + variable + "suffix"` and translates prefix/suffix independently
3. Document coverage expectations honestly -- template literal patterns represent a coverage ceiling
4. Consider post-processing the applied file to detect partially-translated concatenation patterns

**Detection:** After apply, scan for patterns like `"[Chinese text]" + ` or `+ "[English text]"` that indicate partial translation.

**Phase mapping:** Phase 1 (acknowledge limitation) / Phase 2 (address with pattern matching).

---

### Pitfall 5: Version Updates Break Everything (The Maintenance Treadmill)

**What goes wrong:** Claude Code updates approximately weekly. Each update may:
- Add new UI strings (translations become stale)
- Change existing UI strings (translations become mismatched)
- Move strings to different locations (context fingerprints break)
- Remove strings (harmless but creates dead translations)

**Why it happens:** The translation mapping is keyed by exact English string. Any change to the source string (even a typo fix) invalidates the mapping. The current codebase has a `_meta.cli_version` field but no automated mechanism to detect version drift or update translations.

**Consequences:**
- Translations silently degrade with each update
- Users don't notice until they see English text reappearing
- Manual re-extraction and re-translation required for every update
- The `extract` command itself is compromised if the backup is polluted (see Pitfall 1)

**Prevention:**
1. Implement automated version-change detection: compare current `package.json` version against `_meta.cli_version`
2. On version change, re-extract from the NEW clean source (not from backup)
3. Diff old translations against new extractions: classify as new/changed/unchanged/removed
4. For changed strings, flag for human review rather than auto-dropping
5. Build a regression test suite: known CLI outputs that should be translated, tested after each apply

**Detection:** Compare `_meta.cli_version` against actual installed version before each apply. Warn if mismatched.

**Phase mapping:** Phase 1 (version detection + basic re-extraction) / Phase 2 (automated diff and smart merge).

---

### Pitfall 6: Replacement Order Causes Cascade Failures

**What goes wrong:** The current engine sorts translations by length (longest first) and processes them sequentially (line 165). This means `"Extended thinking"` is replaced before `"Extended"`. But if a translation for a shorter string is a substring of a longer string's translation, the shorter replacement can corrupt the longer one's output.

**Why it happens:** The engine uses in-place string replacement on the entire 13MB content. Each replacement modifies the content for all subsequent replacements. There is no isolation between replacement operations.

**Consequences:**
- A translation like `"mode" -> "模式"` could corrupt `"Plan Mode" -> "规划模式"` if processed in wrong order
- Nested or overlapping string matches produce garbled output
- The bug is order-dependent and hard to reproduce

**Prevention:**
1. Maintain the longest-first ordering (already implemented -- good)
2. After all replacements, verify no partial English fragments remain in translated regions
3. Process replacements on an AST-like offset map rather than sequential mutation
4. Build a "replacement planner" that detects overlapping targets and resolves conflicts before execution

**Detection:** Post-apply scan for patterns that mix Chinese and English in suspicious ways (e.g., a Chinese character followed by English word followed by Chinese character within the same quoted string).

**Phase mapping:** Phase 1 (Core Engine) -- replacement ordering must be correct from day one.

---

## Moderate Pitfalls

### Pitfall 7: Hardcoded Installation Paths

**What goes wrong:** `CLI_DIR` is hardcoded to `/Users/zhaolulu/.volta/...` (line 17). Any user with a different installation method (nvm, fnm, system node, Homebrew) or different username gets an immediate failure.

**Prevention:**
1. Use `which claude` or `npm list -g @anthropic-ai/claude-code` to dynamically resolve the path
2. Support a config file (`~/.claude/i18n.json`) for custom paths
3. Document supported installation methods and test each

**Detection:** If `CLI_FILE.exists()` returns False, report a clear error with instructions for manual path configuration.

**Phase mapping:** Phase 1 (Core Engine) -- path resolution is table stakes.

---

### Pitfall 8: node --check Is Necessary but Not Sufficient

**What goes wrong:** The current engine validates with `node --check` after apply (line 201). This catches syntax errors but not semantic errors. A replacement that changes a string inside a comparison operator (`if (x === "Error")` becoming `if (x === "错误")`) passes syntax check but breaks runtime behavior.

**Prevention:**
1. Keep `node --check` as the minimum gate
2. Add structural validation: compare token count and token positions before/after
3. For high-risk replacements, add targeted behavioral tests (run `claude --version`, `claude --help`)
4. Consider a "smoke test suite" that exercises known CLI paths post-apply

**Phase mapping:** Phase 1 (keep `node --check`) / Phase 2 (add behavioral validation).

---

### Pitfall 9: Encoding and BOM Corruption

**What goes wrong:** Reading a UTF-8 file, modifying it in memory with Python, and writing it back can introduce encoding issues: BOM markers, line ending changes, or locale-dependent character handling. The minified JS file is essentially a single 13MB line -- some tools handle this poorly.

**Prevention:**
1. Always use `encoding="utf-8"` explicitly (already done -- good)
2. Never use locale-dependent operations on the content
3. Verify file size is consistent (accounting for character length changes) post-write
4. Use binary-safe file operations when possible
5. Do not introduce BOM; strip existing BOM if present

**Detection:** Compare first 3 bytes of output file -- should not be `\xEF\xBB\xBF`. File should be valid UTF-8.

**Phase mapping:** Phase 1 (Core Engine) -- encoding correctness from the start.

---

### Pitfall 10: Regex Special Characters in Translation Strings

**What goes wrong:** English strings may contain regex metacharacters (`$`, `.`, `?`, `*`, `+`, `(`, `)`, `[`, `]`, `{`, `}`, `\`, `|`, `^`). The current engine uses `re.escape(en)` for medium and short strings (lines 181, 188) but uses raw `content.replace(en, zh)` for long strings (line 178), which is correct for Python's `str.replace()` (not regex-based). However, if the replacement value `zh` contains backslash sequences, unexpected behavior could occur.

**Prevention:**
1. `str.replace()` is safe for both pattern and replacement in Python (no regex interpretation) -- keep using it for long strings
2. For regex-based matching (medium/short strings), always use `re.escape()` on the search pattern (already done)
3. Verify Chinese translation values do not contain unintended backslash sequences

**Phase mapping:** Phase 1 (verify existing escaping is correct).

---

### Pitfall 11: Single-Point-of-Failure Replace Strategy

**What goes wrong:** The apply operation is all-or-nothing on a single 13MB file. If the process crashes mid-write, the file is corrupted. If syntax validation fails, the rollback copies the backup, but the backup itself may be polluted (see Pitfall 1).

**Prevention:**
1. Write to a temporary file first, then atomically rename (`os.rename`) to the target
2. Never modify the target file directly until all replacements and validations are complete
3. Keep the backup as a separate immutable artifact

**Phase mapping:** Phase 1 (Core Engine) -- atomic writes are a basic safety requirement.

---

### Pitfall 12: Performance Degradation with Large Translation Maps

**What goes wrong:** The current engine iterates through all translations and runs `content.count(en)` or `re.finditer()` for each one. With 834+ translations against a 13MB string, this is O(n * m) where n = translations and m = file size. As the translation map grows toward 2000+ entries (90% coverage target), performance degrades.

**Prevention:**
1. Pre-scan the content once to build a string occurrence index
2. Use the index for O(1) lookups per translation entry
3. Consider Aho-Corasick algorithm for multi-pattern matching (find all translation targets in a single pass)
4. Target: 30-second budget for full apply (per PROJECT.md constraints)

**Phase mapping:** Phase 1 (basic performance) / Phase 2 (optimized multi-pattern matching).

---

## Minor Pitfalls

### Pitfall 13: Inconsistent Quote Style Matching

**What goes wrong:** The minified bundle uses both single and double quotes. The medium-string regex checks for quote context (`(?<=[\'"])`) but the extract function only looks for double-quoted strings (line 253: `r'"([A-Z][A-Za-z][^"]{4,120})"'`). Single-quoted UI strings are invisible to extraction.

**Prevention:** Extract from both quote styles. Match `'` and `"` patterns during extraction.

---

### Pitfall 14: Translation Map Format Lock-In

**What goes wrong:** The flat key-value JSON format (`{"English": "Chinese"}`) cannot express context-dependent translations. The same English phrase may need different Chinese translations in different UI locations.

**Prevention:** Plan for a structured format that supports context tags:
```json
{
  "Error": [
    {"context": "title", "zh": "错误"},
    {"context": "button", "zh": "报错"}
  ]
}
```

---

### Pitfall 15: No Incremental/Partial Apply

**What goes wrong:** Every apply starts from the clean backup and re-applies ALL translations. There is no way to apply only new or changed translations. This wastes time and makes debugging harder (which translation caused the break?).

**Prevention:** Track which translations have been applied. Support `--dry-run` and `--only-changed` flags.

---

## Phase-Specific Warnings

| Phase | Likely Pitfall | Severity | Mitigation |
|-------|---------------|----------|------------|
| **Phase 1: Core Engine** | Backup pollution | CRITICAL | Immutable backup + hash verification |
| **Phase 1: Core Engine** | False positives (long strings) | CRITICAL | Context-aware matching, not just quote boundaries |
| **Phase 1: Core Engine** | Short string landmines | CRITICAL | Default-skip strategy, require explicit context for each |
| **Phase 1: Core Engine** | Replacement ordering | HIGH | Longest-first + overlap detection |
| **Phase 1: Core Engine** | Hardcoded paths | HIGH | Dynamic path resolution |
| **Phase 1: Core Engine** | Atomic writes | HIGH | Write-to-temp + rename pattern |
| **Phase 2: Coverage** | Template literal blind spots | MEDIUM | Accept limitation, document coverage ceiling |
| **Phase 2: Coverage** | Performance at scale | MEDIUM | Aho-Corasick or similar multi-pattern matching |
| **Phase 2: Coverage** | Context-dependent translations | MEDIUM | Structured translation format |
| **Phase 2: Coverage** | Behavioral validation | MEDIUM | Smoke test suite post-apply |
| **Phase 3: Maintenance** | Version drift | HIGH | Automated version detection + smart diff |
| **Phase 3: Maintenance** | Regression detection | HIGH | CI integration + coverage reports |
| **Phase 3: Maintenance** | Extract from polluted source | CRITICAL | Always extract from verified-clean source |

---

## Decision Matrix: When to Accept Risk vs. Build Prevention

| Scenario | Risk Level | Recommended Action |
|----------|-----------|-------------------|
| Translating strings >30 chars with unique content | LOW | Safe with basic quote-boundary matching |
| Translating strings 15-30 chars | MEDIUM | Require quote-boundary + NOISE_RE filter |
| Translating strings 10-15 chars | HIGH | Require surrounding-code-context match |
| Translating strings <10 chars | CRITICAL | Skip by default; require explicit per-instance context |
| First-time backup creation | LOW | Just copy + hash |
| Re-using existing backup | HIGH | Verify hash + scan for CJK contamination |
| Applying to same-version CLI | LOW | Standard apply |
| Applying to updated CLI version | HIGH | Re-extract + diff + manual review of changes |

---

## Sources

- [Stack Overflow: Why use AST instead of regex](https://stackoverflow.com/questions/72017024/why-use-ast-syntax-tree-modification-instead-of-regex-replacement) -- HIGH confidence, verifies AST vs regex tradeoff
- [Terser Issue #437: Unicode escape source map offset](https://github.com/terser/terser/issues/437) -- HIGH confidence, documents character-length corruption in minifiers
- [FormatJS Issue #2252: Concatenated string literals](https://github.com/formatjs/formatjs/issues/2252) -- HIGH confidence, documents unsolved i18n extraction challenge for template literals
- [Stack Overflow: Replace values in minified JS with sed](https://stackoverflow.com/questions/54263124/how-to-replace-a-multiple-values-in-a-minified-javascript-file-with-sed) -- MEDIUM confidence, community-verified pitfalls of sed on minified code
- [GitHub Issue: ocdownloader - minified files are nearly impossible to edit](https://github.com/e-alfred/ocdownloader/issues/36) -- MEDIUM confidence, community consensus
- [Phrase: 10 Common Localization Mistakes](https://phrase.com/blog/posts/10-common-mistakes-in-software-localization/) -- MEDIUM confidence, industry reference
- [Direct code analysis of localize.py](file:///Users/zhaolulu/Projects/claude-code-i18n/scripts/localize.py) -- HIGH confidence, primary source
- [PROJECT.md context](file:///Users/zhaolulu/Projects/claude-code-i18n/.planning/PROJECT.md) -- HIGH confidence, project-specific constraints and known issues
