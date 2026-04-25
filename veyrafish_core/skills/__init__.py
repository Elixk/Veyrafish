# -*- coding: utf-8 -*-
"""
veyrafish_core.skills — Veyrafish Skill 注册表与核心 Skill

使用方式::

    from veyrafish_core.skills import default_registry

    # 列出所有已注册 Skill
    skills = default_registry.list()

    # 执行某个 Skill
    from veyrafish_core.skills._models import QualityGateInput
    from veyrafish_core.skill import SkillContext
    result = default_registry.execute(
        "quality_gate",
        QualityGateInput(content="...", content_type="summary"),
        SkillContext(),
    )
"""

from veyrafish_core.skills._registry import SkillRegistry
from veyrafish_core.skills.web_search import WebSearchSkill
from veyrafish_core.skills.query_rewrite import QueryRewriteSkill
from veyrafish_core.skills.llm_summarize import LLMSummarizeSkill
from veyrafish_core.skills.evidence_extract import EvidenceExtractSkill
from veyrafish_core.skills.sentiment_analysis import SentimentAnalysisSkill
from veyrafish_core.skills.gap_finder import GapFinderSkill
from veyrafish_core.skills.quality_gate import QualityGateSkill

# 全局默认注册表（自动注册所有内置 Skill）
default_registry = SkillRegistry()

for _skill in [
    WebSearchSkill(),
    QueryRewriteSkill(),
    LLMSummarizeSkill(),
    EvidenceExtractSkill(),
    SentimentAnalysisSkill(),
    GapFinderSkill(),
    QualityGateSkill(),
]:
    default_registry.register(_skill)

__all__ = [
    "SkillRegistry",
    "default_registry",
    "WebSearchSkill",
    "QueryRewriteSkill",
    "LLMSummarizeSkill",
    "EvidenceExtractSkill",
    "SentimentAnalysisSkill",
    "GapFinderSkill",
    "QualityGateSkill",
]
