# -*- coding: utf-8 -*-
"""
veyrafish_core.base_research_agent — 三引擎共享 Agent 基类

将 InsightEngine / MediaEngine / QueryEngine 三个 DeepSearchAgent 中
约 90% 的相同代码提取到此基类。子类只需实现少量抽象方法。

抽象方法（子类必须实现）
-------------------------
_initialize_llm()            → LLMClient
_initialize_search_agency()  → Any（Bocha / Tavily / MediaCrawlerDB）
_initialize_nodes()          → None（注入节点）
_create_initial_state()      → Any（各引擎自有 State 实例）
execute_search_tool()        → Any（调用各引擎搜索工具，返回原始响应）
_normalize_search_response() → list[dict]（将原始响应标准化为统一 dict 列表）
_get_content_max_length()    → int（传给 format_search_results_for_prompt 的截断长度）

可覆写的钩子方法（有默认实现）
------------------------------
_build_search_kwargs()       → dict（引擎特有的额外搜索参数）
_record_search_results()     → None（将结果写入 paragraph.research）
"""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from veyrafish_core.llm_client import LLMClient
from veyrafish_core.utils import format_search_results_for_prompt
from veyrafish_core.graph import DictGraphState, GraphRunner, StateGraph

# EvidenceStore 可选（降级时静默跳过）
try:
    from veyrafish_core.evidence_store import get_evidence_store as _get_evidence_store  # type: ignore
    from veyrafish_core.output_models import Evidence as _Evidence
    _EVIDENCE_STORE_AVAILABLE = True
except Exception:  # pragma: no cover
    _EVIDENCE_STORE_AVAILABLE = False
    _get_evidence_store = None  # type: ignore
    _Evidence = None  # type: ignore

# task_store 可选（降级时静默跳过进度事件）
try:
    from task_store import get_task_store as _get_task_store  # type: ignore
    _TASK_STORE_AVAILABLE = True
except Exception:  # pragma: no cover
    _TASK_STORE_AVAILABLE = False
    _get_task_store = None  # type: ignore

# SkillRegistry 可选（Wave 2.5 深接线；降级时回退到原节点逻辑）
try:
    from veyrafish_core.skill import SkillContext
    from veyrafish_core.skills import default_registry as _DEFAULT_SKILL_REGISTRY
    from veyrafish_core.skills._models import (
        EvidenceExtractInput,
        GapInput,
        QualityGateInput,
        QueryRewriteInput,
        SummarizeInput,
    )
    _SKILL_REGISTRY_AVAILABLE = True
except Exception:  # pragma: no cover
    SkillContext = None  # type: ignore
    _DEFAULT_SKILL_REGISTRY = None  # type: ignore
    EvidenceExtractInput = None  # type: ignore
    GapInput = None  # type: ignore
    QualityGateInput = None  # type: ignore
    QueryRewriteInput = None  # type: ignore
    SummarizeInput = None  # type: ignore
    _SKILL_REGISTRY_AVAILABLE = False


