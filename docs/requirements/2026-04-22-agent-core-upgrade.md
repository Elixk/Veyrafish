# Veyrafish Agent 核心升级需求冻结

日期：2026-04-22
运行模式：`/vibe`

## 1. Goal

将三引擎（Insight/Media/Query）的高度重复代码统一为共享基类，同时引入 OpenAI 原生结构化输出和 Function Calling，提升代码可维护性和 LLM 输出可靠性。

## 2. Deliverables

- `veyrafish_core/` 新包：统一 LLM 客户端 + 统一节点基类 + 共享 Agent 基类 + Pydantic 输出模型
- 三引擎 `agent.py` 瘦身为继承薄壳（各 < 300 行）
- LLM 客户端新增 `invoke_structured()` 和 `invoke_with_tools()` 方法
- 搜索/总结/反思节点支持结构化输出（带回退机制）
- 分阶段执行计划（已冻结）

## 3. Constraints

- ReportEngine 不参与本轮重构（结构差异过大，保持独立）
- ForumEngine 不参与本轮重构（监控型，非 Agent 链路）
- 所有旧接口名称保留向后兼容（`DeepSearchAgent` 类名可通过 alias 保留）
- `pytest tests/` 全部通过是每个阶段的硬性门禁
- 结构化输出失败时必须有回退到旧 JSON 解析的路径
- 不引入新的外部框架（不加 LangGraph/CrewAI）

## 4. Acceptance Criteria

### 代码层面
- 三引擎 `agent.py` 行数各减少 60%+
- 三引擎 `llms/base.py` 各 < 10 行（re-export）
- `veyrafish_core/base_research_agent.py` 包含所有共享逻辑
- `veyrafish_core/output_models.py` 定义 Pydantic 模型，配合 OpenAI `response_format`

### 功能层面
- `invoke_structured(SearchOutput)` 可返回合法 Pydantic 对象
- 结构化失败时自动回退旧路径，不影响功能
- 三引擎的 `task_id` + `_emit` + 断点恢复全部统一

### 测试层面
- 旧测试 61/61 不回归
- 新增 `tests/test_output_models.py`（Pydantic 模型验证）
- 新增 `tests/test_base_agent.py`（基类共享方法验证）

## 5. Non-goals

- 不改造 ReportEngine 的节点链
- 不引入 LangGraph 状态图
- 不做 MCP 工具服务化
- 不做 Skill 架构拆分（后续阶段）
- 不做评估系统（后续阶段）

## 6. Staged Delivery

| 阶段 | 范围 | 前置条件 |
|------|------|---------|
| Stage A | `veyrafish_core` 基础层（LLM 客户端 + 节点基类） | 无 |
| Stage B | 共享 Agent 基类 + 三引擎瘦身 | Stage A 完成 |
| Stage C | 结构化输出 + Function Calling | Stage B 完成 |
| Stage V | 验收 + 文档更新 | Stage C 完成 |

详细执行计划见：`docs/plans/2026-04-22-agent-core-upgrade-execution-plan.md`
