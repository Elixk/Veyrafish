# -*- coding: utf-8 -*-
"""
veyrafish_core.skill — Skill 基类 + SkillContext + SkillBudget

设计灵感：
- Vibe-Skills-3.0.0 的 SKILL.md（name/description/version/tags 元信息结构）
- Semantic Kernel Plugin（函数组 + 语义描述 + 可注册可替换）
- Veyrafish output_models 的 Pydantic 类型化输出

用法::

    from veyrafish_core.skill import Skill, SkillContext, SkillBudget

    class MySkill(Skill):
        name = "my_skill"
        description = "做某事"
        version = "0.1.0"
        tags = ["category"]
        input_schema = MyInput
        output_schema = MyOutput

        def execute(self, input: MyInput, ctx: SkillContext) -> MyOutput:
            ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# SkillBudget — 执行预算约束
# ---------------------------------------------------------------------------

@dataclass
class SkillBudget:
    """Skill 执行时的资源预算约束。"""
    max_tokens: Optional[int] = None       # LLM token 上限
    max_seconds: Optional[float] = None    # 超时秒数
    max_retries: int = 3                   # 最大重试次数


# ---------------------------------------------------------------------------
# SkillContext — 运行上下文
# ---------------------------------------------------------------------------

@dataclass
class SkillContext:
    """
    Skill 执行时的上下文，提供 LLM 客户端、配置、预算等。

    各 Skill 通过 ctx 获取运行时依赖，而不是在构造函数里硬绑定。
    """
    task_id: Optional[str] = None
    llm_client: Any = None           # LLMClient 实例（弱类型避免循环导入）
    config: Any = None               # Settings 实例
    evidence_store: Any = None       # EvidenceStore（Wave 5 引入后使用）
    budget: Optional[SkillBudget] = field(default_factory=SkillBudget)
    metadata: dict = field(default_factory=dict)  # 业务自定义上下文字段

    def with_task_id(self, task_id: str) -> "SkillContext":
        """返回绑定了 task_id 的新 context（不修改原对象）。"""
        from dataclasses import replace
        return replace(self, task_id=task_id)


# ---------------------------------------------------------------------------
# Skill — 能力基类
# ---------------------------------------------------------------------------

class Skill(ABC):
    """
    Veyrafish Skill 基类。

    一个 Skill 封装一个可复用、可注册的原子能力（如网络搜索、LLM 摘要、情感分析）。

    子类必须定义：
        name          : str                  — 唯一标识符（小写下划线）
        description   : str                  — 能力语义描述
        input_schema  : Type[BaseModel]       — Pydantic 输入模型
        output_schema : Type[BaseModel]       — Pydantic 输出模型

    子类可选定义：
        version       : str  = "0.1.0"
        tags          : list = []
    """

    # 子类必须覆盖这些类属性
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    tags: List[str] = []
    input_schema: Type[BaseModel] = BaseModel
    output_schema: Type[BaseModel] = BaseModel

    # ------------------------------------------------------------------
    # 抽象方法
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, input: BaseModel, ctx: SkillContext) -> BaseModel:
        """执行 Skill 的核心逻辑。"""

    # ------------------------------------------------------------------
    # 可选扩展方法
    # ------------------------------------------------------------------

    def validate_input(self, input: BaseModel) -> bool:
        """在 execute 之前做额外校验（默认仅依赖 Pydantic schema 校验）。"""
        return True

    def on_error(
        self,
        error: Exception,
        input: BaseModel,
        ctx: SkillContext,
    ) -> Optional[BaseModel]:
        """
        错误时的降级处理。
        返回 None 表示不降级（抛出原异常）；
        返回 output_schema 实例表示使用降级结果继续。
        """
        return None

    # ------------------------------------------------------------------
    # 元信息
    # ------------------------------------------------------------------

    def to_metadata(self) -> dict:
        """导出 Skill 的元信息（用于 Registry 列表、文档生成）。"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": list(self.tags),
            "input_schema": self.input_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Skill name='{self.name}' v{self.version} tags={self.tags}>"
