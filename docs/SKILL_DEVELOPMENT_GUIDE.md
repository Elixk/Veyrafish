# Veyrafish Skill 开发指南

## 1. 定位

Veyrafish 的 Skill 不是一段泛化 prompt，也不是普通工具函数。一个合格 Skill 必须同时具备：

- 明确输入边界
- 明确输出 schema
- 明确决策规则
- 明确禁止事项
- 明确失败降级
- 可被单元测试验证

## 2. 最小 Contract

每个 Skill 在实现前先写清 8 个问题：

| 项 | 要求 |
|---|---|
| 目标 | 一句话说明只负责什么 |
| 适用场景 | 说明在哪个引擎、哪个阶段调用 |
| 输入定义 | 所有字段必须有含义、类型、是否必填 |
| 输出定义 | 所有字段必须有类型和约束 |
| 决策规则 | 冲突、重复、缺失、低置信度如何处理 |
| 禁止事项 | 明确不能脑补、不能越权、不能混淆事实和观点 |
| 质量检查 | 输出前如何自检 |
| 降级策略 | LLM、搜索、解析失败时返回什么 |

## 3. 代码结构

新增 Skill 时优先放在：

```text
veyrafish_core/skills/
    _models.py          # 输入/输出 Pydantic 模型
    <skill_name>.py     # Skill 实现
```

并在 `veyrafish_core/skills/__init__.py` 的默认注册表中注册。

## 4. Schema 规则

- 输入模型以 `<SkillName>Input` 命名。
- 输出模型以 `<SkillName>Output` 命名。
- LLM 输出字段必须有默认值或明确必填理由。
- 置信度字段统一使用 `0.0 ~ 1.0`。
- 证据相关输出优先保留 `conflicts`、`uncertainties`、`confidence`。
- 增量更新类输出必须保留更新痕迹，如 `retained_points`、`new_points`、`revised_points`、`change_log`。

## 5. Prompt 规则

Prompt 必须写成任务 contract，而不是角色设定。

推荐结构：

```text
你是“具体执行器名称”，不是自由写作者。

任务：
给定哪些输入，只产出哪些结果。

硬性规则：
1. 只能使用输入中明确出现的信息。
2. 遇到冲突时保留冲突，不强行融合。
3. 证据不足时保守表达，并写入 uncertainties。
4. 重复信息合并，不重复堆叠。

输出 JSON 字段：
...
```

## 6. 测试要求

每个 Skill 至少覆盖：

- metadata 能被 registry 列出
- 无依赖降级路径
- LLM/外部服务失败时不崩溃
- 输出 schema 关键字段存在
- 关键数值字段被归一化，如 `confidence`

## 7. 当前优先级

后续应优先硬化这些 Skill：

1. `llm_summarize`：已升级为首轮证据压缩 + 增量修订 contract。
2. `evidence_extract`：需要增加 source binding、claim/source 对齐、缺口分类。
3. `gap_finder`：需要区分 coverage gap、conflict gap、recency gap。
4. `query_rewrite`：需要增加工具选择规则和日期/平台约束。
5. `quality_gate`：需要从长度检查升级为按 content_type 的标准集。

## 8. Phase 2.5 Wave 1 落地要求

当前 Phase 2.5 Wave 1 实施时，应额外满足：

- `query_rewrite`：即使没有 LLM，也要给出可解释的工具选择规则与约束输出。
- `gap_finder`：输出的每个 gap 都应带 `gap_type`，避免只给笼统缺口描述。
- `quality_gate`：返回结果应明确本次实际使用的 `content_type` 标准和 criteria 集。
- `evidence_extract`：返回结果应同时保留 `gaps` 文本摘要与可机读的 `gap_details`。
- 所有新增字段都必须提供默认值或降级路径，避免破坏现有主链路。
