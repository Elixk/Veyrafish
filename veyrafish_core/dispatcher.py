# -*- coding: utf-8 -*-
"""
veyrafish_core.dispatcher — 三引擎并发研究调度器

将三引擎研究任务从串行调用升级为真正的并发执行（ThreadPoolExecutor），
首轮耗时从 T_insight + T_media + T_query 降到 max(T_insight, T_media, T_query)。

用法::

    from veyrafish_core.dispatcher import ResearchDispatcher

    dispatcher = ResearchDispatcher()
    results = dispatcher.dispatch(
        query="Veyrafish 舆情分析",
        agents={"insight": insight_agent, "media": media_agent, "query": query_agent},
        task_ids={"insight": "tid-i", "media": "tid-m", "query": "tid-q"},
    )
    # results = {"insight": "报告内容...", "media": "...", "query": "...", "_errors": {...}}
"""

from __future__ import annotations

import threading
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, as_completed, wait
from typing import Any, Dict, List, Optional

from loguru import logger


class ResearchDispatcher:
    """
    并发研究调度器。

    使用 ThreadPoolExecutor 同时启动多个引擎的研究任务，
    等待所有任务完成后返回结果字典。
    """

    def __init__(self, max_workers: int = 3, thread_name_prefix: str = "engine") -> None:
        self._max_workers = max_workers
        self._thread_name_prefix = thread_name_prefix

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def dispatch(
        self,
        query: str,
        agents: Dict[str, Any],
        task_ids: Optional[Dict[str, str]] = None,
        save_report: bool = True,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        并发调度多引擎研究任务。

        Args:
            query: 研究主题
            agents: 引擎名 → Agent 实例的映射，如 {"insight": insight_agent}
            task_ids: 引擎名 → task_id 的映射（可选，有则传给 research(task_id=...)）
            save_report: 是否让各引擎保存报告文件
            timeout: 总等待超时（秒），None 表示不限时

        Returns:
            dict，key 为引擎名，value 为报告字符串；
            "_errors" key 下存放执行失败的引擎及其异常信息；
            "_task_ids" key 下存放实际使用的 task_ids。
        """
        if not agents:
            return {"_errors": {}, "_task_ids": {}}

        task_ids = task_ids or {}
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        logger.info(
            f"[Dispatcher] 并发启动 {len(agents)} 个研究引擎：{list(agents.keys())}，"
            f"查询='{query[:40]}...'"
        )

        with ThreadPoolExecutor(
            max_workers=min(self._max_workers, len(agents)),
            thread_name_prefix=self._thread_name_prefix,
        ) as pool:
            future_to_engine: Dict[Any, str] = {}
            for engine_name, agent in agents.items():
                tid = task_ids.get(engine_name)
                future = pool.submit(
                    self._run_one,
                    engine_name=engine_name,
                    agent=agent,
                    query=query,
                    task_id=tid,
                    save_report=save_report,
                )
                future_to_engine[future] = engine_name

            for future in as_completed(future_to_engine, timeout=timeout):
                engine_name = future_to_engine[future]
                try:
                    results[engine_name] = future.result()
                    logger.info(f"[Dispatcher] {engine_name} 引擎完成")
                except Exception as exc:
                    logger.error(f"[Dispatcher] {engine_name} 引擎失败：{exc}")
                    errors[engine_name] = str(exc)
                    results[engine_name] = None

        results["_errors"] = errors
        results["_task_ids"] = task_ids

        if errors:
            logger.warning(f"[Dispatcher] {len(errors)} 个引擎失败：{list(errors.keys())}")
        else:
            logger.info(f"[Dispatcher] 全部 {len(agents)} 个引擎完成")

        return results

    def dispatch_with_forum(
        self,
        query: str,
        agents: Dict[str, Any],
        task_ids: Optional[Dict[str, str]] = None,
        forum_monitor: Any = None,
        save_report: bool = True,
    ) -> Dict[str, Any]:
        """
        并发调度研究任务，同时启动 ForumEngine 事件驱动监控。

        Args:
            forum_monitor: LogMonitor 实例（可选）；传入时会在调度前
                           调用 bind_tasks() 并启动事件驱动监控
        """
        task_ids = task_ids or {}

        # 启动 ForumEngine 事件驱动监控
        if forum_monitor is not None and task_ids:
            try:
                engine_task_ids = [v for k, v in task_ids.items() if k != "forum"]
                forum_monitor.bind_tasks(engine_task_ids)
                forum_monitor.start_event_driven_monitoring()
                logger.info("[Dispatcher] ForumEngine 事件驱动监控已启动")
            except Exception as exc:
                logger.warning(f"[Dispatcher] ForumEngine 监控启动失败，忽略：{exc}")

        return self.dispatch(
            query=query,
            agents=agents,
            task_ids=task_ids,
            save_report=save_report,
        )

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    @staticmethod
    def _run_one(
        engine_name: str,
        agent: Any,
        query: str,
        task_id: Optional[str],
        save_report: bool,
    ) -> str:
        """在线程中执行单个引擎的研究任务。"""
        logger.info(f"[Dispatcher:{engine_name}] 开始研究，task_id={task_id}")
        try:
            result = agent.research(
                query=query,
                save_report=save_report,
                task_id=task_id,
            )
            logger.info(f"[Dispatcher:{engine_name}] 研究完成")
            return result
        except Exception as exc:
            logger.error(f"[Dispatcher:{engine_name}] 研究失败：{exc}")
            raise
