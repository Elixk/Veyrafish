# Veyrafish Agent 核心升级执行计划

日期：2026-04-22
运行模式：`/vibe`
内部执行等级：`L`（串行分阶段）
涵盖升级项：2.1 共享基类 / 2.7 统一 LLM / 2.2 结构化输出 / 2.3 Function Calling

---

## 总体策略

**四项升级拆为 3 个阶段 + 1 个验收阶段**，每阶段独立可验证，不做大爆炸重写。

```
Stage A: veyrafish_core 基础层
         ├── 统一 LLM 客户端  (2.7)
         └── 统一节点基类      (2.1 的前置)
              ↓
Stage B: 共享 Agent 基类
         ├── BaseResearchAgent 抽取  (2.1)
         └── 三引擎改为薄壳继承
              ↓
Stage C: 结构化输出 + Function Calling
         ├── Pydantic 输出模型定义  (2.2)
         ├── LLM 客户端支持 response_format  (2.2)
         └── 工具调用框架  (2.3)
              ↓
Stage V: 验收与回归
         ├── 全量 pytest 通过
         ├── 结构化输出 vs 旧 JSON 解析对比测试
         └── 文档更新
```

---

## Stage A：`veyrafish_core` 基础层

### 目标

新建 `veyrafish_core/` 包，抽取三引擎共享的 LLM 客户端和节点基类。

### 任务清单

#### A.1 新建 `veyrafish_core/` 目录结构

```
veyrafish_core/
  __init__.py
  llm_client.py      ← 统一 LLM 客户端
  base_node.py        ← 统一节点基类（BaseNode + StateMutationNode）
  output_models.py    ← Stage C 用的 Pydantic 输出模型（本阶段先建空文件）
```

- [ ] 创建目录和 `__init__.py`
- [ ] `veyrafish_core/llm_client.py`：从 `InsightEngine/llms/base.py` 提取，参数化引擎名称和超时环境变量
- [ ] `veyrafish_core/base_node.py`：从 `InsightEngine/nodes/base_node.py` 提取
- [ ] `veyrafish_core/output_models.py`：空占位文件，Stage C 填充

#### A.2 三引擎 `llms/base.py` 改为 re-export

- [ ] `InsightEngine/llms/base.py` → `from veyrafish_core.llm_client import LLMClient`
- [ ] `MediaEngine/llms/base.py` → 同上
- [ ] `QueryEngine/llms/base.py` → 同上
- [ ] 确保各引擎 `from .llms import LLMClient` 仍能正常工作

#### A.3 三引擎 `nodes/base_node.py` 改为 re-export

- [ ] `InsightEngine/nodes/base_node.py` → `from veyrafish_core.base_node import BaseNode, StateMutationNode`
- [ ] `MediaEngine/nodes/base_node.py` → 同上
- [ ] `QueryEngine/nodes/base_node.py` → 同上

### 检验标准

- [ ] `python -c "from veyrafish_core.llm_client import LLMClient; print('OK')"` 通过
- [ ] `python -c "from veyrafish_core.base_node import BaseNode; print('OK')"` 通过
- [ ] `python -c "from InsightEngine.llms import LLMClient; print('OK')"` 通过（re-export 兼容）
- [ ] `python -m pytest tests/ -q` → **61/61 通过**
- [ ] 三引擎 `llms/base.py` 各自不超过 5 行

### 回滚方式

删除 `veyrafish_core/` 目录，恢复三个 `llms/base.py` 和 `nodes/base_node.py` 的原始内容。

---

## Stage B：共享 Agent 基类

### 目标

抽取 `veyrafish_core/base_research_agent.py`，三引擎的 `agent.py` 从 ~900 行降到 ~200 行。

### 任务清单

#### B.1 新建 `veyrafish_core/base_research_agent.py`

```python
class BaseResearchAgent(ABC):
    # ---- 共享方法（直接继承即可）----
    _validate_date_format()          # 完全相同
    _emit()                          # 完全相同
    research()                       # 参数化调度
    research_with_resume()           # 完全相同
    _generate_report_structure()     # 完全相同
    _process_paragraphs()            # 参数化跳过+事件
    _generate_final_report()         # 完全相同
    _save_report()                   # 完全相同
    get_progress_summary()           # 完全相同
    load_state() / save_state()      # 完全相同

    # ---- 抽象方法（子类必须实现）----
    @abstractmethod
    _initialize_llm() → LLMClient
    @abstractmethod
    _initialize_search_agency() → Any
    @abstractmethod
    execute_search_tool(tool_name, query, **kw) → Any
    @abstractmethod
    _normalize_search_response(response) → list[dict]
    @abstractmethod
    _get_default_search_tool() → str
    @abstractmethod
    _get_content_max_length() → int
```

- [ ] 实现基类，将三引擎中「IDENTICAL」和「SIMILAR」的方法统一
- [ ] `_initial_search_and_summary()` 抽取为模板方法：调用 `execute_search_tool` + `_normalize_search_response`
- [ ] `_reflection_loop()` 同上

#### B.2 InsightEngine/agent.py 改为薄壳

