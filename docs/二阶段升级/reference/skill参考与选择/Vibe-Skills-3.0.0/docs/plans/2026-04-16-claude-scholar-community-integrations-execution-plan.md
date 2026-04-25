# Execution Plan: claude-scholar 社区 Skill / Agent 扩充接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-16-claude-scholar-community-integrations-execution-plan |
| 状态 | completed |
| 需求文档 | docs/requirements/2026-04-16-claude-scholar-community-integrations.md |
| 内部等级 | L（serial native execution） |
| 创建日期 | 2026-04-16 |

## Wave 1: Skill 镜像（41 个）

### Step 1.1: 逐目录镜像
- 来源根：`_temp_community_skills/claude-scholar/skills/`
- 目标根：`bundled/skills/`
- 对需求文档“本轮接入（41 个）”中的每个 `skill-id`：
  - 镜像整个目录到 `bundled/skills/<skill-id>/`
  - 保留 `SKILL.md`、`scripts/`、`references/`、`examples/`、`USAGE.md` 等结构

### Step 1.2: 同名不替换
- 对需求文档“已存在（7 个）”保持不覆盖：
  - `code-review-excellence`
  - `doc-coauthoring`
  - `frontend-design`
  - `mcp-integration`
  - `planning-with-files`
  - `ui-ux-pro-max`
  - `webapp-testing`

## Wave 2: Agent 资产接入（15 个）

### Step 2.1: 接入路径
- 将 `_temp_community_skills/claude-scholar/agents/*.md` 作为仓库资产接入（不改变 `config/opencode/agents/` 主入口结构）
- 同步更新 `agent-map.md`：补充 claude-scholar agent 列表、定位、与 Vibe XL subagent 的边界说明

## Wave 3: Canonical 路由接入（41 个 skills）

### Step 3.1: `config/pack-manifest.json`
- 新增 claude-scholar community packs（按主题拆分，保守优先级）：
  - research ideation / literature
  - experiment analysis + reporting
  - paper writing + rebuttal + post-acceptance
  - obsidian knowledge base
  - zotero ↔ obsidian bridge
  - engineering workflow & debugging
  - skill-ops / quality reviewer / improver
- 每个 pack 定义：
  - `priority`
  - `task_allow`
  - `trigger_keywords`（中英文）
  - `skill_candidates`
  - `defaults_by_task`（按需）

### Step 3.2: `config/skill-keyword-index.json`
- 为 41 个 skills 补充**中英文关键词**召回
- 关键词策略：
  - 以“强意图词”为主（例如 `rebuttal` / `obsidian vault` / `Zotero` / `gap analysis`）
  - 避免用过泛词导致误抢（例如仅用 `plan` / `report` 这类词）

### Step 3.3: `config/skill-routing-rules.json`
- 为 41 个 skills 增加规则：
  - `task_allow`
  - `positive_keywords`
  - `negative_keywords`（对高冲突技能必须加）
- 目标：让代表性表达稳定命中，同时不显著干扰现有窄技能。

## Wave 4: 文档与来源披露

### Step 4.1: `skills管理和安装指南.md`
- 第三章分类清单补充 claude-scholar 新增技能（带 `*(Community)*`）
- 第六章社区技能集成记录新增 claude-scholar 条目（可按“一个来源 + 多技能清单”或“逐 skill 记录”落表）
- 调通检查补入：
  - 路由命中验证（`vgo_cli route`）
  - 脚本级 smoke（对含 scripts 的关键技能）

### Step 4.2: 许可与上游锁定
- 更新 `config/upstream-lock.json`：新增 `Galaxy-Dawn/claude-scholar`（MIT，distributed-local，bundled_paths 列出新增 skills）
- 更新 `THIRD_PARTY_LICENSES.md`：新增披露行（claude-scholar）

## Wave 5: 验证与收尾

### Step 5.1: 路由验证（代表性表达）
- 每个新增 pack 至少 1 条：
  - `research-ideation`：研究选题 / gap 分析 / 5W1H
  - `results-analysis`：统计显著性 / ablation / figure catalog
  - `results-report`：实验复盘报告 / decision-oriented summary
  - `ml-paper-writing`：related work / methods / 写论文
  - `review-response`：rebuttal / 审稿回复
  - `obsidian-project-memory`：Obsidian 项目知识库 / vault 同步
  - `zotero-obsidian-bridge`：Zotero collection → paper notes / schema 校验
  - `skill-development`：新增 skill 设计 / 结构化改进

验证命令形态：
- `python -m vgo_cli.main route "<query>"`

### Step 5.2: 脚本级 smoke（关键 scripts）
示例（以 `--help` 或安全子命令为准）：
- `python bundled/skills/obsidian-project-memory/scripts/project_kb.py --help`
- `python bundled/skills/zotero-obsidian-bridge/scripts/verify_paper_notes.py --help`
- `python bundled/skills/publication-chart-skill/scripts/ensure_publication_tooling.py --help`

### Step 5.3: 仓库健康检查
- `pwsh ./check.ps1 -Deep`
- `pwsh ./scripts/verify/vibe-generate-skills-lock.ps1`

### Step 5.4: 任务日志
- 写入：`logs/tasks/2026-04-16-claude-scholar-community-integrations.md`

## 回滚规则

- 若新 pack 抢走现有窄技能（例如 `prompt-library`、`literature-review`、`code-reviewer`），优先：
  1) 降低 pack `priority`
  2) 收紧 `trigger_keywords`
  3) 增加 skill 级 `negative_keywords`
- 若路由命中长期不稳定：
  - 先保证“强意图词”命中（如 `rebuttal`/`Obsidian vault`/`gap analysis`）
  - 允许对泛化表达保持命中到已有通用 skill（记录为已知边界）

