# Project Agent Convention

This file defines cross-tool conventions for any AI agent working in this repository.
It applies to Cursor, Codex, Claude Code, OpenClaw, OpenCode, and any future host.

## Task Logging (Mandatory)

Every agent that completes a round of work in this repository **must** write a task log before claiming completion.

### Where

```
logs/tasks/YYYY-MM-DD-<topic>.md
```

One file per task round. If the same day has multiple tasks, append a short distinguishing suffix.

### What to Record

Every task log must contain at least these fields:

```markdown
# Task Log: <topic>

## Meta
- Date: YYYY-MM-DD
- Agent / Tool: (e.g. Cursor, Codex, Claude Code)
- Trigger: (user request summary or /vibe session ID)

## What Was Done
- (bullet list of deliverables)

## How It Was Done
- (approach, key decisions, trade-offs)

## Files Changed
- (list of created / modified / deleted files)

## Verification
- (commands run, checks passed, route tests, linter results)

## Residual Risk / Known Gaps
- (anything not yet covered, edge cases, TODO)

## Next Steps
- (suggested follow-up for user or next agent session)
```

### Rules

1. **No "done" without a log.** If you claim a task is complete, the log file must already exist.
2. **Incomplete tasks still get logged.** Write the log with a clear `Status: incomplete` and explain where you stopped and why.
3. **Do not put logs only in chat.** The log must be a committed file in `logs/tasks/`, not just a chat message.
4. **Keep it concise but auditable.** Aim for 30–80 lines. Not a novel, but enough for someone else to understand what happened without re-reading the full chat history.
5. **Reference, don't duplicate.** If a `/vibe` session already produced `docs/requirements/` and `docs/plans/` artifacts, link to them instead of repeating their content.

### Relationship to /vibe Governed Runtime

When a task is executed under `/vibe` (the governed runtime), the runtime already produces:

- `docs/requirements/YYYY-MM-DD-<topic>.md`
- `docs/plans/YYYY-MM-DD-<topic>-execution-plan.md`
- `outputs/runtime/vibe-sessions/<run-id>/cleanup-receipt.json`

The task log in `logs/tasks/` is **complementary**, not a replacement. It serves as the human-readable summary that ties the formal governance artifacts together and records the "what actually happened" narrative.

### Example

```
logs/tasks/2026-04-14-algorithm-engineer-dualstack-integration.md
```

```markdown
# Task Log: algorithm-engineer-dualstack Integration

## Meta
- Date: 2026-04-14
- Agent / Tool: Cursor (Agent mode)
- Trigger: User requested adding 算法skill.md as a community skill

## What Was Done
- Mirrored algorithm-engineer-dualstack as bundled/skills/algorithm-engineer-dualstack/SKILL.md
- Added canonical routing (pack-manifest, skill-keyword-index, skill-routing-rules)
- Updated skills管理和安装指南.md (category + community record)

## How It Was Done
- Classified as single-entry community skill, AI/ML domain (category 5)
- Set conservative priority (85) to avoid stealing narrow ML/vision skills
- Added negative keywords to prevent misrouting from security/literature/UI contexts

## Files Changed
- bundled/skills/algorithm-engineer-dualstack/SKILL.md (created)
- config/pack-manifest.json (modified)
- config/skill-keyword-index.json (modified)
- config/skill-routing-rules.json (modified)
- skills管理和安装指南.md (modified)
- docs/requirements/2026-04-14-algorithm-engineer-dualstack-community-skill.md (created)
- docs/plans/2026-04-14-algorithm-engineer-dualstack-community-skill-execution-plan.md (created)

## Verification
- vgo_cli route: "调度算法工程" → algorithm-engineer-dualstack (confidence 0.7) ✅
- vgo_cli route: "图像算法复现与消融实验" → algorithm-engineer-dualstack (confidence 0.45) ✅
- Pure MATLAB requests still route to matlab skill ✅
- ReadLints: no errors on modified files ✅

## Residual Risk / Known Gaps
- Prompts mentioning both "MATLAB" and "algorithm engineering" may still route to matlab due to name_score boost
- License field in community record marked as "待补充"

## Next Steps
- User to provide upstream repo URL and license for documentation completeness
- Consider further keyword tuning if MATLAB+algorithm dual-intent misroutes persist
```

## Other Conventions

### Do Not

- Do not create a second router or a second requirement-freeze surface (canonical router authority is in `config/pack-manifest.json`).
- Do not put runtime governance artifacts (receipts, capsules) into `logs/tasks/`. Those belong in `outputs/runtime/`.
- Do not use `logs/tasks/` for prompt assets, skill definitions, or configuration — those have their own canonical homes.

### Directory Hygiene

- `logs/tasks/` is for task logs only.
- Old logs should not be deleted during routine cleanup. They are audit trail.
- If the directory grows very large, archive by year: `logs/tasks/2026/`, `logs/tasks/2027/`.