- [ ] `class InsightAgent(BaseResearchAgent)`:
  - 实现 `_initialize_llm()`（读取 `INSIGHT_ENGINE_*` 配置）
  - 实现 `_initialize_search_agency()`（创建 `MediaCrawlerDB`）
  - 实现 `execute_search_tool()`（带关键词优化 + 情感分析）
  - 实现 `_normalize_search_response()`（`DBResponse.results` → 标准 dict 列表）
  - 保留 Insight 独有方法：`_cluster_and_sample_results()`、`_perform_sentiment_analysis()`、`analyze_sentiment_only()`
- [ ] 保持 `create_agent()` 工厂函数向后兼容

#### B.3 MediaEngine/agent.py 改为薄壳

- [ ] `class MediaAgent(BaseResearchAgent)`:
  - 实现 `_initialize_llm()`
  - 实现 `_initialize_search_agency()`（创建 `BochaMultimodalSearch`）
  - 实现 `execute_search_tool()`
  - 实现 `_normalize_search_response()`（`BochaResponse.webpages` → 标准 dict 列表）
- [ ] 保留 `AnspireSearchAgent` 子类
- [ ] 保持 `create_agent()` 向后兼容

#### B.4 QueryEngine/agent.py 改为薄壳

- [ ] `class QueryAgent(BaseResearchAgent)`:
  - 实现 `_initialize_llm()`
  - 实现 `_initialize_search_agency()`（创建 `TavilyNewsAgency`）
  - 实现 `execute_search_tool()`
  - 实现 `_normalize_search_response()`（`TavilyResponse.results` → 标准 dict 列表）
- [ ] 补齐 `task_id` + `_emit` 支持（当前 Query 缺失）
- [ ] 保持 `create_agent()` 向后兼容

### 检验标准

- [ ] `python -m pytest tests/ -q` → **61/61 通过**
- [ ] `InsightEngine/agent.py` 行数 < 300（当前 ~1100）
- [ ] `MediaEngine/agent.py` 行数 < 250（当前 ~630）
- [ ] `QueryEngine/agent.py` 行数 < 200（当前 ~480）
- [ ] `python -c "from InsightEngine.agent import DeepSearchAgent; print('OK')"` 通过（向后兼容名称）
- [ ] 共享方法在基类中，子类只有 5-7 个 override

### 回滚方式

删除 `veyrafish_core/base_research_agent.py`，恢复三个 `agent.py` 的原始内容。

---

## Stage C：结构化输出 + Function Calling

### 目标

让 LLM 输出走 API 原生约束路径，减少 JSON 解析失败；工具调用走 OpenAI function calling。

### 任务清单

#### C.1 定义 Pydantic 输出模型

在 `veyrafish_core/output_models.py` 中定义：

```python
from pydantic import BaseModel
from typing import Optional, List

class SearchOutput(BaseModel):
    search_query: str
    search_tool: str
    reasoning: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platform: Optional[str] = None

class SummaryOutput(BaseModel):
    paragraph_latest_state: str

class ReflectionSummaryOutput(BaseModel):
    updated_paragraph_latest_state: str

class ReportStructureItem(BaseModel):
    title: str
    content: str
```

- [ ] 定义所有输出模型
- [ ] 为每个模型写最小验证测试（`tests/test_output_models.py`）

#### C.2 LLM 客户端支持结构化输出

在 `veyrafish_core/llm_client.py` 中新增方法：

```python
def invoke_structured(
    self,
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
    **kwargs,
) -> BaseModel:
    """使用 OpenAI 原生 JSON Schema 约束，返回 Pydantic 对象。"""
    response = self.client.beta.chat.completions.parse(
        model=self.model_name,
        messages=[...],
        response_format=response_model,
        timeout=self.timeout,
    )
    return response.choices[0].message.parsed
```

- [ ] 实现 `invoke_structured()` 方法
- [ ] 实现 `invoke_structured_with_fallback()` 方法（结构化失败时回退到旧的 JSON 解析）
- [ ] 保留 `invoke()` 和 `stream_invoke_to_string()` 不变（向后兼容）

#### C.3 节点改用结构化输出

- [ ] `FirstSearchNode.run()` → 调用 `invoke_structured(SearchOutput)`，失败回退旧路径
- [ ] `ReflectionNode.run()` → 同上
- [ ] `FirstSummaryNode.run()` → 调用 `invoke_structured(SummaryOutput)`
- [ ] `ReflectionSummaryNode.run()` → 调用 `invoke_structured(ReflectionSummaryOutput)`
- [ ] `ReportStructureNode.run()` → 调用 `invoke_structured(List[ReportStructureItem])`

**注意**：节点是三引擎共享的（通过基类），改一处 = 改三处。

#### C.4 工具调用框架（Function Calling）

在 `veyrafish_core/llm_client.py` 中新增：

```python
def invoke_with_tools(
    self,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict],
    tool_executor: Callable[[str, dict], Any],
    max_rounds: int = 3,
    **kwargs,
) -> str:
    """支持多轮工具调用循环，直到模型输出最终文本。"""
```

