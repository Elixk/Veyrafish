# Vibe 智能调用与复杂 Skill 接入指南

> 目标：讲清楚两件事——  
> 1) Vibe 到底如何“智能调用” skill；  
> 2) 多子技能 + commands/hooks/agents 这类复杂 skill，怎样才算“接入成功且可调用”。

---

## 1. Vibe 是如何智能调用 Skill 的

Vibe 不是“扫目录即生效”，而是**受治理路由**。核心由三层组成：

1. **候选生成层**
   - 来源于 `pack-manifest` 的 pack 与候选 skill。
   - 来源于关键词索引与别名映射（如 `skill-keyword-index`、`skill-alias-map`）。
   - 来源于自定义准入清单（`custom-workflows.json` / `custom-skills.json`）。

2. **打分与阈值层**
   - 按意图、关键词、工作区信号等权重综合评分。
   - 与阈值比较后决定：自动路由 / 需要确认 / 回退策略。

3. **治理与边界层**
   - 显式用户选择优先（用户点名 skill）。
   - canonical `vibe` 与官方 workflow core 具备优先级。
   - 自定义能力只能“参与路由”，不能夺取 route authority。

一句话：**“目录里有 skill” ≠ “路由会调用 skill”；必须先进入受治理候选池。**

---

## 2. 复杂 Skill（多子技能 + commands/hooks/agents）的本质

以 `pua` 这类仓库为例，它不是单一 `SKILL.md`，而是一个技能系统：

- `skills/`：多个子技能入口（如 `pua`、`pua-en`、`p9` 等）
- `commands/`：手动触发命令
- `hooks/`：会话/工具后置触发逻辑
- `agents/`：子代理角色模板
- `scripts/`：辅助脚本

### 关键认知

- **Vibe 的基础调用入口仍然是 `SKILL.md`**。  
- `commands/hooks/agents/scripts` 是能力增强层，不会因为文件存在就自动被主路由调用。  
- 复杂 skill 需要定义一个“主入口 skill”（通常顶层 `SKILL.md`），由它描述何时触发、如何分流到子技能体系。

---

## 3. 什么叫“正常添加了该 Skill”

请按“3 层验收”判断，而不是只看文件是否复制成功。

### A. 结构验收（文件层）

至少满足：

- 有主入口：`<skill>/SKILL.md`
- 有能力资源：`scripts/`、`references/`、`commands/`、`hooks/`、`agents/`（按技能类型可选）
- 编码可读（UTF-8），`SKILL.md` frontmatter 可解析

### B. 准入验收（路由层）

要进入可调用态，必须满足其一：

1. **官方路由链路**：已被 canonical pack/关键词索引纳入候选；或  
2. **自定义准入链路**：在 `config/custom-workflows.json` 或 `config/custom-skills.json` 正确声明。

若走自定义准入，必须有这些字段（缺失即无效）：

- `id`
- `path`
- `keywords`
- `intent_tags`
- `non_goals`
- `requires`

并建议：

- `trigger_mode`：默认 `advisory`
- `priority`：建议低于 canonical 核心链路（通常不超过 89）

### C. 运行验收（调用层）

- 能执行至少一个“可验证调用”：
  - 脚本型：`python ... --help` / smoke test
  - 命令/Hook 型：关键结构校验 + 最小触发链路演练
- `check --deep` 后不应出现：
  - `custom_manifest_invalid`
  - `custom_dependencies_missing`

---

## 4. 复杂 Skill 推荐接入模式（实践模板）

### 4.1 目录落地

建议结构：

```text
bundled/skills/<skill-id>/
├── SKILL.md                  # 主入口（必须）
├── skills/                   # 多子技能（可选）
├── commands/                 # 命令集（可选）
├── hooks/                    # Hook 逻辑（可选）
├── agents/                   # 子代理模板（可选）
├── scripts/                  # 脚本（可选）
├── references/               # 参考文档（可选）
└── requirements.txt          # 依赖（建议）
```

### 4.2 路由声明（自定义推荐）

若该 skill 不在 canonical 默认路由里，建议走受治理声明：

- `config/custom-workflows.json`（偏流程）
- `config/custom-skills.json`（偏技能）

最小示例：

```json
{
  "version": 1,
  "skills": [
    {
      "id": "pua",
      "path": "bundled/skills/pua",
      "enabled": true,
      "trigger_mode": "advisory",
      "keywords": ["pua", "pip", "高能动性", "别放弃"],
      "intent_tags": ["debug", "coding", "review"],
      "preferred_stages": ["plan_execute"],
      "requires": ["vibe"],
      "priority": 60,
      "non_goals": ["general chat"]
    }
  ]
}
```

> 注意：`path` 必须在目标根目录内，且最终能解析到 `SKILL.md`。

---

## 5. Vibe 实际如何决定“调不调用”

可按下面顺序理解：

1. 任务进入路由器，先判任务类型与上下文信号。  
2. 从 pack + 索引 + 自定义 manifest 生成候选 skill。  
3. 按权重打分并做阈值判定（自动/确认/回退）。  
4. 应用治理规则（显式用户选择优先、canonical 优先级稳定）。  
5. 输出最终 skill，进入执行阶段。  

对复杂 skill 而言，主路由命中的是“主入口 skill”，然后再由该 skill 内容引导其子模式（如子技能、命令、hook 协同）。

---

## 6. 常见失败场景与排查

### 场景 1：文件都在，但就是不触发

优先检查：

1. 是否有主入口 `SKILL.md`  
2. 是否已进入准入（canonical 或 custom manifest）  
3. `keywords/intent_tags/non_goals` 是否过窄或冲突  
4. `trigger_mode` 是否设成 `explicit_only`

### 场景 2：声明了 manifest，但判定无效

常见原因：

- JSON 解析失败
- 顶层集合键错误（`workflows` / `skills`）
- 缺必填字段（尤其 `requires`）
- `path` 越界或 `SKILL.md` 不存在

### 场景 3：更新后“看似丢失”

多数不是丢失，而是依赖断裂：

- `requires` 指向的 skill 在当前 profile 不再可用
- 结果表现为 `custom_dependencies_missing`

---

## 7. 给团队的统一接入流程（建议长期执行）

每次新增 skill 固定执行：

1. 完整镜像：主入口 + 关键资源（scripts/examples/commands/hooks/agents）  
2. 依赖落盘：`requirements.txt`（或等价依赖文件）  
3. 路由准入：进入 canonical（更新 `pack-manifest` + `skill-keyword-index` + `skill-routing-rules`）或 custom manifest  
4. 可执行校验：至少 1 条真实触发/运行检查  
5. 路由验证：用 `vgo_cli route` 确认 `selected.skill` 命中正确  
6. `check --deep`：确认无 `custom_manifest_invalid` / `custom_dependencies_missing`  
7. 文档登记：记录来源、归属、资源、验证状态

---

## 8. 结论（最重要的一条）

在 Vibe 里，**“可见”不等于“可调”**。  
真正的“已接入可调用”必须同时满足：

- 有主入口（`SKILL.md`）  
- 有准入（canonical 或 custom manifest）  
- 有验证（可执行检查 + `check --deep` 状态健康）

只要按这个标准做，复杂 skill 也能稳定进入智能调用链路。

