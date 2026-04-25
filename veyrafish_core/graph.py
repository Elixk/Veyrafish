# -*- coding: utf-8 -*-
"""
veyrafish_core.graph — 自研轻量状态图引擎

提供 StateGraph / GraphRunner / GraphState 三个核心组件，
用于将 Agent 的研究流程从硬编码调用链升级为显式状态图执行。

设计原则：
- 零外部框架依赖（纯 Python 标准库 + loguru）
- 图定义与执行分离（StateGraph 定义，GraphRunner 执行）
- 支持条件分支、段落级 checkpoint 恢复
- 与 task_store 集成：自动写入 node_start / node_done / error 事件
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

# 可选：与 task_store 集成
try:
    from task_store import get_task_store as _get_task_store  # type: ignore
    _TASK_STORE_AVAILABLE = True
except Exception:
    _TASK_STORE_AVAILABLE = False
    _get_task_store = None  # type: ignore


# ---------------------------------------------------------------------------
# GraphState — 图状态基类
# ---------------------------------------------------------------------------

class GraphState(ABC):
    """
    图执行时的状态容器基类。

    各引擎的 State 类可以直接继承此类，或通过适配器使用。
    必须实现 to_dict / from_dict 以支持 checkpoint 序列化。
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """将状态序列化为字典（用于 checkpoint 持久化）。"""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphState":
        """从字典恢复状态（用于 checkpoint 恢复）。"""

    def copy(self) -> "GraphState":
        """返回当前状态的浅拷贝（子类可 override 做深拷贝）。"""
        return self.__class__.from_dict(self.to_dict())


