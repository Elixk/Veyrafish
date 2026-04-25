# Wave 1：自研轻量状态图引擎

**所属**：Phase 2 二阶段架构升级  
**前置**：veyrafish_core 基础层已建立  
**产出**：`veyrafish_core/graph.py` + `tests/test_graph.py`

---

## 1. 目标

在 `veyrafish_core` 内实现零依赖的 **StateGraph + GraphRunner**，作为后续三引擎图谱化迁移的基础。

为什么自研而不用 LangGraph：
- Veyrafish 的定位是"从零实现，不依赖任何框架"
- LangGraph 引入 LangChain 生态的大量传递依赖
- 自研图引擎是竞赛答辩的加分项
- 我们只需要图引擎最核心的 20% 能力

## 2. 核心类设计

### 2.1 GraphState（图状态基类）

```python
class GraphState:
    """图执行时的状态容器，子类可扩展字段。"""
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "GraphState": ...
```

设计要点：
- 使用 `dataclass` 或 Pydantic `BaseModel` 实现
- 必须可序列化（用于 checkpoint / resume）
- 各引擎的 `State` 类可以直接继承或适配

### 2.2 StateGraph（图定义）

```python
class StateGraph:
    def __init__(self, name: str): ...
    def add_node(self, name: str, fn: Callable[[GraphState], GraphState]): ...
    def add_edge(self, from_node: str, to_node: str): ...
    def add_conditional_edge(self, from_node: str, condition: Callable[[GraphState], str], targets: dict[str, str]): ...
    def set_entry(self, node_name: str): ...
    def set_finish(self, node_name: str): ...
    def validate(self) -> list[str]: ...  # 返回错误列表
    def get_execution_order(self) -> list[str]: ...  # 拓扑排序（线性图）
    def to_mermaid(self) -> str: ...  # 可视化导出
```

设计要点：
- 内部用 `dict[str, NodeDef]` 和 `list[EdgeDef]` 存储
- `validate()` 检查：entry/finish 已设置、所有边的 target 存在、无孤立节点
- `add_conditional_edge` 的 `condition` 函数接收当前 state，返回 target key
- `to_mermaid()` 输出 Mermaid 图语法，可直接粘贴到文档里

### 2.3 GraphRunner（图执行器）

```python
class GraphRunner:
    def __init__(self, graph: StateGraph, task_store=None): ...
    def run(self, initial_state: GraphState, task_id: str | None = None) -> GraphState: ...
    def resume(self, state: GraphState, task_id: str, from_node: str) -> GraphState: ...
```

设计要点：
- `run()` 从 entry 节点开始，按边关系依次执行，直到 finish
- 每个节点执行前后自动写入 `task_events`（如果 task_store 可用）
- 节点执行失败时自动保存当前 state 到 checkpoint（序列化到 task result）
- `resume()` 从指定节点恢复执行
- 条件边：执行 condition 函数，根据返回值选择 target

### 2.4 内部数据结构

```python
@dataclass
class NodeDef:
    name: str
    fn: Callable[[GraphState], GraphState]

@dataclass  
class EdgeDef:
    from_node: str
    to_node: str | None          # None 表示条件边
    condition: Callable | None
    targets: dict[str, str] | None  # condition 返回值 → target node
```

## 3. 任务分解

| 编号 | 任务 | 预估行数 | 说明 |
|------|------|---------|------|
| W1.1 | `GraphState` 基类 | ~30 行 | dataclass + to_dict/from_dict |
| W1.2 | `NodeDef` / `EdgeDef` 数据结构 | ~20 行 | 简单 dataclass |
| W1.3 | `StateGraph` 核心（add_node/edge/conditional_edge） | ~80 行 | 图定义 + 存储 |
| W1.4 | `StateGraph.validate()` | ~30 行 | 校验完整性 |
| W1.5 | `StateGraph.to_mermaid()` | ~25 行 | 可视化导出 |
| W1.6 | `GraphRunner.run()` | ~60 行 | 核心执行循环 |
| W1.7 | `GraphRunner` task_events 集成 | ~30 行 | 自动写入节点事件 |
| W1.8 | `GraphRunner.resume()` | ~30 行 | 断点恢复 |
| W1.9 | 单元测试 | ~150 行 | 覆盖所有场景 |

预估总量：**~450 行代码 + ~150 行测试**

## 4. 测试计划

```python
# tests/test_graph.py

class TestStateGraph:
    def test_add_node_and_edge(self): ...
    def test_validate_missing_entry(self): ...
    def test_validate_missing_finish(self): ...
    def test_validate_dangling_edge(self): ...
    def test_to_mermaid(self): ...

class TestGraphRunner:
    def test_linear_execution(self): ...
    def test_conditional_branch_true(self): ...
    def test_conditional_branch_false(self): ...
    def test_node_failure_checkpoint(self): ...
    def test_resume_from_checkpoint(self): ...
    def test_task_events_emitted(self): ...
    def test_run_without_task_store(self): ...
    def test_graph_state_serialization(self): ...
```

## 5. 验证门禁

```bash
pytest tests/test_graph.py -v     # 全部通过
pytest tests/ -q                  # 原有测试无回归
```

## 6. 回滚方式

删除 `veyrafish_core/graph.py` + `tests/test_graph.py`，不影响任何现有代码。

## 7. 与后续 Wave 的接口

- Wave 3 将使用 `StateGraph` 定义引擎的研究流程图
- Wave 3 将使用 `GraphRunner` 替代 `BaseResearchAgent.research()` 中的硬编码循环
- Wave 4 的 ForumEngine 将通过 `GraphRunner` 的 task_events 获取引擎进度
