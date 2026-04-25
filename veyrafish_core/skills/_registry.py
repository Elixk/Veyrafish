# -*- coding: utf-8 -*-
"""
veyrafish_core.skills._registry — SkillRegistry 实现

管理所有已注册 Skill 的索引，提供 register / get / list / execute 接口。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext


class SkillRegistry:
    """
    全局 Skill 注册表。

    用法::

        registry = SkillRegistry()
        registry.register(WebSearchSkill())

        skill = registry.get("web_search")
        result = registry.execute("web_search", input_data, ctx)

        # 按 tag 筛选
        search_skills = registry.list(tag="search")
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    # ------------------------------------------------------------------
    # 注册 / 注销
    # ------------------------------------------------------------------

    def register(self, skill: Skill) -> None:
        """注册一个 Skill。同名 Skill 已存在时抛出 ValueError。"""
        if not skill.name:
            raise ValueError(f"Skill {skill.__class__.__name__} 的 name 不能为空")
        if skill.name in self._skills:
            raise ValueError(
                f"Skill '{skill.name}' 已注册，若要替换请先调用 unregister()"
            )
        self._skills[skill.name] = skill
        logger.debug(f"[SkillRegistry] 已注册 Skill: {skill.name} v{skill.version}")

    def unregister(self, name: str) -> bool:
        """注销指定名称的 Skill，返回是否成功。"""
        if name in self._skills:
            del self._skills[name]
            logger.debug(f"[SkillRegistry] 已注销 Skill: {name}")
            return True
        return False

    def register_or_replace(self, skill: Skill) -> None:
        """注册 Skill，若同名已存在则替换（用于单元测试和热更新）。"""
        self._skills[skill.name] = skill

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[Skill]:
        """根据名称获取 Skill，不存在返回 None。"""
        return self._skills.get(name)

    def has(self, name: str) -> bool:
        """判断指定名称的 Skill 是否已注册。"""
        return name in self._skills

    def list(self, tag: Optional[str] = None) -> List[dict]:
        """
        返回所有已注册 Skill 的元信息列表。

        Args:
            tag: 如果提供，只返回包含该 tag 的 Skill
        """
        result = []
        for skill in self._skills.values():
            if tag is None or tag in skill.tags:
                result.append(skill.to_metadata())
        return result

    def names(self) -> List[str]:
        """返回所有已注册 Skill 的名称列表。"""
        return list(self._skills.keys())

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------

    def execute(
        self,
        name: str,
        input: BaseModel,
        ctx: SkillContext,
    ) -> BaseModel:
        """
        按名称执行 Skill。

        Args:
            name: Skill 名称
            input: 符合 Skill.input_schema 的 Pydantic 实例
            ctx: 运行上下文

        Returns:
            符合 Skill.output_schema 的 Pydantic 实例

        Raises:
            KeyError: Skill 未注册
            Exception: Skill 执行失败且 on_error 未降级
        """
        skill = self._skills.get(name)
        if skill is None:
            raise KeyError(f"Skill '{name}' 未注册")

        if not skill.validate_input(input):
            raise ValueError(f"Skill '{name}' 输入校验失败")

        try:
            return skill.execute(input, ctx)
        except Exception as exc:
            logger.warning(f"[SkillRegistry] Skill '{name}' 执行失败：{exc}，尝试 on_error 降级")
            fallback = skill.on_error(exc, input, ctx)
            if fallback is not None:
                return fallback
            raise

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SkillRegistry(count={len(self._skills)}, skills={self.names()})"
