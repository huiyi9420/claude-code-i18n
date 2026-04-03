---
name: gsd:session-report
description: 生成会话报告，包含 token 用量估算、工作摘要和结果
allowed-tools:
  - Read
  - Bash
  - Write
---
<objective>
Generate a structured SESSION_REPORT.md document capturing session outcomes, work performed, and estimated resource usage. Provides a shareable artifact for post-session review.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/session-report.md
</execution_context>

<process>
Execute the session-report workflow from @$HOME/.claude/get-shit-done/workflows/session-report.md end-to-end.
</process>