class DictGraphState(GraphState):
    """
    通用字典状态，用于不需要强类型的场景（测试 / 轻量使用）。
    """

    def __init__(self, **kwargs: Any) -> None:
        self._data: Dict[str, Any] = dict(kwargs)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, **kwargs: Any) -> None:
        self._data.update(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DictGraphState":
        return cls(**data)

    def __repr__(self) -> str:  # pragma: no cover
        return f"DictGraphState({self._data!r})"


# ---------------------------------------------------------------------------
# 内部数据结构
# ---------------------------------------------------------------------------

@dataclass
class _NodeDef:
    name: str
    fn: Callable[[GraphState], GraphState]


@dataclass
class _EdgeDef:
    from_node: str
    # 普通边：to_node 有值；条件边：to_node 为 None，condition/targets 有值
    to_node: Optional[str] = None
    condition: Optional[Callable[[GraphState], str]] = None
    targets: Optional[Dict[str, str]] = None  # condition 返回值 → 目标节点名

    @property
    def is_conditional(self) -> bool:
        return self.condition is not None


# ---------------------------------------------------------------------------
# StateGraph — 图定义
# ---------------------------------------------------------------------------

class StateGraph:
    """
    轻量有向状态图，用于定义 Agent 的执行流程。

    用法::

        graph = StateGraph("insight_research")
        graph.add_node("generate_structure", fn_generate)
        graph.add_node("process_paragraph", fn_process)
        graph.add_node("format_report", fn_format)

        graph.set_entry("generate_structure")
        graph.add_edge("generate_structure", "process_paragraph")
        graph.add_conditional_edge(
            "process_paragraph",
            condition=lambda s: "next" if s.has_more else "done",
            targets={"next": "process_paragraph", "done": "format_report"},
        )
        graph.set_finish("format_report")
        errors = graph.validate()
    """

    def __init__(self, name: str = "graph") -> None:
        self.name = name
        self._nodes: Dict[str, _NodeDef] = {}
        self._edges: List[_EdgeDef] = []
        self._entry: Optional[str] = None
        self._finish: Optional[str] = None

    # ------------------------------------------------------------------
    # 构建 API
    # ------------------------------------------------------------------

    def add_node(self, name: str, fn: Callable[[GraphState], GraphState]) -> "StateGraph":
        """注册一个节点及其处理函数。"""
        if name in self._nodes:
            raise ValueError(f"[StateGraph:{self.name}] 节点 '{name}' 已存在")
        self._nodes[name] = _NodeDef(name=name, fn=fn)
        return self

    def add_edge(self, from_node: str, to_node: str) -> "StateGraph":
        """添加普通（无条件）边。"""
        self._edges.append(_EdgeDef(from_node=from_node, to_node=to_node))
        return self

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[GraphState], str],
        targets: Dict[str, str],
    ) -> "StateGraph":
        """
        添加条件边。

        condition 接收当前 state，返回一个 key 字符串；
        targets 是 key → 目标节点名 的映射。
        """
        self._edges.append(_EdgeDef(
            from_node=from_node,
            condition=condition,
            targets=targets,
        ))
        return self

    def set_entry(self, node_name: str) -> "StateGraph":
        """设置图的入口节点。"""
        self._entry = node_name
        return self

    def set_finish(self, node_name: str) -> "StateGraph":
        """设置图的终止节点（执行到此节点后图运行结束）。"""
        self._finish = node_name
        return self

    # ------------------------------------------------------------------
    # 验证
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """
        校验图定义的完整性。

        返回错误列表；空列表表示图定义有效。
        """
        errors: List[str] = []

        if not self._entry:
            errors.append("未设置入口节点（调用 set_entry()）")
        elif self._entry not in self._nodes:
            errors.append(f"入口节点 '{self._entry}' 未在 add_node() 中注册")

        if not self._finish:
            errors.append("未设置终止节点（调用 set_finish()）")
        elif self._finish not in self._nodes:
            errors.append(f"终止节点 '{self._finish}' 未在 add_node() 中注册")

        # 检查所有边的节点是否存在
        for edge in self._edges:
            if edge.from_node not in self._nodes:
                errors.append(f"边的源节点 '{edge.from_node}' 未注册")
            if edge.is_conditional:
                if not edge.targets:
                    errors.append(f"节点 '{edge.from_node}' 的条件边缺少 targets 映射")
                else:
                    for key, target in edge.targets.items():
                        if target not in self._nodes:
                            errors.append(
                                f"条件边 '{edge.from_node}' 的目标节点 '{target}'（key='{key}'）未注册"
                            )
            else:
                if edge.to_node not in self._nodes:
                    errors.append(f"边的目标节点 '{edge.to_node}' 未注册")

        return errors

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _get_next_node(self, current_node: str, state: GraphState) -> Optional[str]:
        """根据当前节点和状态，返回下一个节点名；到达 finish 或无后继返回 None。"""
        if current_node == self._finish:
            return None

        for edge in self._edges:
            if edge.from_node != current_node:
                continue
            if edge.is_conditional:
                key = edge.condition(state)  # type: ignore[misc]
                next_node = edge.targets.get(key) if edge.targets else None  # type: ignore[union-attr]
                if next_node is None:
                    raise RuntimeError(
                        f"[StateGraph:{self.name}] 节点 '{current_node}' 的条件边 "
                        f"返回了未知 key='{key}'，合法值为 {list(edge.targets.keys())}"  # type: ignore[union-attr]
                    )
                return next_node
            else:
                return edge.to_node

        # 没有任何匹配边
        if current_node == self._finish:
            return None
        raise RuntimeError(
            f"[StateGraph:{self.name}] 节点 '{current_node}' 没有出边，"
            "且不是 finish 节点"
        )

    def to_mermaid(self) -> str:
        """导出 Mermaid 流图语法，方便写入文档可视化。"""
        lines = ["graph TD"]
        entry_mark = f"[/{self._entry}/]" if self._entry else ""
        finish_mark = f"([{self._finish}])" if self._finish else ""

        for node_name in self._nodes:
            if node_name == self._entry:
                lines.append(f"    {node_name}{entry_mark}")
            elif node_name == self._finish:
                lines.append(f"    {node_name}{finish_mark}")

        for edge in self._edges:
            if edge.is_conditional and edge.targets:
                for key, target in edge.targets.items():
                    lines.append(f"    {edge.from_node} -->|{key}| {target}")
            else:
                lines.append(f"    {edge.from_node} --> {edge.to_node}")

        return "\n".join(lines)

    def node_names(self) -> List[str]:
        """返回所有已注册节点名称列表。"""
        return list(self._nodes.keys())

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"StateGraph(name='{self.name}', "
            f"nodes={list(self._nodes.keys())}, "
            f"entry='{self._entry}', finish='{self._finish}')"
        )


# ---------------------------------------------------------------------------
# GraphRunner — 图执行器
# ---------------------------------------------------------------------------

