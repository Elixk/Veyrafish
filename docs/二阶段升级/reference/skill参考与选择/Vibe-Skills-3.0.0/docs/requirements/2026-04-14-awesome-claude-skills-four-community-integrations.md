# Requirement: awesome-claude-skills 四个社区 Skill 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-awesome-claude-skills-four-community-integrations |
| 状态 | frozen |
| 创建日期 | 2026-04-14 |
| 作者 | AI Agent (governed) |

## 1. 背景

用户已将 `awesome-claude-skills` 手动下载到 `_temp_community_skills/awesome-claude-skills/`，并要求按 `skills管理和安装指南.md` 的规范，把其中“尚未接入、且值得接入”的 skill 纳入本系统。

经过人工筛选，本轮只接入以下四个：

1. `invoice-organizer`
2. `tailored-resume-generator`
3. `meeting-insights-analyzer`
4. `langsmith-fetch`

## 2. 目标

将以上四个 skill 以社区 skill 形式接入到当前仓库，并满足“已接入可调用”的最低标准：

1. 镜像到 `bundled/skills/<skill-id>/`
2. 进入 canonical 路由
3. 更新 `skills管理和安装指南.md`
4. 对代表性表达进行路由验证
5. 记录 task log 到 `logs/tasks/`

## 3. 类型判断

这四个 skill 当前都以单 `SKILL.md` 为主入口：

- `invoice-organizer`：单入口；带 shell 示例，但无 bundled scripts
- `tailored-resume-generator`：单入口；纯 prompt/workflow 型
- `meeting-insights-analyzer`：单入口；纯分析型
- `langsmith-fetch`：单入口；依赖外部 `langsmith-fetch` CLI，但未自带本地脚本

因此本轮统一按 **单入口 community skill** 接入，不伪造额外 `scripts/` 或 `requirements.txt`。

## 4. 分类判断

- `invoice-organizer` → 第 21 类：其他工具与实用技能
- `tailored-resume-generator` → 第 20 类：规划与知识管理
- `meeting-insights-analyzer` → 第 21 类：其他工具与实用技能
- `langsmith-fetch` → 第 4 类：代码开发与审查

## 5. 来源与许可

- 来源仓库：`awesome-claude-skills`
- 仓库地址：待在记录中补为对应 GitHub 仓库地址
- 许可：Apache-2.0（依据 upstream `README.md`）

## 6. 验收标准

- [x] 四个 skill 目录已创建且 `SKILL.md` 存在
- [x] `config/pack-manifest.json` 已新增四个 canonical pack
- [x] `config/skill-keyword-index.json` 已新增四个技能关键词
- [x] `config/skill-routing-rules.json` 已新增四个技能规则
- [x] `skills管理和安装指南.md` 已补充分类与社区记录
- [x] `vgo_cli route` 已对 `tailored-resume-generator`、`meeting-insights-analyzer`、`langsmith-fetch` 命中验证
- [x] `invoice-organizer` 已接入 canonical，但与 `spreadsheet` 在“CSV 导出”表达下存在路由重叠，已记录为已知边界
- [x] `logs/tasks/` 已写入本轮 task log
- [x] 无新增文档/结构错误

## 7. 约束

- 不接入已存在于 bundled/skills 的 skill
- 不接入本轮评估为低质量或高合规风险的候选
- 不伪造上游不存在的脚本或依赖文件
- 对 `langsmith-fetch` 明确记录其外部 CLI 前置依赖，不假装本仓库内自带执行面
