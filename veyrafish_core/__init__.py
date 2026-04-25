# -*- coding: utf-8 -*-
"""
veyrafish_core — Veyrafish 引擎共享基础层

包含三个研究引擎（Insight / Media / Query）共用的：
- 统一 LLM 客户端
- 统一节点基类
- 共享 Agent 基类
- 结构化输出 Pydantic 模型
"""

from .llm_client import LLMClient
from .base_node import BaseNode, StateMutationNode
from .base_research_agent import BaseResearchAgent
from .graph import StateGraph, GraphRunner, GraphState, DictGraphState
from .skill import Skill, SkillContext, SkillBudget
from .dispatcher import ResearchDispatcher
from .evidence_store import EvidenceStore, get_evidence_store

__all__ = [
    "LLMClient",
    "BaseNode",
    "StateMutationNode",
    "BaseResearchAgent",
    "StateGraph",
    "GraphRunner",
    "GraphState",
    "DictGraphState",
    "Skill",
    "SkillContext",
    "SkillBudget",
    "ResearchDispatcher",
    "EvidenceStore",
    "get_evidence_store",
]
