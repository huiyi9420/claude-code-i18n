---
name: gsd:plant-seed
description: 捕获带有触发条件的前瞻性想法 — 在合适的里程碑自动浮现
argument-hint: "[idea summary]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

<objective>
Capture an idea that's too big for now but should surface automatically when the right
milestone arrives. Seeds solve context rot: instead of a one-liner in Deferred that nobody
reads, a seed preserves the full WHY, WHEN to surface, and breadcrumbs to details.

Creates: .planning/seeds/SEED-NNN-slug.md
Consumed by: /gsd:new-milestone (scans seeds and presents matches)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/plant-seed.md
</execution_context>

<process>
Execute the plant-seed workflow from @$HOME/.claude/get-shit-done/workflows/plant-seed.md end-to-end.
</process>
