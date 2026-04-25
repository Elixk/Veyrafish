# Requirement: claude-scholar 社区 Skill / Agent 扩充接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-16-claude-scholar-community-integrations |
| 状态 | completed |
| 创建日期 | 2026-04-16 |
| 作者 | AI Agent (governed) |

## 1. 背景

用户已将 `claude-scholar` 项目手动下载到：

- `_temp_community_skills/claude-scholar/`

并要求按 `skills管理和安装指南.md` 的规范，将其中**值得接入**的 skill 与 agent 资产纳入本仓库，使其进入 canonical 路由并通过验证。

现状盘点结论（以 `_temp_community_skills/claude-scholar/skills/*/SKILL.md` 与 `bundled/skills/*/SKILL.md` 对比）：

- claude-scholar 技能总数：48
- 已存在于 `bundled/skills/` 的技能：7（本轮**不替换**）
- 缺失待接入技能：41（本轮接入范围）

## 2. 目标

将 claude-scholar 的“缺失待接入”技能（41 个）以**社区 skill**形式接入本仓库，并把 claude-scholar 的 agent（15 个）作为仓库可追溯资产纳入，同时满足“已接入可调用”的最低标准：

1. 镜像到 `bundled/skills/<skill-id>/`（保留上游结构：`SKILL.md` + `scripts/`/`references/`/`examples/` 等）
2. 进入 canonical 路由（`pack-manifest` + `skill-keyword-index` + `skill-routing-rules`）
3. 更新 `skills管理和安装指南.md`（分类清单 + 社区集成记录 + 调通检查说明）
4. 更新第三方来源披露（`config/upstream-lock.json` + `THIRD_PARTY_LICENSES.md`）
5. 对代表性表达进行路由验证，并通过 `check.ps1 -Deep`
6. 写入 `logs/tasks/` 任务日志

## 3. 接入范围

### 3.1 已存在（7 个，不替换）

以下技能在本仓库 `bundled/skills/` 已存在，本轮**不从 claude-scholar 覆盖**：

- `code-review-excellence`
- `doc-coauthoring`
- `frontend-design`
- `mcp-integration`
- `planning-with-files`
- `ui-ux-pro-max`
- `webapp-testing`

### 3.2 本轮接入（41 个）

> 以下均来自 `_temp_community_skills/claude-scholar/skills/<skill-id>/`。

- `agent-identifier`
- `architecture-design`
- `bug-detective`
- `citation-verification`
- `command-development`
- `daily-coding`
- `daily-paper-generator`
- `defuddle`
- `git-workflow`
- `hook-development`
- `json-canvas`
- `kaggle-learner`
- `latex-conference-template-organizer`
- `ml-paper-writing`
- `obsidian-bases`
- `obsidian-cli`
- `obsidian-experiment-log`
- `obsidian-link-graph`
- `obsidian-literature-workflow`
- `obsidian-markdown`
- `obsidian-project-bootstrap`
- `obsidian-project-lifecycle`
- `obsidian-project-memory`
- `obsidian-research-log`
- `obsidian-synthesis-map`
- `paper-self-review`
- `plugin-structure`
- `post-acceptance`
- `publication-chart-skill`
- `research-ideation`
- `results-analysis`
- `results-report`
- `review-response`
- `skill-development`
- `skill-improver`
- `skill-quality-reviewer`
- `uv-package-manager`
- `verification-loop`
- `web-design-reviewer`
- `writing-anti-ai`
- `zotero-obsidian-bridge`

### 3.3 Agent 资产（15 个）

claude-scholar 提供的 agent prompts（位于 `_temp_community_skills/claude-scholar/agents/*.md`）本轮将作为仓库资产接入，并同步更新 `agent-map.md` 说明其定位与调用边界：

- `architect`
- `build-error-resolver`
- `bug-analyzer`
- `code-reviewer`
- `dev-planner`
- `kaggle-miner`
- `literature-reviewer`
- `literature-reviewer-obsidian`
- `paper-miner`
- `rebuttal-writer`
- `refactor-cleaner`
- `research-knowledge-curator-obsidian`
- `story-generator`
- `tdd-guide`
- `ui-sketcher`

## 4. 类型判断

本轮接入以“多 skill 集合（skill pack family）”为主，单个 skill 形态不强行统一：

- **单入口 workflow/prompt 型**：仅 `SKILL.md` 或少量 references（如 `uv-package-manager`）
- **脚本增强型**：包含 `scripts/`，可做脚本级 smoke（如 `obsidian-project-memory`、`publication-chart-skill`、`zotero-obsidian-bridge`）
- **知识库/多资源型**：references/examples 较多，用于形成可复用工作流（如 `results-analysis`）

## 5. 路由策略（边界约束）

1. **不替换已存在技能**：对“已存在 7 个”不做覆盖式同步，避免无意回归。
2. **分 pack 接入，避免误抢**：按主题拆为多个 community pack，并设置保守优先级（不高于核心治理/代码质量 packs）。
3. **关键词精确化**：为每个新 skill 增加中英文关键词；为易冲突技能补 `negative_keywords` 边界。
4. **不扩大宿主权力面**：claude-scholar 的 rules/hooks/installer 资产不作为本仓库默认执行面；本轮仅接入 skills 与 agents 的可调用/可追溯层。

## 6. 来源与许可

- 来源仓库：`Galaxy-Dawn/claude-scholar`
- 仓库地址：`https://github.com/Galaxy-Dawn/claude-scholar`
- 许可：MIT（以 claude-scholar README/Badge 为准；最终以 upstream LICENSE 为准）

## 7. 验收标准

- [x] 41 个缺失 skill 已镜像到 `bundled/skills/<skill-id>/`，且每个目录至少包含 `SKILL.md`
- [x] claude-scholar 的 15 个 agents 已以仓库资产形式接入，并在 `agent-map.md` 中可检索
- [x] `config/pack-manifest.json` 已新增 claude-scholar community packs，并能覆盖主要任务意图
- [x] `config/skill-keyword-index.json` 已补全上述 41 个 skill 的中英文关键词
- [x] `config/skill-routing-rules.json` 已补全上述 41 个 skill 的规则（含必要的 negative keywords）
- [x] `skills管理和安装指南.md` 已更新：分类清单 + 社区集成记录 + 调通检查说明
- [x] `config/upstream-lock.json` 与 `THIRD_PARTY_LICENSES.md` 已新增 claude-scholar 披露条目
- [x] `vgo_cli route` 已对每个 pack 至少 1 条代表性表达命中验证（记录 selected.skill + 置信度）
- [x] 脚本型 skill 已完成至少 1 条脚本级 smoke（例如 `--help` 或显式的安全子命令）
- [x] `check.ps1 -Deep -SkipRuntimeFreshnessGate` 通过（无 `custom_manifest_invalid` / `custom_dependencies_missing` 等新增问题；remaining warnings 属于宿主 readiness）
- [x] `logs/tasks/` 已写入本轮 task log

## 8. 非目标

- 不尝试把 claude-scholar 的 Claude Code 插件/安装器行为“迁移为本仓库默认执行面”
- 不在本轮引入 Zotero MCP 的真实联调（仅接入 skill 资产与路由；MCP 真实联调作为后续可选任务）
- 不对已存在的 7 个同名技能进行上游版本对齐或替换（如确需升级，另起变更轮次）

