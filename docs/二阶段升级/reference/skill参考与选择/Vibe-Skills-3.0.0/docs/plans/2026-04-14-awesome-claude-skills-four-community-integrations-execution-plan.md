# Execution Plan: awesome-claude-skills 四个社区 Skill 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-awesome-claude-skills-four-community-integrations-execution-plan |
| 状态 | completed |
| 需求文档 | docs/requirements/2026-04-14-awesome-claude-skills-four-community-integrations.md |
| 内部等级 | L（serial native execution） |
| 创建日期 | 2026-04-14 |

## Wave 1: Skill 镜像

### Step 1.1: 镜像主入口
- 创建以下目录：
  - `bundled/skills/invoice-organizer/`
  - `bundled/skills/tailored-resume-generator/`
  - `bundled/skills/meeting-insights-analyzer/`
  - `bundled/skills/langsmith-fetch/`
- 将上游 `SKILL.md` 原样镜像为主入口

### Step 1.2: 保持单入口形态
- 不额外伪造 `scripts/`、`references/`、`requirements.txt`
- 在文档中显式记录 `langsmith-fetch` 依赖外部 CLI

## Wave 2: Canonical 路由接入

### Step 2.1: 更新 `config/pack-manifest.json`
- 为四个新 skill 增加独立 community pack
- 采用保守优先级，避免误抢现有窄技能

### Step 2.2: 更新 `config/skill-keyword-index.json`
- 增加中英文关键词召回

### Step 2.3: 更新 `config/skill-routing-rules.json`
- 设置 `task_allow`
- 设置 `positive_keywords` / `negative_keywords`
- 仅在边界明确时设置 `canonical_for_task`

## Wave 3: 文档与验证

### Step 3.1: 更新 `skills管理和安装指南.md`
- 第 4 / 20 / 21 类同步补入 skill 名
- 社区技能集成记录增加 4 行
- 调通检查区补入验证说明

### Step 3.2: 路由验证
- `invoice-organizer`：发票/收据整理类表达
- `tailored-resume-generator`：JD 定制简历类表达
- `meeting-insights-analyzer`：会议转录/沟通模式分析类表达
- `langsmith-fetch`：LangSmith trace/debug 类表达

### Step 3.3: 收尾
- 更新 requirement / plan 状态
- 写 task log 到 `logs/tasks/`
- 检查最近修改文件的诊断

## 回滚规则

- 若新 skill 抢走已有窄技能（如 `file-organizer`、`code-reviewer`），优先降低 priority 并增加 negative keywords
- 若纯 prompt 型 skill 命中过宽，收紧 trigger keywords，不扩展 task_allow
