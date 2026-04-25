# -*- coding: utf-8 -*-
"""
veyrafish_core.base_node — 统一节点基类

取代三引擎各自维护的 nodes/base_node.py（内容完全相同）。
使用 Any 类型标注 State，避免与各引擎自有 State 类产生耦合。
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from veyrafish_core.llm_client import LLMClient


class BaseNode(ABC):
    """节点基类，定义所有处理节点的基础接口。"""

    def __init__(self, llm_client: LLMClient, node_name: str = "") -> None:
        self.llm_client = llm_client
        self.node_name = node_name or self.__class__.__name__

    @abstractmethod
    def run(self, input_data: Any, **kwargs) -> Any:
        """执行节点处理逻辑。"""

    def validate_input(self, input_data: Any) -> bool:
        return True

    def process_output(self, output: Any) -> Any:
        return output

    def log_info(self, message: str) -> None:
        logger.info(f"[{self.node_name}] {message}")

    def log_warning(self, message: str) -> None:
        logger.warning(f"[{self.node_name}] 警告: {message}")

    def log_error(self, message: str) -> None:
        logger.error(f"[{self.node_name}] 错误: {message}")


class StateMutationNode(BaseNode):
    """带状态修改功能的节点基类。state 类型为 Any 以兼容各引擎自有 State 类。"""

    @abstractmethod
    def mutate_state(self, input_data: Any, state: Any, **kwargs) -> Any:
        """修改并返回新状态。"""