class BaseResearchAgent(ABC):
    """
    深度研究 Agent 基类。

    研究流程（research() 方法）
    ---------------------------
    1. 生成报告段落结构 (_generate_report_structure)
    2. 逐段落执行搜索+总结+反思 (_process_paragraphs)
    3. 生成最终报告文本 (_generate_final_report)
    4. 可选保存报告文件 (_save_report)

    Wave 3 升级
    -----------
    通过 _build_graph() 返回 StateGraph，research() 默认走图执行路径。
    设置 USE_GRAPH_ENGINE = False 可回退到旧的硬编码调用链。
    """

    # Wave 3：图执行开关。子类可设为 False 回退到旧路径。
    USE_GRAPH_ENGINE: bool = True

    # Wave 5：证据沉淀开关。默认关闭，避免 LLM 调用开销影响主流程。
    # 设为 True 后，每个段落研究完成时自动提取并沉淀证据到 evidence 表。
    ENABLE_EVIDENCE_SINK: bool = False
    REFLECTION_CONSERVATIVE_NOTE: str = (
        "【审慎说明】当前证据存在冲突、时效或覆盖缺口，相关结论已按保守口径表达。"
    )

    def __init__(self, config: Any = None) -> None:
        self.config = config
        self.llm_client: LLMClient = self._initialize_llm()
        self.search_agency: Any = self._initialize_search_agency()
        self._initialize_nodes()
        self.state: Any = self._create_initial_state()
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        # Wave 5：可选 evidence_store（ENABLE_EVIDENCE_SINK=True 时使用）
        self._evidence_store: Any = None
        self._skill_registry: Any = _DEFAULT_SKILL_REGISTRY if _SKILL_REGISTRY_AVAILABLE else None
        if self.ENABLE_EVIDENCE_SINK and _EVIDENCE_STORE_AVAILABLE and _get_evidence_store:
            try:
                self._evidence_store = _get_evidence_store()
            except Exception as exc:  # pragma: no cover
                logger.debug(f"[EvidenceStore] 初始化失败，后续按需获取: {exc}")

    # ------------------------------------------------------------------
    # 抽象方法 — 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def _initialize_llm(self) -> LLMClient:
        """初始化并返回 LLM 客户端。"""

    @abstractmethod
    def _initialize_search_agency(self) -> Any:
        """初始化并返回搜索工具集（Bocha / Tavily / MediaCrawlerDB 等）。"""

    @abstractmethod
    def _initialize_nodes(self) -> None:
        """
        初始化全部处理节点并赋值到 self。
        约定节点属性：
          self.first_search_node, self.reflection_node,
          self.first_summary_node, self.reflection_summary_node,
          self.report_formatting_node
        （ReportStructureNode 在 _generate_report_structure 内部按需创建）
        """

    @abstractmethod
    def _create_initial_state(self) -> Any:
        """创建并返回各引擎自有的 State 实例。"""

    @abstractmethod
    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> Any:
        """
        调用引擎特有的搜索后端，返回原始响应对象。
        原始对象由 _normalize_search_response() 转为标准 dict 列表。
        """

    @abstractmethod
    def _normalize_search_response(self, response: Any) -> List[dict]:
        """
        将 execute_search_tool 返回的原始响应标准化为统一结构的 dict 列表。

        每条 dict 至少包含：
          title, url, content, score, raw_content, published_date
        """

    @abstractmethod
    def _get_content_max_length(self) -> int:
        """返回传递给 format_search_results_for_prompt 的内容截断长度。"""

    # ------------------------------------------------------------------
    # 钩子方法 — 有默认实现，子类可覆写
    # ------------------------------------------------------------------

    def _prepare_search_call(
        self, search_tool: str, search_output: dict
    ) -> tuple:
        """
        准备搜索调用，返回 (final_tool_name, kwargs) 元组。
        允许子类在返回 kwargs 的同时修改工具名（如日期无效时回退到默认工具）。
        默认实现返回 (search_tool, {})，子类可覆写。
        """
        return search_tool, {}

    def _record_search_results(
        self,
        paragraph: Any,
        query: str,
        results: List[dict],
        search_tool: str = "",
    ) -> None:
        """
        将标准化的搜索结果写入段落研究状态。
        默认使用两参数签名；MediaEngine 覆写以传递 search_tool 和 paragraph_title。
        """
        paragraph.research.add_search_results(query, results)

    # ------------------------------------------------------------------
    # 进度事件辅助（内部使用）
    # ------------------------------------------------------------------

    def _emit(
        self,
        task_id: Optional[str],
        event_type: str,
        node_name: Optional[str] = None,
        paragraph: Optional[int] = None,
        iteration: Optional[int] = None,
        detail: Optional[dict] = None,
    ) -> None:
        """向 task_store 写入节点级进度事件；task_id 为 None 时静默跳过。"""
        if not task_id or not _TASK_STORE_AVAILABLE:
            return
        try:
            store = _get_task_store()
            store.add_event(
                task_id=task_id,
                event_type=event_type,
                node_name=node_name,
                paragraph=paragraph,
                iteration=iteration,
                detail=detail,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[TaskStore] 写入进度事件失败，忽略继续: {exc}")

    # ------------------------------------------------------------------
    # Wave 3：StateGraph 图定义与图节点函数
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        """
        构建研究流程的 StateGraph。

        图结构：
            generate_structure → process_paragraph → [has_more?] → more → process_paragraph
                                                                  → done → format_report

        子类可以 override 此方法定制图结构（如增加额外节点）。
        """
        g = StateGraph(name=f"{self.__class__.__name__}_research")
        g.add_node("generate_structure", self._graph_node_generate_structure)
        g.add_node("process_paragraph", self._graph_node_process_paragraph)
        g.add_node("format_report", self._graph_node_format_report)

        g.set_entry("generate_structure")
        g.add_edge("generate_structure", "process_paragraph")
        g.add_conditional_edge(
            "process_paragraph",
            condition=self._graph_cond_has_more_paragraphs,
            targets={"more": "process_paragraph", "done": "format_report"},
        )
        g.set_finish("format_report")
        return g

    def _graph_node_generate_structure(self, gs: DictGraphState) -> DictGraphState:
        """图节点：生成报告结构（对应旧 _generate_report_structure）。"""
        self._generate_report_structure(gs.get("query", ""))
        gs.current_paragraph_index = 0
        gs.total_paragraphs = len(self.state.paragraphs)
        return gs

    def _graph_node_process_paragraph(self, gs: DictGraphState) -> DictGraphState:
        """图节点：处理一个段落（搜索 + 总结 + 反思）。"""
        idx: int = gs.current_paragraph_index or 0
        task_id: Optional[str] = gs.get("task_id")
        skip_indices: set = gs.get("skip_indices") or set()
        total = len(self.state.paragraphs)

        if idx in skip_indices:
            logger.info(
                f"[断点恢复] 跳过已完成段落 {idx + 1}/{total}: "
                f"{self.state.paragraphs[idx].title}"
            )
            self.state.paragraphs[idx].research.mark_completed()
        else:
            logger.info(f"\n[步骤 2.{idx + 1}] 处理段落: {self.state.paragraphs[idx].title}")
            logger.info("-" * 50)
            self._emit(task_id, "paragraph_start", paragraph=idx,
                       detail={"title": self.state.paragraphs[idx].title})
            try:
                self._initial_search_and_summary(idx, task_id=task_id)
                self._reflection_loop(idx, task_id=task_id)
                self.state.paragraphs[idx].research.mark_completed()
                progress = (idx + 1) / total * 100
                logger.info(f"段落处理完成 ({progress:.1f}%)")
                self._emit(task_id, "paragraph_done", paragraph=idx,
                           detail=self._build_paragraph_done_detail(
                               self.state.paragraphs[idx], progress
                           ))

                # Wave 5：可选证据沉淀
                if self.ENABLE_EVIDENCE_SINK and task_id:
                    self._sink_paragraph_evidence(idx, task_id)

            except Exception as exc:
                self._emit(task_id, "error", paragraph=idx,
                           detail={"error": str(exc), "step": "process_paragraph"})
                raise

        gs.current_paragraph_index = idx + 1
        return gs

    def _graph_node_format_report(self, gs: DictGraphState) -> DictGraphState:
        """图节点：生成最终报告（对应旧 _generate_final_report）。"""
        task_id: Optional[str] = gs.get("task_id")
        final_report = self._generate_final_report(task_id=task_id)
        gs.final_report = final_report
        return gs

    @staticmethod
    def _graph_cond_has_more_paragraphs(gs: DictGraphState) -> str:
        """图条件：判断是否还有未处理的段落。"""
        # paragraphs 由 self.state 维护；图通过 current_paragraph_index 追踪进度
        # 注意：此条件函数无法直接访问 self，通过 DictGraphState 中存储的总段落数判断
        total = gs.get("total_paragraphs") or 0
        current = gs.get("current_paragraph_index") or 0
        return "more" if current < total else "done"

    # ------------------------------------------------------------------
    # 主研究流程
    # ------------------------------------------------------------------

    def research(
        self,
        query: str,
        save_report: bool = True,
        task_id: Optional[str] = None,
        skip_paragraph_indices: Optional[set] = None,
    ) -> str:
        """
        执行深度研究，返回最终报告内容（Markdown 字符串）。

        Args:
            query:                  研究主题
            save_report:            是否将报告保存到文件
            task_id:                可选任务 ID，用于写入 task_events 进度事件
            skip_paragraph_indices: 断点恢复时跳过的段落索引集合
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"开始深度研究: {query}")
        if task_id:
            logger.info(f"任务 ID: {task_id}")
        logger.info(f"{'=' * 60}")

        self._emit(task_id, "research_start", detail={"query": query})

        if self.USE_GRAPH_ENGINE:
            return self._research_via_graph(
                query=query,
                save_report=save_report,
                task_id=task_id,
                skip_paragraph_indices=skip_paragraph_indices or set(),
            )
        return self._research_legacy(
            query=query,
            save_report=save_report,
            task_id=task_id,
            skip_paragraph_indices=skip_paragraph_indices or set(),
        )

    def _research_via_graph(
        self,
        query: str,
        save_report: bool,
        task_id: Optional[str],
        skip_paragraph_indices: set,
    ) -> str:
        """
        Wave 3 图执行路径：通过 GraphRunner 执行 StateGraph。

        注意：GraphRunner 的 task_store 传 None（禁用图级别粗粒度事件），
        由现有的 _emit() 调用负责所有 task_events 写入，避免重复。
        """
        try:
            # 构建初始图状态（控制流数据）
            initial_gs = DictGraphState(
                query=query,
                task_id=task_id,
                skip_indices=skip_paragraph_indices,
                current_paragraph_index=0,
                total_paragraphs=0,
                final_report="",
            )

            g = self._build_graph()
            runner = GraphRunner(g, task_store=None)
            final_gs = runner.run(initial_gs, task_id=None)
            final_report: str = final_gs.final_report or ""

            if save_report:
                self._save_report(final_report)

            total = len(self.state.paragraphs)
            self._emit(task_id, "research_done",
                       detail={"paragraphs": total})
            logger.info("深度研究完成！")
            return final_report

        except Exception as exc:
            self._emit(task_id, "error",
                       detail={"error": str(exc), "step": "research_via_graph"})
            logger.exception(f"研究过程中发生错误（图执行）: {exc}")
            raise

    def _research_legacy(
        self,
        query: str,
        save_report: bool,
        task_id: Optional[str],
        skip_paragraph_indices: set,
    ) -> str:
        """
        旧的硬编码执行路径（向后兼容保留）。
        设置 USE_GRAPH_ENGINE = False 可使用此路径。
        """
        try:
            self._generate_report_structure(query)
            self._process_paragraphs(
                task_id=task_id,
                skip_indices=skip_paragraph_indices,
            )
            final_report = self._generate_final_report(task_id=task_id)

            if save_report:
                self._save_report(final_report)

            self._emit(task_id, "research_done",
                       detail={"paragraphs": len(self.state.paragraphs)})
            logger.info("深度研究完成！")
            return final_report

        except Exception as exc:
            self._emit(task_id, "error",
                       detail={"error": str(exc), "step": "research"})
            logger.exception(f"研究过程中发生错误: {exc}")
            raise

    def research_with_resume(
        self,
        query: str,
        task_id: str,
        save_report: bool = True,
    ) -> str:
        """
        带断点恢复的深度研究。
        自动读取 task_id 对应的已完成段落并跳过。
        """
        skip_indices: set = set()
        if _TASK_STORE_AVAILABLE:
            try:
                store = _get_task_store()
                skip_indices = store.get_completed_paragraphs(task_id)
                if skip_indices:
                    logger.info(
                        f"[断点恢复] 已完成段落: {sorted(skip_indices)}，"
                        f"将从下一个未完成段落继续"
                    )
            except Exception as exc:  # pragma: no cover
                logger.warning(f"[断点恢复] 读取历史进度失败，从头开始: {exc}")

        if self.USE_GRAPH_ENGINE:
            return self._resume_via_graph(
                query=query,
                save_report=save_report,
                task_id=task_id,
                skip_paragraph_indices=skip_indices,
            )

        return self.research(
            query=query,
            save_report=save_report,
            task_id=task_id,
            skip_paragraph_indices=skip_indices,
        )

    def _resume_via_graph(
        self,
        query: str,
        save_report: bool,
        task_id: str,
        skip_paragraph_indices: set,
    ) -> str:
        """
        Wave 3 断点恢复路径：生成结构后从 process_paragraph 节点 resume。

        当前持久化层只保存段落完成事件，不保存完整 Agent State；
        因此这里通过 skip_indices 重放跳过已完成段落，并使用 GraphRunner.resume()
        进入图执行路径。
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"断点恢复深度研究: {query}")
        logger.info(f"任务 ID: {task_id}")
        logger.info(f"{'=' * 60}")
        self._emit(task_id, "research_resume", detail={"query": query})

        try:
            self._generate_report_structure(query)
            total = len(self.state.paragraphs)
            initial_gs = DictGraphState(
                query=query,
                task_id=task_id,
                skip_indices=skip_paragraph_indices,
                current_paragraph_index=0,
                total_paragraphs=total,
                final_report="",
            )
            runner = GraphRunner(self._build_graph(), task_store=None)
            final_gs = runner.resume(initial_gs, from_node="process_paragraph", task_id=None)
            final_report: str = final_gs.final_report or ""

            if save_report:
                self._save_report(final_report)

            self._emit(task_id, "research_done", detail={"paragraphs": total, "resume": True})
            logger.info("断点恢复研究完成！")
            return final_report
        except Exception as exc:
            self._emit(task_id, "error", detail={"error": str(exc), "step": "resume_via_graph"})
            logger.exception(f"断点恢复过程中发生错误（图执行）: {exc}")
            raise

    # ------------------------------------------------------------------
    # 内部步骤
    # ------------------------------------------------------------------

    def _generate_report_structure(self, query: str) -> None:
        """
        步骤 1：调用 ReportStructureNode 生成报告段落结构。

        子类须在 _initialize_nodes() 中设置：
            self._report_structure_node_class = ReportStructureNode
        """
        logger.info("\n[步骤 1] 生成报告结构...")

        if not hasattr(self, "_report_structure_node_class") or \
                self._report_structure_node_class is None:
            raise RuntimeError(
                f"{self.__class__.__name__}._initialize_nodes() 必须设置 "
                "self._report_structure_node_class = ReportStructureNode"
            )

        RSNode = self._report_structure_node_class  # type: ignore
        report_structure_node = RSNode(self.llm_client, query)
        self.state = report_structure_node.mutate_state(state=self.state)

        msg = f"报告结构已生成，共 {len(self.state.paragraphs)} 个段落:"
        for i, p in enumerate(self.state.paragraphs, 1):
            msg += f"\n  {i}. {p.title}"
        logger.info(msg)

    def _process_paragraphs(
        self,
        task_id: Optional[str] = None,
        skip_indices: Optional[set] = None,
    ) -> None:
        """步骤 2：逐段落执行搜索+总结+反思循环，支持断点跳过。"""
        total = len(self.state.paragraphs)
        skip_set = skip_indices or set()

        for i in range(total):
            if i in skip_set:
                logger.info(
                    f"[断点恢复] 跳过已完成段落 {i + 1}/{total}: "
                    f"{self.state.paragraphs[i].title}"
                )
                self.state.paragraphs[i].research.mark_completed()
                continue

            logger.info(f"\n[步骤 2.{i + 1}] 处理段落: {self.state.paragraphs[i].title}")
            logger.info("-" * 50)
            self._emit(task_id, "paragraph_start", paragraph=i,
                       detail={"title": self.state.paragraphs[i].title})

            try:
                self._initial_search_and_summary(i, task_id=task_id)
                self._reflection_loop(i, task_id=task_id)
                self.state.paragraphs[i].research.mark_completed()

                progress = (i + 1) / total * 100
                logger.info(f"段落处理完成 ({progress:.1f}%)")
                self._emit(task_id, "paragraph_done", paragraph=i,
                           detail=self._build_paragraph_done_detail(
                               self.state.paragraphs[i], progress
                           ))

                # Wave 5：可选证据沉淀
                if self.ENABLE_EVIDENCE_SINK and task_id:
                    self._sink_paragraph_evidence(i, task_id)

            except Exception as exc:
                self._emit(task_id, "error", paragraph=i,
                           detail={"error": str(exc), "step": "process_paragraph"})
                raise

    def _initial_search_and_summary(
        self, paragraph_index: int, task_id: Optional[str] = None
    ) -> None:
        """初始搜索和总结（模板方法，子类通过钩子自定义细节）。"""
        paragraph = self.state.paragraphs[paragraph_index]
        search_input = {"title": paragraph.title, "content": paragraph.content}

        # --- 第一步：生成搜索查询 ---
        logger.info("  - 生成搜索查询...")
        self._emit(task_id, "node_start", node_name="FirstSearchNode",
                   paragraph=paragraph_index)
        search_output = self.first_search_node.run(search_input)
        self._emit(task_id, "node_done", node_name="FirstSearchNode",
                   paragraph=paragraph_index)
        search_output = self._rewrite_search_plan(
            paragraph=paragraph,
            original_search_output=search_output,
            task_id=task_id,
        )

        search_query = search_output["search_query"]
        search_tool = search_output.get("search_tool", self._get_default_search_tool())
        logger.info(f"  - 搜索查询: {search_query}  工具: {search_tool}")

        # --- 第二步：执行搜索 ---
        logger.info("  - 执行搜索...")
        search_tool, search_kwargs = self._prepare_search_call(search_tool, search_output)
        raw_response = self.execute_search_tool(search_tool, search_query, **search_kwargs)
        search_results = self._normalize_search_response(raw_response)

        self._log_search_results(search_results)
        self._record_search_results(paragraph, search_query, search_results, search_tool)

        # --- 第三步：生成初始总结 ---
        logger.info("  - 生成初始总结...")
        skill_summary = self._summarize_with_skill(
            paragraph=paragraph,
            search_results=search_results,
            task_id=task_id,
            mode="first_summary",
        )
        if skill_summary and self._quality_gate_passed(skill_summary, task_id=task_id):
            paragraph.research.latest_summary = skill_summary
            logger.info("  - 初始总结完成（skill）")
            return

        summary_input = {
            "title": paragraph.title,
            "content": paragraph.content,
            "search_query": search_query,
            "search_results": format_search_results_for_prompt(
                search_results, self._get_content_max_length()
            ),
        }
        self._emit(task_id, "node_start", node_name="FirstSummaryNode",
                   paragraph=paragraph_index)
        self.state = self.first_summary_node.mutate_state(
            summary_input, self.state, paragraph_index
        )
        self._emit(task_id, "node_done", node_name="FirstSummaryNode",
                   paragraph=paragraph_index)
        logger.info("  - 初始总结完成")

    def _reflection_loop(
        self, paragraph_index: int, task_id: Optional[str] = None
    ) -> None:
        """反思循环（模板方法）。"""
        paragraph = self.state.paragraphs[paragraph_index]

        for reflection_i in range(self.config.MAX_REFLECTIONS):
            logger.info(f"  - 反思 {reflection_i + 1}/{self.config.MAX_REFLECTIONS}...")

            reflection_input = {
                "title": paragraph.title,
                "content": paragraph.content,
                "paragraph_latest_state": paragraph.research.latest_summary,
            }

            self._emit(task_id, "node_start", node_name="ReflectionNode",
                       paragraph=paragraph_index, iteration=reflection_i)
            reflection_output = self.reflection_node.run(reflection_input)
            self._emit(task_id, "node_done", node_name="ReflectionNode",
                       paragraph=paragraph_index, iteration=reflection_i)
            reflection_output = self._rewrite_search_plan(
                paragraph=paragraph,
                original_search_output=reflection_output,
                task_id=task_id,
            )

            search_query = reflection_output["search_query"]
            search_tool = reflection_output.get(
                "search_tool", self._get_default_search_tool()
            )
            logger.info(f"    反思查询: {search_query}  工具: {search_tool}")

            search_tool, search_kwargs = self._prepare_search_call(search_tool, reflection_output)
            raw_response = self.execute_search_tool(search_tool, search_query, **search_kwargs)
            search_results = self._normalize_search_response(raw_response)

            self._log_search_results(search_results, is_reflection=True)
            self._record_search_results(paragraph, search_query, search_results, search_tool)

            reflection_summary_input = {
                "title": paragraph.title,
                "content": paragraph.content,
                "search_query": search_query,
                "search_results": format_search_results_for_prompt(
                    search_results, self._get_content_max_length()
                ),
                "paragraph_latest_state": paragraph.research.latest_summary,
            }

            skill_summary = self._summarize_with_skill(
                paragraph=paragraph,
                search_results=search_results,
                task_id=task_id,
                mode="reflection_summary",
            )
            if skill_summary and self._quality_gate_passed(skill_summary, task_id=task_id):
                paragraph.research.latest_summary = skill_summary
                if hasattr(paragraph.research, "increment_reflection"):
                    paragraph.research.increment_reflection()
                signal = self._apply_reflection_signal(
                    paragraph=paragraph,
                    paragraph_index=paragraph_index,
                    task_id=task_id,
                )
                logger.info(f"    反思 {reflection_i + 1} 完成（skill）")
                if not signal.get("continue_search", True):
                    logger.info("    反思收敛：缺口较小，后续以保守表达结束本段反思循环")
                    break
                continue

            self._emit(task_id, "node_start", node_name="ReflectionSummaryNode",
                       paragraph=paragraph_index, iteration=reflection_i)
            self.state = self.reflection_summary_node.mutate_state(
                reflection_summary_input, self.state, paragraph_index
            )
            self._emit(task_id, "node_done", node_name="ReflectionSummaryNode",
                       paragraph=paragraph_index, iteration=reflection_i)

            logger.info(f"    反思 {reflection_i + 1} 完成")
            signal = self._apply_reflection_signal(
                paragraph=paragraph,
                paragraph_index=paragraph_index,
                task_id=task_id,
            )
            if not signal.get("continue_search", True):
                logger.info("    反思收敛：缺口较小，后续以保守表达结束本段反思循环")
                break

    def _build_paragraph_done_detail(self, paragraph: Any, progress: float) -> dict:
        detail = {
            "progress_pct": round(progress, 1),
            "engine": self._resolve_engine_name(),
        }
        signal = getattr(paragraph.research, "last_reflection_signal", None)
        if not isinstance(signal, dict):
            return detail

        for key in (
            "gap_types",
            "high_priority_gap_count",
            "overall_coverage",
            "conflict_notes",
            "evidence_conflict_count",
            "evidence_avg_confidence",
            "evidence_total_count",
            "conservative_expression_applied",
            "continue_search",
        ):
            value = signal.get(key)
            if value in (None, "", []):
                continue
            detail[key] = value
        return detail

    def _apply_reflection_signal(
        self,
        paragraph: Any,
        paragraph_index: int,
        task_id: Optional[str],
    ) -> Dict[str, Any]:
        signal: Dict[str, Any] = {
            "gap_types": [],
            "high_priority_gap_count": 0,
            "overall_coverage": "",
            "conflict_notes": [],
            "evidence_conflict_count": 0,
            "evidence_avg_confidence": None,
            "evidence_total_count": 0,
            "conservative_expression_applied": False,
            "continue_search": True,
        }

        gap_output = self._analyze_gap_with_skill(paragraph, task_id)
        if gap_output is not None:
            gap_items = list(getattr(gap_output, "gaps", []) or [])
            signal["gap_types"] = list(dict.fromkeys(
                str(getattr(gap, "gap_type", "coverage") or "coverage")
                for gap in gap_items
            ))
            signal["high_priority_gap_count"] = sum(
                1
                for gap in gap_items
                if str(getattr(gap, "priority", "medium")).lower() in {"high", "medium"}
            )
            signal["overall_coverage"] = str(
                getattr(gap_output, "overall_coverage", "") or ""
            ).strip()
            signal["conflict_notes"] = [
                str(note)
                for note in (getattr(gap_output, "conflict_notes", []) or [])
                if str(note).strip()
            ][:3]

        signal.update(self._collect_evidence_signal(task_id))

        gap_types = set(signal.get("gap_types") or [])
        evidence_conflicts = int(signal.get("evidence_conflict_count") or 0)
        avg_confidence = signal.get("evidence_avg_confidence")
        evidence_total_count = int(signal.get("evidence_total_count") or 0)
        has_recency_risk = "recency" in gap_types
        has_conflict_risk = "conflict" in gap_types or evidence_conflicts > 0
        low_confidence_risk = (
            evidence_total_count > 0
            and isinstance(avg_confidence, (int, float))
            and float(avg_confidence) < 0.55
        )

        if (has_recency_risk or has_conflict_risk or low_confidence_risk):
            summary = str(getattr(paragraph.research, "latest_summary", "") or "")
            if summary and self.REFLECTION_CONSERVATIVE_NOTE not in summary:
                paragraph.research.latest_summary = (
                    f"{summary}\n\n{self.REFLECTION_CONSERVATIVE_NOTE}"
                )
            signal["conservative_expression_applied"] = bool(
                getattr(paragraph.research, "latest_summary", "")
            )

        overall_coverage = str(signal.get("overall_coverage", "") or "")
        if signal.get("high_priority_gap_count", 0) > 0:
            signal["continue_search"] = True
        elif "coverage" in gap_types and "较好" not in overall_coverage and "完整" not in overall_coverage:
            signal["continue_search"] = True
        elif has_conflict_risk:
            signal["continue_search"] = True
        elif overall_coverage:
            signal["continue_search"] = False

        setattr(paragraph.research, "last_reflection_signal", signal)
        self._emit(
            task_id,
            "gap_analysis",
            paragraph=paragraph_index,
            detail=signal,
        )
        return signal

    def _analyze_gap_with_skill(self, paragraph: Any, task_id: Optional[str]) -> Any:
        if not _SKILL_REGISTRY_AVAILABLE or GapInput is None:
            return None

        summaries: List[str] = []
        latest_summary = str(getattr(paragraph.research, "latest_summary", "") or "").strip()
        if latest_summary:
            summaries.append(latest_summary)
        summaries.extend(self._extract_search_history_fragments(paragraph))
        summaries = list(dict.fromkeys([summary for summary in summaries if summary]))[:6]
        if not summaries:
            return None

        research_question = " ".join(
            str(part).strip()
            for part in [getattr(paragraph, "title", ""), getattr(paragraph, "content", "")]
            if str(part).strip()
        ) or "研究问题"

        return self._execute_skill(
            "gap_finder",
            GapInput(
                summaries=summaries,
                research_question=research_question,
                engine_names=[self._resolve_engine_name() for _ in summaries],
            ),
            task_id=task_id,
        )

    def _extract_search_history_fragments(self, paragraph: Any) -> List[str]:
        fragments: List[str] = []
        search_history = list(getattr(paragraph.research, "search_history", []) or [])
        for item in reversed(search_history):
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                content = str(item.get("content", "")).strip()
            else:
                title = str(getattr(item, "title", "")).strip()
                content = str(getattr(item, "content", "")).strip()
            merged = " ".join(part for part in [title, content[:220]] if part)
            if not merged:
                continue
            fragments.append(merged)
            if len(fragments) >= 3:
                break
        return fragments

    def _collect_evidence_signal(self, task_id: Optional[str]) -> Dict[str, Any]:
        if not task_id or not _EVIDENCE_STORE_AVAILABLE or not _get_evidence_store:
            return {}

        store = self._evidence_store
        if store is None:
            try:
                store = _get_evidence_store()
            except Exception as exc:  # pragma: no cover
                logger.debug(f"[EvidenceStore] 读取聚合信息失败，跳过反思证据信号: {exc}")
                return {}

        try:
            aggregate = store.aggregate(task_id)
            return {
                "evidence_conflict_count": len(getattr(aggregate, "conflicts", []) or []),
                "evidence_avg_confidence": round(float(getattr(aggregate, "avg_confidence", 0.0)), 3),
                "evidence_total_count": int(getattr(aggregate, "total_count", 0)),
            }
        except Exception as exc:  # pragma: no cover
            logger.debug(f"[EvidenceStore] 聚合读取失败，跳过反思证据信号: {exc}")
            return {}

    def _generate_final_report(self, task_id: Optional[str] = None) -> str:
        """步骤 3：汇总所有段落总结，生成最终报告文本。"""
        logger.info("\n[步骤 3] 生成最终报告...")

        report_data = [
            {"title": p.title, "paragraph_latest_state": p.research.latest_summary}
            for p in self.state.paragraphs
        ]

        self._emit(task_id, "node_start", node_name="ReportFormattingNode")
        try:
            final_report = self.report_formatting_node.run(report_data)
        except Exception as exc:
            logger.exception(f"LLM格式化失败，使用备用方法: {exc}")
            final_report = self.report_formatting_node.format_report_manually(
                report_data, self.state.report_title
            )
        self._emit(task_id, "node_done", node_name="ReportFormattingNode")

        self.state.final_report = final_report
        self.state.mark_completed()
        logger.info("最终报告生成完成")
        return final_report

    def _save_report(self, report_content: str) -> None:
        """步骤 4：将报告保存到文件（可选）。"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(
            c for c in self.state.query if c.isalnum() or c in (" ", "-", "_")
        ).rstrip().replace(" ", "_")[:30]

        filename = f"deep_search_report_{query_safe}_{timestamp}.md"
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info(f"报告已保存到: {filepath}")

        if getattr(self.config, "SAVE_INTERMEDIATE_STATES", False):
            state_path = os.path.join(
                self.config.OUTPUT_DIR, f"state_{query_safe}_{timestamp}.json"
            )
            self.state.save_to_file(state_path)
            logger.info(f"状态已保存到: {state_path}")

    # ------------------------------------------------------------------
    # Wave 5：证据沉淀工具方法
    # ------------------------------------------------------------------

    def _sink_paragraph_evidence(
        self,
        paragraph_index: int,
        task_id: str,
    ) -> None:
        """
        将段落总结中的核心内容以证据形式沉淀到 evidence 表。

        触发条件：ENABLE_EVIDENCE_SINK=True 且 task_id 非空。
        失败时静默记录 warning，不影响主流程。
        """
        if not _EVIDENCE_STORE_AVAILABLE or not _get_evidence_store or not _Evidence:
            return
        try:
            paragraph = self.state.paragraphs[paragraph_index]
            summary = getattr(paragraph.research, "latest_summary", "") or ""
            if not summary:
                return

            evidences = self._extract_evidences_from_summary(
                summary=summary,
                paragraph_index=paragraph_index,
                task_id=task_id,
            )
            if evidences:
                store = _get_evidence_store()
                n = store.add_batch(evidences)
                logger.debug(
                    f"[EvidenceSink] 段落 {paragraph_index} 沉淀 {n} 条证据"
                )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[EvidenceSink] 段落 {paragraph_index} 证据沉淀失败，忽略: {exc}")

    def _extract_evidences_from_summary(
        self,
        summary: str,
        paragraph_index: int,
        task_id: str,
    ) -> List:
        """
        从段落总结中提取 Evidence 列表（轻量实现：按句分割，不额外调用 LLM）。

        初版使用启发式规则；如需 LLM 提取，子类可 override 调用 EvidenceExtractSkill。
        """
        if not _Evidence:
            return []

        engine = self._resolve_engine_name()

        skill_evidences = self._extract_evidences_with_skill(
            summary=summary,
            paragraph_index=paragraph_index,
            task_id=task_id,
            engine=engine,
        )
        if skill_evidences:
            return skill_evidences

        evidences = []

        # 按句切分（简单按 "。" / "." / "\n" 分割，过滤短句）
        sentences = []
        for sep in ("。", "\n", ". "):
            parts = summary.split(sep)
            if len(parts) > len(sentences):
                sentences = parts

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 15:
                continue
            evidences.append(_Evidence(
                task_id=task_id,
                engine=engine,
                paragraph_index=paragraph_index,
                claim=sent[:200],
                supporting_text=summary[:500],
                confidence=0.6,
            ))
            if len(evidences) >= 3:
                break

        return evidences

    # ------------------------------------------------------------------
    # Wave 2.5：Skill 深接线辅助
    # ------------------------------------------------------------------

    def _build_skill_context(self, task_id: Optional[str] = None):
        if not _SKILL_REGISTRY_AVAILABLE or SkillContext is None:
            return None

        evidence_store = self._evidence_store
        if evidence_store is None and _EVIDENCE_STORE_AVAILABLE and _get_evidence_store:
            try:
                evidence_store = _get_evidence_store()
            except Exception as exc:  # pragma: no cover
                logger.debug(f"[SkillContext] 获取 evidence_store 失败，继续降级: {exc}")
                evidence_store = None

        return SkillContext(
            task_id=task_id,
            llm_client=self.llm_client,
            config=self.config,
            evidence_store=evidence_store,
        )

    def _execute_skill(self, name: str, input_model: Any, task_id: Optional[str] = None) -> Any:
        if not _SKILL_REGISTRY_AVAILABLE or self._skill_registry is None:
            return None
        if not self._skill_registry.has(name):
            return None

        ctx = self._build_skill_context(task_id=task_id)
        if ctx is None:
            return None

        try:
            return self._skill_registry.execute(name, input_model, ctx)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[Skill:{name}] 执行失败，回退到原节点逻辑: {exc}")
            return None

    def _rewrite_search_plan(
        self,
        paragraph: Any,
        original_search_output: dict,
        task_id: Optional[str] = None,
    ) -> dict:
        if not _SKILL_REGISTRY_AVAILABLE or QueryRewriteInput is None:
            return original_search_output

        original_query = original_search_output.get("search_query")
        if not original_query:
            return original_search_output

        search_tool = original_search_output.get("search_tool", self._get_default_search_tool())
        tools_available = list(dict.fromkeys([
            tool for tool in [search_tool, self._get_default_search_tool()] if tool
        ]))
        skill_output = self._execute_skill(
            "query_rewrite",
            QueryRewriteInput(
                original_query=original_query,
                context=f"{paragraph.title}\n{paragraph.content}",
                search_tools_available=tools_available,
            ),
            task_id=task_id,
        )
        if skill_output is None:
            return original_search_output

        merged = dict(original_search_output)
        merged["search_query"] = skill_output.rewritten_query or original_query
        if skill_output.search_tool:
            merged["search_tool"] = skill_output.search_tool

        for field in ("start_date", "end_date", "platform", "time_period", "constraints", "selection_rule", "reasoning"):
            value = getattr(skill_output, field, None)
            if value not in (None, "", []):
                merged[field] = value
        return merged

    def _summarize_with_skill(
        self,
        paragraph: Any,
        search_results: List[dict],
        task_id: Optional[str],
        mode: str,
    ) -> str:
        if not _SKILL_REGISTRY_AVAILABLE or SummarizeInput is None:
            return ""

        content_items = self._build_skill_summary_content(search_results)
        if not content_items:
            return ""

        summary_output = self._execute_skill(
            "llm_summarize",
            SummarizeInput(
                content=content_items,
                paragraph_title=paragraph.title,
                existing_summary=paragraph.research.latest_summary,
                existing_key_points=[],
                mode=mode,
            ),
            task_id=task_id,
        )
        if summary_output is None:
            return ""
        return summary_output.summary or "；".join(summary_output.key_points[:3])

    def _quality_gate_passed(self, content: str, task_id: Optional[str] = None) -> bool:
        if not content or not _SKILL_REGISTRY_AVAILABLE or QualityGateInput is None:
            return bool(content)

        result = self._execute_skill(
            "quality_gate",
            QualityGateInput(content=content, content_type="summary"),
            task_id=task_id,
        )
        if result is None:
            return True
        if not result.passed:
            issue_types = [issue.issue_type for issue in result.issues]
            logger.warning(f"[QualityGate] 摘要未通过门禁，回退到原节点逻辑: {issue_types}")
        return bool(result.passed)

    def _extract_evidences_with_skill(
        self,
        summary: str,
        paragraph_index: int,
        task_id: str,
        engine: str,
    ) -> List:
        if not _SKILL_REGISTRY_AVAILABLE or EvidenceExtractInput is None or not _Evidence:
            return []

        output = self._execute_skill(
            "evidence_extract",
            EvidenceExtractInput(content=summary),
            task_id=task_id,
        )
        if output is None or not getattr(output, "evidences", None):
            return []

        evidences = []
        for item in output.evidences[:3]:
            evidences.append(_Evidence(
                task_id=task_id,
                engine=engine,
                paragraph_index=paragraph_index,
                claim=item.claim[:200],
                supporting_text=item.supporting_text[:500],
                source_url=item.source_url,
                source_title=item.source_title,
                confidence=item.confidence,
                sentiment=item.sentiment,
                tags=list(item.tags or []),
            ))
        return evidences

    @staticmethod
    def _build_skill_summary_content(search_results: List[dict]) -> List[str]:
        items = []
        for result in search_results:
            title = str(result.get("title", "")).strip()
            content = str(result.get("content") or result.get("raw_content") or "").strip()
            published_date = str(result.get("published_date", "")).strip()
            url = str(result.get("url", "")).strip()
            parts = [part for part in [title, content[:300], published_date, url] if part]
            if not parts:
                continue
            items.append(" | ".join(parts))
            if len(items) >= 12:
                break
        return items

    def _resolve_engine_name(self) -> str:
        engine_name = self.__class__.__module__.split(".")[0].lower()
        if "insight" in engine_name:
            return "insight"
        if "media" in engine_name:
            return "media"
        if "query" in engine_name:
            return "query"
        return engine_name or "unknown"

    # ------------------------------------------------------------------
    # 公共工具方法
    # ------------------------------------------------------------------

    def get_progress_summary(self) -> Dict[str, Any]:
        return self.state.get_progress_summary()

    def load_state(self, filepath: str) -> None:
        self.state = self.state.__class__.load_from_file(filepath)
        logger.info(f"状态已从 {filepath} 加载")

    def save_state(self, filepath: str) -> None:
        self.state.save_to_file(filepath)
        logger.info(f"状态已保存到 {filepath}")

    def _validate_date_format(self, date_str: str) -> bool:
        """验证日期格式是否为 YYYY-MM-DD。"""
        if not date_str:
            return False
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _get_default_search_tool(self) -> str:
        """各引擎默认搜索工具名称；子类可覆写。"""
        return "search_topic_globally"

    # ------------------------------------------------------------------
    # 私有日志辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _log_search_results(
        search_results: List[dict], is_reflection: bool = False
    ) -> None:
        prefix = "    " if is_reflection else "  "
        if search_results:
            msg = f"{prefix}- 找到 {len(search_results)} 个搜索结果"
            for j, r in enumerate(search_results[:5], 1):
                title = str(r.get("title", ""))[:50]
                date = r.get("published_date", "")
                date_info = f" (发布于: {date})" if date else ""
                msg += f"\n{prefix}  {j}. {title}...{date_info}"
            logger.info(msg)
        else:
            logger.info(f"{prefix}- 未找到搜索结果")