- [ ] 实现 `invoke_with_tools()` 方法
- [ ] 定义 InsightEngine 的工具 JSON Schema（`search_topic_globally`、`search_hot_content` 等）
- [ ] 定义 MediaEngine 的工具 JSON Schema（`comprehensive_search`、`web_search_only` 等）
- [ ] 定义 QueryEngine 的工具 JSON Schema（`basic_search_news`、`deep_search_news` 等）
- [ ] 在 `BaseResearchAgent._initial_search_and_summary()` 中，如果模型支持 tools，使用 `invoke_with_tools()`；否则回退提示词 JSON

### 检验标准

- [ ] `python -m pytest tests/ -q` → 全部通过（旧测试 + 新输出模型测试）
- [ ] `tests/test_output_models.py` → 所有 Pydantic 模型验证测试通过
- [ ] 手动测试：`invoke_structured(SearchOutput)` 返回合法 Pydantic 对象
- [ ] 对比测试：同一个提示词，结构化输出 vs 旧 JSON 解析，统计失败率
- [ ] 所有节点在结构化失败时，仍可回退到旧的 JSON 解析路径（不会 crash）

### 回滚方式

- `invoke_structured` 是新增方法，删除不影响旧路径
- 节点使用 `try ... except` 包裹结构化调用，回退旧路径；删除 try 即恢复

---

## Stage V：验收与回归

### 全量检验清单

#### V.1 代码验证

- [ ] `python -m pytest tests/ -q` → 全部通过
- [ ] `python -c "from veyrafish_core import LLMClient, BaseNode, BaseResearchAgent"` → 无报错
- [ ] `python -c "from veyrafish_core.output_models import SearchOutput, SummaryOutput"` → 无报错
- [ ] `python -c "from InsightEngine.agent import DeepSearchAgent; print(DeepSearchAgent.__bases__)"` → 包含 `BaseResearchAgent`
- [ ] `python -c "from MediaEngine.agent import DeepSearchAgent; print(DeepSearchAgent.__bases__)"` → 同上
- [ ] `python -c "from QueryEngine.agent import DeepSearchAgent; print(DeepSearchAgent.__bases__)"` → 同上

#### V.2 文件行数验证

| 文件 | 预期行数上限 |
|------|------------|
| `veyrafish_core/llm_client.py` | ~200 |
| `veyrafish_core/base_node.py` | ~60 |
| `veyrafish_core/base_research_agent.py` | ~500 |
| `veyrafish_core/output_models.py` | ~80 |
| `InsightEngine/agent.py` | < 300（当前 ~1100） |
| `MediaEngine/agent.py` | < 250（当前 ~630） |
| `QueryEngine/agent.py` | < 200（当前 ~480） |
| `InsightEngine/llms/base.py` | < 10（re-export） |
| `MediaEngine/llms/base.py` | < 10 |
| `QueryEngine/llms/base.py` | < 10 |

#### V.3 功能验证（需真实环境）

- [ ] 启动系统后，三引擎能正常接收查询
- [ ] `task_events` 表记录节点事件（与 Phase 2 一致）
- [ ] ReportEngine 仍能正常读取三引擎输出
- [ ] Forum 论坛流不受影响

#### V.4 文档更新

- [ ] 更新 `PHASE_2_IMPLEMENTATION_CHECKLIST.md`（标记 3.4 推广策略完成）
- [ ] 更新 `MASTER_IMPLEMENTATION_CHECKLIST.md`
- [ ] 更新 `AGENT_UPGRADE_ROADMAP.md` 中 2.1/2.2/2.3/2.7 的状态
- [ ] 写本轮日志

---

## 阶段间依赖关系

```
Stage A（必须先做）
  ↓ A 完成后才能
Stage B（依赖 A 的 veyrafish_core 包存在）
  ↓ B 完成后才能
Stage C（依赖 B 的基类，改一处 = 改三处）
  ↓ C 完成后才能
Stage V（验收所有改动的累积效果）
```

---

## 风险评估

| 风险 | 应对策略 |
|------|---------|
| `client.beta.chat.completions.parse` 不被某些 API 提供商支持 | `invoke_structured_with_fallback()` 回退到旧 JSON 解析 |
| 三引擎节点共享后，某个引擎有独特行为被遗漏 | InsightEngine 保留独有方法；基类模板方法通过 `_get_*()` 钩子允许覆写 |
| ReportEngine 节点结构不同，不适合纳入基类 | ReportEngine 保持独立，不参与本轮重构 |
| `veyrafish_core` 的 import 路径在 Docker 中出问题 | `pyproject.toml` 中 `[tool.setuptools.packages.find]` 已包含 `veyrafish_core*` |

---

## 预估工作量

| 阶段 | 新增/修改文件数 | 预估改动量 |
|------|---------------|----------|
| Stage A | 新增 4 文件 + 修改 6 文件 | ~350 行新增，~100 行删除 |
| Stage B | 新增 1 文件 + 修改 3 文件 | ~600 行新增，~1800 行删除（三引擎瘦身） |
| Stage C | 修改 2 核心 + 5 节点文件 | ~300 行新增 |
| Stage V | 0 代码 | 文档 + 测试运行 |
| **合计** | ~10 文件 | 净减少 ~800 行代码 |
