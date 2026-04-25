# -*- coding: utf-8 -*-
"""
veyrafish_core.llm_client — 统一 OpenAI 兼容 LLM 客户端

取代原先三引擎各自维护的 llms/base.py（Insight / Media / Query 版本几乎相同，
仅错误提示字符串和超时环境变量名不同）。

Stage C 预留的 invoke_structured() 和 invoke_with_tools() 方法定义于此文件末尾。
"""

import os
import sys
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Type

from loguru import logger
from openai import OpenAI

# 复用项目根目录的 retry_helper（若不可用则降级为无重试版本）
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_utils_dir = os.path.join(_project_root, "utils")
if _utils_dir not in sys.path:
    sys.path.append(_utils_dir)

try:
    from retry_helper import LLM_RETRY_CONFIG, with_retry
except ImportError:
    def with_retry(config=None):  # type: ignore
        def decorator(func):
            return func
        return decorator

    LLM_RETRY_CONFIG = None


class LLMClient:
    """
    统一的 OpenAI 兼容 Chat Completions 客户端。

    所有三个研究引擎（Insight / Media / Query）均使用此类，
    通过构造参数传入各自的 API Key、Model Name 和 Base URL。

    方法一览
    --------
    invoke()                 - 同步调用，返回字符串
    stream_invoke()          - 流式调用，generator 逐块返回
    stream_invoke_to_string()- 流式调用后拼接为完整字符串
    invoke_structured()      - Stage C: 结构化输出（Pydantic）
    invoke_with_tools()      - Stage C: Function Calling 多轮循环
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
        engine_name: str = "LLM",
    ) -> None:
        """
        Args:
            api_key:     OpenAI 兼容 API 密钥
            model_name:  模型名称（如 gpt-4o、deepseek-chat）
            base_url:    自定义 API 地址（可选，None 表示使用 OpenAI 官方地址）
            engine_name: 引擎名称，仅用于错误提示，默认 "LLM"
        """
        if not api_key:
            raise ValueError(f"{engine_name} API key is required.")
        if not model_name:
            raise ValueError(f"{engine_name} model name is required.")

        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.provider = model_name

        timeout_str = (
            os.getenv("LLM_REQUEST_TIMEOUT")
            or os.getenv(f"{engine_name.upper()}_REQUEST_TIMEOUT")
            or "1800"
        )
        try:
            self.timeout = float(timeout_str)
        except ValueError:
            self.timeout = 1800.0

        client_kwargs: Dict[str, Any] = {"api_key": api_key, "max_retries": 0}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    # ------------------------------------------------------------------
    # 核心调用方法
    # ------------------------------------------------------------------

    @with_retry(LLM_RETRY_CONFIG)
    def invoke(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """同步调用 LLM，返回完整字符串。"""
        if user_prompt is None:
            user_prompt = kwargs.pop("prompt", None)
        if user_prompt is None:
            user_prompt = system_prompt or ""
            system_prompt = kwargs.pop("system_prompt", "") if "system_prompt" in kwargs else ""
        if system_prompt is None:
            system_prompt = kwargs.pop("system_prompt", "")

        messages = self._build_messages(system_prompt, user_prompt)
        extra_params = self._filter_params(kwargs, include_stream=True)
        timeout = kwargs.pop("timeout", self.timeout)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            timeout=timeout,
            **extra_params,
        )
        if response.choices and response.choices[0].message:
            return self.validate_response(response.choices[0].message.content)
        return ""

    def stream_invoke(
        self, system_prompt: str, user_prompt: str, **kwargs
    ) -> Generator[str, None, None]:
        """流式调用 LLM，逐块 yield 字符串片段。"""
        messages = self._build_messages(system_prompt, user_prompt)
        extra_params = self._filter_params(kwargs, include_stream=False)
        extra_params["stream"] = True
        timeout = kwargs.pop("timeout", self.timeout)

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                timeout=timeout,
                **extra_params,
            )
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except Exception as e:
            logger.error(f"流式请求失败: {e}")
            raise

    @with_retry(LLM_RETRY_CONFIG)
    def stream_invoke_to_string(
        self, system_prompt: str, user_prompt: str, **kwargs
    ) -> str:
        """流式调用后安全拼接为完整字符串（避免 UTF-8 多字节截断）。"""
        byte_chunks = [
            chunk.encode("utf-8")
            for chunk in self.stream_invoke(system_prompt, user_prompt, **kwargs)
        ]
        return b"".join(byte_chunks).decode("utf-8", errors="replace") if byte_chunks else ""

    # ------------------------------------------------------------------
    # Stage C: 结构化输出（Pydantic）
    # ------------------------------------------------------------------

    def invoke_structured(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        response_model: Optional[Type] = None,
        **kwargs,
    ):
        """
        使用 OpenAI beta.chat.completions.parse 进行结构化输出。

        返回 Pydantic 模型实例；若提供商不支持则抛出 NotImplementedError，
        调用方应捕获后回退到 stream_invoke_to_string + 手动 JSON 解析路径。

        Args:
            response_model: Pydantic BaseModel 子类（定义期望输出结构）

        Returns:
            response_model 的实例
        """
        if user_prompt is None:
            user_prompt = kwargs.pop("prompt", None)
        if response_model is None:
            response_model = kwargs.pop("output_model", None)
        if system_prompt is None:
            system_prompt = kwargs.pop("system_prompt", "")
        if user_prompt is None:
            raise ValueError("invoke_structured requires user_prompt/prompt")
        if response_model is None:
            raise ValueError("invoke_structured requires response_model/output_model")

        messages = self._build_messages(system_prompt, user_prompt)
        timeout = kwargs.pop("timeout", self.timeout)

        try:
            response = self.client.beta.chat.completions.parse(  # type: ignore[attr-defined]
                model=self.model_name,
                messages=messages,
                response_format=response_model,
                timeout=timeout,
            )
            parsed = response.choices[0].message.parsed
            if parsed is None:
                raise ValueError("Structured output returned None")
            return parsed
        except AttributeError:
            raise NotImplementedError(
                "invoke_structured requires openai>=1.50 with beta.chat.completions.parse"
            )

    def invoke_structured_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type,
        fallback_fn: Optional[Callable[[str], Any]] = None,
        **kwargs,
    ):
        """
        先尝试结构化输出，失败时回退到 stream_invoke_to_string + fallback_fn 解析。

        Args:
            fallback_fn: 接收原始字符串、返回解析结果的函数（可为 None）

        Returns:
            response_model 实例，或 fallback_fn 的返回值，或原始字符串
        """
        try:
            return self.invoke_structured(system_prompt, user_prompt, response_model, **kwargs)
        except (NotImplementedError, Exception) as e:
            logger.warning(f"结构化输出失败，回退到文本解析: {e}")
            raw = self.stream_invoke_to_string(system_prompt, user_prompt, **kwargs)
            if fallback_fn:
                return fallback_fn(raw)
            return raw

    # ------------------------------------------------------------------
    # Stage C: Function Calling 多轮循环
    # ------------------------------------------------------------------

    def invoke_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[dict],
        tool_executor: Callable[[str, dict], Any],
        max_rounds: int = 5,
        **kwargs,
    ) -> str:
        """
        支持 OpenAI Function Calling 的多轮对话循环。

        模型若返回 tool_calls，自动执行对应工具并将结果回填，
        直到模型返回纯文本内容或达到 max_rounds 上限。

        Args:
            tools:         OpenAI tool schema 列表（JSON Schema 格式）
            tool_executor: 接收 (tool_name: str, arguments: dict) 返回工具结果的可调用
            max_rounds:    最大工具调用轮数（防止死循环）

        Returns:
            模型最终生成的文本字符串
        """
        messages = self._build_messages(system_prompt, user_prompt)
        timeout = kwargs.pop("timeout", self.timeout)

        for _ in range(max_rounds):
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=timeout,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return self.validate_response(msg.content)

            messages.append(msg)
            for call in msg.tool_calls:
                import json as _json
                args = _json.loads(call.function.arguments)
                result = tool_executor(call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                })

        logger.warning("invoke_with_tools: 达到最大轮数，返回最后一次文本输出")
        return self.validate_response(response.choices[0].message.content or "")

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def validate_response(response: Optional[str]) -> str:
        return "" if response is None else response.strip()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model_name,
            "api_base": self.base_url or "default",
        }

    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[dict]:
        current_time = datetime.now().strftime("%Y年%m月%d日%H时%M分")
        time_prefix = f"今天的实际时间是{current_time}"
        user_content = f"{time_prefix}\n{user_prompt}" if user_prompt else time_prefix
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _filter_params(kwargs: dict, include_stream: bool = True) -> dict:
        allowed = {"temperature", "top_p", "presence_penalty", "frequency_penalty"}
        if include_stream:
            allowed.add("stream")
        return {k: v for k, v in kwargs.items() if k in allowed and v is not None}
