---
name: gsd:next
description: 自动推进到 GSD 工作流的下一个逻辑步骤
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - SlashCommand
---
<objective>
Detect the current project state and automatically invoke the next logical GSD workflow step.
No arguments needed — reads STATE.md, ROADMAP.md, and phase directories to determine what comes next.

Designed for rapid multi-project workflows where remembering which phase/step you're on is overhead.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/next.md
</execution_context>

<process>
Execute the next workflow from @$HOME/.claude/get-shit-done/workflows/next.md end-to-end.
</process>
