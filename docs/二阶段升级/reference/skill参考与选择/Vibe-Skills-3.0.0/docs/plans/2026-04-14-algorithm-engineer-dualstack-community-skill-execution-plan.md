# Execution Plan: algorithm-engineer-dualstack 社区 Skill 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-algorithm-engineer-dualstack-community-skill-execution-plan |
| 状态 | completed |
| 需求文档 | docs/requirements/2026-04-14-algorithm-engineer-dualstack-community-skill.md |
| 内部等级 | L（serial native execution） |
| 创建日期 | 2026-04-14 |

## Wave 1: Skill 镜像

### Step 1.1: 建立主入口目录
- 创建 `bundled/skills/algorithm-engineer-dualstack/`
- 将 `算法skill.md` 作为主入口内容镜像为 `SKILL.md`

### Step 1.2: 结构判断
- 保持单入口 Skill 形态
- 不补不存在的 `scripts/` / `references/` / `requirements.txt`

## Wave 2: Canonical 路由接入

### Step 2.1: 更新 `config/pack-manifest.json`
- 新增 community pack
- 设置保守优先级
- 允许 `planning` / `coding` / `research`

### Step 2.2: 更新 `config/skill-keyword-index.json`
- 补充“算法工程 / 双栈 / 调度 / 深度学习 / 图像算法 / 路径规划 / MATLAB / Python”相关关键词

### Step 2.3: 更新 `config/skill-routing-rules.json`
- 设置 `task_allow`
- 设置正向与负向关键词
- 将 canonical task 偏好收敛到 `coding` / `planning`

## Wave 3: 文档与验证

### Step 3.1: 更新 `skills管理和安装指南.md`
- 第 5 类补入 `algorithm-engineer-dualstack` *(Community)*
- 社区技能集成记录补入来源、归属、许可、目录、包含资源

### Step 3.2: 路由验证
- 用 `vgo_cli route` 验证代表性 prompt 是否命中该 Skill

### Step 3.3: 质量检查
- 运行最近编辑文件的诊断检查
- 完成 requirement / plan 收尾

## 回滚规则

- 若算法类意图被过度误触发，则优先降低 priority 并增加 negative keywords
- 若路由与现有窄领域技能冲突，则收紧 trigger_keywords，不扩大 skill_candidates
