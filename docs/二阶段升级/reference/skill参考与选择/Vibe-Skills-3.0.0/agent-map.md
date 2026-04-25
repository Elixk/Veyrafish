# Vibe-Skills Agent Map

> 目标：说明本仓库内有哪些 agent、分别负责什么、哪些是主 agent、哪些是 skill 内部 agent，以及哪些 subagent 仅在 XL 下调用。

## 1) 主 Agent（Primary / 入口级）

这些是宿主侧主入口 agent，负责把用户任务带入 `vibe` 受控运行时（governed runtime）。

### A. `vibe-plan`（主 agent）
- 位置：`config/opencode/agents/vibe-plan.md`
- 定位：Plan-first，优先完成需求澄清、需求冻结与执行计划。
- 核心职责：
  - 推进 `skeleton_check`、`deep_interview`、`requirement_doc`、`xl_plan`
  - 明确约束、验收标准、验证方案
  - 不建立第二路由或第二运行时真相面

### B. `vibe-implement`（主 agent）
- 位置：`config/opencode/agents/vibe-implement.md`
- 定位：Implementation-first，在已冻结需求/计划下执行实现。
- 核心职责：
  - 按冻结计划实施改动
  - 执行验证与清理，不跳过证据
  - 不做无证据完成声明

### C. `vibe-review`（主 agent）
- 位置：`config/opencode/agents/vibe-review.md`
- 定位：Review-first，缺陷与回归优先。
- 核心职责：
  - 先报问题（bug/回归/缺测/证据缺口），后摘要
  - 对弱证据保持阻断态度

---

## 2) 通用角色模板 Agent（模板级，不是直接入口）

这些模板提供角色能力，通常由主 agent 或编排逻辑按需调用。

### A. `planner` 模板
- 位置：`agents/templates/planner.md`
- 负责：范围边界、依赖风险、里程碑拆解、回滚策略。

### B. `debugger` 模板
- 位置：`agents/templates/debugger.md`
- 负责：复现问题、定位根因、最小安全修复、验证闭环。

### C. `reviewer` 模板
- 位置：`agents/templates/reviewer.md`
- 负责：按验收标准检查行为、识别回归与边界缺口、严重度分级。

### D. `security-reviewer` 模板
- 位置：`agents/templates/security-reviewer.md`
- 负责：泄漏/注入/鉴权风险、配置安全默认值、缓解措施清单。

---

## 3) 仓库级社区 Agent 资产（Repo-scoped）

这类 agent 以“prompt 资产”的形式被收录到仓库里，便于可追溯、可复用，但它们：

- 不是宿主默认主入口（不等同于 `vibe-plan` / `vibe-implement` / `vibe-review`）
- 不等同于 XL 编排下的 `spawn_agent` 子代理（后者属于运行时内部拓扑）

### A. claude-scholar agent prompts
- 位置：`agents/community/claude-scholar/`
- 包含（15 个）：
  - 研究/写作：`literature-reviewer`, `literature-reviewer-obsidian`, `paper-miner`, `rebuttal-writer`, `research-knowledge-curator-obsidian`
  - 工程/质量：`dev-planner`, `code-reviewer`, `bug-analyzer`, `build-error-resolver`, `tdd-guide`, `architect`, `refactor-cleaner`
  - 其他：`ui-sketcher`, `kaggle-miner`, `story-generator`

---

## 4) Skill 内部 Agent（Skill-scoped）

这类 agent 只在对应 skill 的内部工作流中生效，不是全局默认主入口。

### A. PUA skill 内部分层 agent
- 位置：`bundled/skills/pua/agents/`
- 包含：
  - `cto-p10`：战略层、组织拓扑、跨 P9 仲裁（不写 Task Prompt）
  - `tech-lead-p9`：任务拆解、并行调度、验收闭环（不直接写业务代码）
  - `senior-engineer-p7`：方案先行的技术实施与自审（受 P8 管理）
- 典型调用关系：
  - `P10 -> P9 -> P8 -> P7`
  - 强调管理边界与层级职责，不鼓励越权降维

### B. Digital Brain automation agents 模块
- 位置：`bundled/skills/digital-brain/agents/AGENTS.md`
- 性质：脚本自动化助手（如 weekly_review/content_ideas 等），偏任务自动化，不是治理总控 agent。

### C. `subagent-driven-development` 内部子代理流程
- 位置：`bundled/skills/subagent-driven-development/SKILL.md`
- 包含角色：
  - implementer subagent
  - spec reviewer subagent
  - code quality reviewer subagent
  - final reviewer（收尾）
- 特点：同会话逐任务派发 + 双阶段评审（先规范符合，再代码质量）。
- 边界：该 skill 明确不作为 XL 团队编排主执行器。

---

## 5) 哪些是“主 Agent”

按仓库当前定义，**主 agent**可归纳为两层：

1. **运行时主控（逻辑主 agent）**
   - `vibe` 受控运行时本身（root_governed lane）是最终治理 owner。
   - 拥有阶段顺序、需求/计划冻结、最终完成声明权。

2. **宿主入口主 agent（配置主 agent）**
   - `vibe-plan`
   - `vibe-implement`
   - `vibe-review`

> 简化理解：`vibe` 是总控 authority，三个 `vibe-*` 是不同工作偏好的主入口外观。

---

## 6) 仅在 XL 下会调用的 Subagent（重点）

依据 `protocols/team.md` 与 `protocols/runtime.md`：

### A. XL 多代理编排子代理（仅 XL）
- 触发条件：任务 grade 判定为 `XL`，进入 stage 5 `plan_execute` 的团队编排路径。
- 调用 API（内部）：`spawn_agent` / `send_input` / `wait` / `close_agent`
- 运行特征：
  - wave-sequential（波次串行）
  - 波次内仅对独立单元做有界并行
  - 子代理提示词必须以 `$vibe` 结尾
  - 子 lane 为 `child_governed`，不得创建第二份需求/计划真相面

### B. XL 下的 specialist dispatch 子代理（仅 XL 场景启用并受限）
- 前提：已在冻结计划中 root 批准（`approved_dispatch`）。
- 约束：
  - 必须是有界子任务
  - 必须带 phase/lane/write-scope/review-mode
  - 未批准的仅可作为 `local_suggestion` 上报，不得自行激活

### C. XL Dialectic 团队子代理（仅 XL 团队模式）
- 在辩证智囊团模式下，XL 形态可并行 4 个 thinker agent 做结构化对辩与综合。
- L 级可有顺序双 agent 适配，但不属于 XL 并行子代理窗口。

---

## 7) 快速判别表（实操）

- 你在用 `vibe-plan / vibe-implement / vibe-review`：这是主 agent 入口。
- 你在某个 skill 目录下看到 `agents/`：这是 skill 内部 agent，不自动升级为全局主 agent。
- 你看到 `spawn_agent/send_input/wait/close_agent` 波次并行：这是 XL 子代理编排。
- 你看到 child lane 在写第二份 requirements/plans：这是违规（应由 root 保持唯一真相面）。

