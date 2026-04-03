---
name: gsd:progress
description: 检查项目进度、显示上下文并路由到下一步操作（执行或规划）
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - SlashCommand
---
<objective>
Check project progress, summarize recent work and what's ahead, then intelligently route to the next action - either executing an existing plan or creating the next one.

Provides situational awareness before continuing work.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/progress.md
</execution_context>

<process>
Execute the progress workflow from @$HOME/.claude/get-shit-done/workflows/progress.md end-to-end.
Preserve all routing logic (Routes A through F) and edge case handling.
</process>