class GraphRunner:
    """
    执行 StateGraph，支持：
    - 顺序执行（run）
    - 指定节点恢复执行（resume）
    - 节点事件自动写入 task_store
    - 异常时自动保存 checkpoint（序列化 state 到 task result）
    """

    def __init__(
        self,
        graph: StateGraph,
        task_store: Any = None,
        max_steps: int = 500,
    ) -> None:
        """
        Args:
            graph: 已配置并通过 validate() 的 StateGraph 实例
            task_store: TaskStore 实例（可选）；传 None 时禁用事件记录
            max_steps: 防止死循环的最大节点执行步数（默认 500）
        """
        errors = graph.validate()
        if errors:
            raise ValueError(
                f"StateGraph '{graph.name}' 验证失败：\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        self._graph = graph
        self._task_store = task_store
        self._max_steps = max_steps

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def run(
        self,
        initial_state: GraphState,
        task_id: Optional[str] = None,
    ) -> GraphState:
        """
        从入口节点开始执行图，直到 finish 节点。

        Args:
            initial_state: 初始状态
            task_id: 可选，关联 task_store 事件记录

        Returns:
            执行完毕后的最终状态
        """
        return self._execute(
            state=initial_state,
            start_node=self._graph._entry,  # type: ignore[arg-type]
            task_id=task_id,
        )

    def resume(
        self,
        state: GraphState,
        from_node: str,
        task_id: Optional[str] = None,
    ) -> GraphState:
        """
        从指定节点恢复执行（用于断点续跑）。

        Args:
            state: 上次 checkpoint 时保存的状态
            from_node: 恢复执行的起始节点名
            task_id: 可选，关联 task_store 事件记录

        Returns:
            执行完毕后的最终状态
        """
        if from_node not in self._graph._nodes:
            raise ValueError(
                f"[GraphRunner] 恢复节点 '{from_node}' 未在图 '{self._graph.name}' 中注册"
            )
        return self._execute(state=state, start_node=from_node, task_id=task_id)

    # ------------------------------------------------------------------
    # 内部执行逻辑
    # ------------------------------------------------------------------

    def _execute(
        self,
        state: GraphState,
        start_node: str,
        task_id: Optional[str],
    ) -> GraphState:
        current_node = start_node
        step = 0

        logger.info(
            f"[GraphRunner:{self._graph.name}] 开始执行，"
            f"起始节点='{current_node}'，task_id={task_id}"
        )

        while current_node is not None:
            if step >= self._max_steps:
                raise RuntimeError(
                    f"[GraphRunner:{self._graph.name}] 执行步数超过上限 {self._max_steps}，"
                    "疑似死循环，已中止"
                )

            node_def = self._graph._nodes[current_node]
            self._emit_event(task_id, "node_start", node_name=current_node)
            t0 = time.monotonic()

            try:
                state = node_def.fn(state)
            except Exception as exc:
                elapsed = time.monotonic() - t0
                logger.error(
                    f"[GraphRunner:{self._graph.name}] 节点 '{current_node}' 执行失败 "
                    f"({elapsed:.2f}s)：{exc}"
                )
                self._emit_event(
                    task_id, "error",
                    node_name=current_node,
                    detail={"error": str(exc), "elapsed_s": round(elapsed, 3)},
                )
                self._save_checkpoint(task_id, current_node, state)
                raise

            elapsed = time.monotonic() - t0
            logger.debug(
                f"[GraphRunner:{self._graph.name}] 节点 '{current_node}' 完成 ({elapsed:.2f}s)"
            )
            self._emit_event(
                task_id, "node_done",
                node_name=current_node,
                detail={"elapsed_s": round(elapsed, 3)},
            )

            try:
                next_node = self._graph._get_next_node(current_node, state)
            except RuntimeError as routing_err:
                logger.error(f"[GraphRunner:{self._graph.name}] 路由失败：{routing_err}")
                self._emit_event(
                    task_id, "error",
                    node_name=current_node,
                    detail={"routing_error": str(routing_err)},
                )
                raise

            current_node = next_node
            step += 1

        logger.info(
            f"[GraphRunner:{self._graph.name}] 执行完成，共 {step} 步，task_id={task_id}"
        )
        return state

    # ------------------------------------------------------------------
    # task_store 事件记录
    # ------------------------------------------------------------------

    def _emit_event(
        self,
        task_id: Optional[str],
        event_type: str,
        node_name: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        """向 task_store 写入节点执行事件；不可用或 task_id 为 None 时静默跳过。"""
        if not task_id:
            return
        store = self._task_store
        if store is None and _TASK_STORE_AVAILABLE and _get_task_store is not None:
            try:
                store = _get_task_store()
            except Exception:
                return
        if store is None:
            return
        try:
            store.add_event(
                task_id=task_id,
                event_type=event_type,
                node_name=node_name,
                detail=detail,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[GraphRunner] 写入事件失败，忽略继续：{exc}")

    def _save_checkpoint(
        self,
        task_id: Optional[str],
        current_node: str,
        state: GraphState,
    ) -> None:
        """节点执行失败时，将当前状态序列化保存为 checkpoint。"""
        if not task_id:
            return
        store = self._task_store
        if store is None and _TASK_STORE_AVAILABLE and _get_task_store is not None:
            try:
                store = _get_task_store()
            except Exception:
                return
        if store is None:
            return
        try:
            checkpoint = {
                "checkpoint_node": current_node,
                "checkpoint_time": datetime.now(timezone.utc).isoformat(),
                "state": state.to_dict(),
            }
            store.update_task(task_id, "error", result=checkpoint)
            logger.info(
                f"[GraphRunner] 已保存 checkpoint：task_id={task_id}，节点='{current_node}'"
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[GraphRunner] 保存 checkpoint 失败，忽略：{exc}")
