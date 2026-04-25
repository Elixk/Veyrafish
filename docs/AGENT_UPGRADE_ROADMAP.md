# Veyrafish Agent 架构升级路线图

> 本文档基于当前仓库真实代码（2026-04-22）全量审计后编写，不是概念性建议。
> 每一项升级点都标注了「现状 → 升级方向 → 推荐技术 → 预估改动量 → 优先级」。

---

## 1. 当前架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Flask + SocketIO (app.py)             │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│    │ Insight  │ │  Media   │ │  Query   │ │  Report  │ │
│    │ Engine   │ │ Engine   │ │ Engine   │ │ Engine   │ │
│    │          │ │          │ │          │ │          │ │
│    │ Nodes:   │ │ Nodes:   │ │ Nodes:   │ │ Nodes:   │ │
│    │ Search → │ │ Search → │ │ Search → │ │ Template │ │
│    │ Summary →│ │ Summary →│ │ Summary →│ │→Layout→  │ │
│    │ Reflect →│ │ Reflect →│ │ Reflect →│ │ Budget→  │ │
│    │ Format   │ │ Format   │ │ Format   │ │ Chapter  │ │
│    └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│         │            │            │             │       │
│         └────────────┼────────────┘             │       │
│                      │                          │       │
│              ┌───────▼────────┐                 │       │
│              │  ForumEngine   │◄────────────────┘       │
│              │  (Log Monitor  │                          │
│              │   + LLM Host)  │                          │
│              └────────────────┘                          │
│                                                         │
│  通信方式：文件总线 (logs/*.log) + 内存状态 + SocketIO   │
│  LLM 调用：OpenAI-compatible API（直接调用，无框架）      │
│  工具调用：提示词要求 JSON → Python if/elif 分发           │
│  状态管理：自定义 dataclass（State/Paragraph/Research）    │
└─────────────────────────────────────────────────────────┘
```

### 核心优点（应保留）

1. **模块分离清晰**：四引擎+论坛各有独立目录，互不依赖
2. **报告引擎成熟度高**：IR Schema + 校验器 + 多 LLM 救援 + 流式章节生成，是项目最强模块
3. **反思循环**：搜索→总结→反思→再搜→再总结的闭环，每个段落独立运行
4. **状态可序列化**：`State.save_to_file()` / `load_from_file()` 已有
5. **task_store 事件层**：Phase 1-2 已建立的 SQLite 进度追踪 + 断点恢复

### 核心问题（需解决）

1. **三引擎代码高度重复**：Insight/Media/Query 的 `agent.py` 90% 代码相同，维护成本高
2. **工具调用不走 API 原生能力**：提示词里写 JSON Schema，人工解析 JSON，可靠性依赖 `fix_incomplete_json`
3. **Forum 协作基于文件轮询**：脆弱，依赖日志行格式、SummaryNode 类名
4. **无统一图执行器**：节点流程写死在 `agent.py` 里，无法动态调整边/分支
5. **无评估体系**：跑完了不知道质量变了没有

---

## 2. 可升级点清单

### 2.1 抽取共享 Agent 基类（代码去重）

| 项目 | 说明 |
|------|------|
| **现状** | Insight/Media/Query 各有一个 ~900 行的 `DeepSearchAgent`，结构几乎相同 |
| **升级方向** | 抽取 `veyrafish_core/base_research_agent.py`，三引擎只继承+覆写搜索工具 |
| **推荐技术** | 纯 Python 继承（不需要框架），配合 `abc.ABC` 定义抽象方法 |
| **改动量** | 中等（新建 1 文件，改 3 个 agent.py 为薄壳） |
| **优先级** | ★★★★★ — 这是所有后续升级的前提，不做这个后面每个改动都要改三遍 |

### 2.2 OpenAI 原生结构化输出（Structured Output）

| 项目 | 说明 |
|------|------|
| **现状** | 提示词里写 `output_schema_first_search` 字典，LLM 输出自由文本包含 JSON，用 `json.loads` + `fix_incomplete_json` 解析 |
| **升级方向** | 使用 OpenAI API 的 `response_format={"type": "json_schema", ...}` 参数，或 `tools=[...]` function calling |
| **推荐技术** | `openai>=1.3.0`（已安装）的 `response_format` 参数 + Pydantic 模型定义输出结构 |
| **改动量** | 小-中（每个 Node 的 `run()` 方法加 `response_format`，删除 repair 逻辑） |
| **优先级** | ★★★★★ — 直接提升可靠性，减少 JSON 解析失败率 |

**示例升级前后对比**：

```python
# 升级前（当前）
response = self.llm_client.stream_invoke_to_string(messages)
cleaned = extract_clean_response(response)
result = json.loads(fix_incomplete_json(cleaned))

# 升级后
from pydantic import BaseModel
class SearchOutput(BaseModel):
    search_query: str
    search_tool: str
    reasoning: str

response = client.beta.chat.completions.parse(
    model=model_name,
    messages=messages,
    response_format=SearchOutput,
)
result = response.choices[0].message.parsed  # 直接拿到 Pydantic 对象
```

### 2.3 OpenAI Function Calling（工具调用）

| 项目 | 说明 |
|------|------|
| **现状** | Agent 在提示词中列出可用工具名，LLM 回复 `search_tool: "search_topic_globally"`，Python 用 `if/elif` 分发 |
| **升级方向** | 使用 OpenAI API 的 `tools=[...]` 参数，让模型直接发出工具调用请求 |
| **推荐技术** | `openai` 库原生 function calling（`tools` + `tool_choice`） |
| **改动量** | 中（每个 Engine 的工具需要定义为 JSON Schema，`execute_search_tool` 改为自动分发） |
| **优先级** | ★★★★☆ — 配合 2.2 一起做效果最好 |

**示例**：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_topic_globally",
            "description": "在所有平台中全局搜索话题",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "limit_per_table": {"type": "integer", "default": 50}
                },
                "required": ["topic"]
            }
        }
    },
    # ... 其他工具
]
```

### 2.4 LangGraph 状态图（可选，非必须）

| 项目 | 说明 |
|------|------|
| **现状** | 节点流程写死在 `_process_paragraphs()` 的 for 循环里，反思轮次固定 |
| **升级方向** | 用 LangGraph 定义节点+边+条件分支，让流程可视化、可修改 |
| **推荐技术** | `langgraph>=0.2.0`（Google + LangChain 团队维护） |
| **改动量** | 大（需要将现有节点适配为 LangGraph 节点，重写 agent.py 调度逻辑） |
| **优先级** | ★★★☆☆ — 有价值但不紧迫；你的 `task_store` + `_emit` 已经覆盖了最急需的可观测性 |

**什么时候应该做**：
- 如果你需要「反思 3 轮后质量不达标就切换到更强的模型重试」这样的动态分支
- 如果你需要「搜索结果太少就自动扩展关键词再搜一轮」
- 如果你需要把流程图作为竞赛展示材料

**什么时候不需要做**：
- 当前固定的 `for i in range(MAX_REFLECTIONS)` 循环如果够用，不需要引入框架

### 2.5 MCP（Model Context Protocol）工具协议

| 项目 | 说明 |
|------|------|
| **现状** | 每个 Engine 的 `tools/` 目录各自封装搜索工具，代码不共享 |
| **升级方向** | 把搜索工具、情感分析器、数据库查询器暴露为 MCP Server，各引擎作为 MCP Client 调用 |
| **推荐技术** | `mcp` Python SDK（Anthropic 主导的开放协议） |
| **改动量** | 大（新建 MCP Server 进程，各引擎改为 MCP Client） |
| **优先级** | ★★☆☆☆ — 架构上优雅，但当前单进程部署不需要，后续微服务化时再做 |

### 2.6 Skill 架构（模块化能力包）

| 项目 | 说明 |
|------|------|
| **现状** | 每个 Engine 的 `prompts/prompts.py` 是巨型文件，包含所有提示词 |
| **升级方向** | 按能力拆分为 Skill 包：每个 Skill = 提示词 + Schema + 工具列表 + 验证逻辑 |
| **推荐技术** | 自定义 `Skill` 类 + YAML 清单文件（类似 Codex Skills 的 `SKILL.md` 模式） |
| **改动量** | 中（重构 prompts/ 目录为 skills/ 目录，每个 skill 一个文件夹） |
| **优先级** | ★★★☆☆ — 对代码组织有帮助，对竞赛展示有加分 |

**结构示例**：

```
InsightEngine/skills/
  topic_search/
    skill.yaml          # name, description, tools, schema
    prompt.md           # system prompt
    output_schema.json  # Pydantic 或 JSON Schema
  sentiment_analysis/
    skill.yaml
    prompt.md
    output_schema.json
```

### 2.7 统一 LLM 客户端（veyrafish_core）

| 项目 | 说明 |
|------|------|
| **现状** | 每个 Engine 有自己的 `llms/base.py`，代码 ~95% 相同 |
| **升级方向** | 抽取 `veyrafish_core/llm_client.py`，所有引擎共用 |
| **推荐技术** | 纯 Python 重构（或用 `litellm` 做多模型统一接口） |
| **改动量** | 中（新建 1 文件，4 个引擎的 llms/ 改为 import） |
| **优先级** | ★★★★☆ — 和 2.1 一起做，一次性解决重复代码 |

### 2.8 评估与回放系统

| 项目 | 说明 |
|------|------|
| **现状** | 跑完分析后没有自动化的质量评估手段 |
| **升级方向** | 固定金标准任务集 + 自动评分（LLM-as-Judge + 结构完整性检查） |
| **推荐技术** | `ragas` / 自定义评估管道 + `task_store` 记录评估结果 |
| **改动量** | 中-大（新建评估模块，定义评分标准） |
| **优先级** | ★★★★☆ — 没有评估就无法证明升级是否真的提升了质量 |

### 2.9 Pydantic AI（可选替代方案）

| 项目 | 说明 |
|------|------|
| **现状** | Pydantic 只用于 `config.py` 的配置管理 |
| **升级方向** | 用 Pydantic AI 框架直接定义 Agent，输入/输出全部类型安全 |
| **推荐技术** | `pydantic-ai`（Pydantic 团队维护，2025 发布） |
| **改动量** | 大（Agent 重写） |
| **优先级** | ★★☆☆☆ — 如果选了 LangGraph 就不需要这个，二者选其一 |

---

## 3. 推荐实施优先级

```
阶段一（立即可做，改动最小，收益最高）
├── 2.1 抽取共享 Agent 基类         ← 解除三引擎重复
├── 2.7 统一 LLM 客户端             ← 和 2.1 一起做
└── 2.2 OpenAI 原生结构化输出       ← 直接提升可靠性

阶段二（中期，需要设计评估后再做）
├── 2.3 OpenAI Function Calling    ← 配合 2.2
├── 2.6 Skill 架构                 ← 提升代码组织
└── 2.8 评估与回放系统             ← 证明质量提升

阶段三（远期/可选，按需引入）
├── 2.4 LangGraph 状态图           ← 需要动态分支时
├── 2.5 MCP 工具协议               ← 需要微服务化时
└── 2.9 Pydantic AI                ← 全面重写时
```

---

## 4. 新技术选型对照表

| 技术 | 当前用的是什么 | 升级为什么 | 安装命令 | 侵入程度 |
|------|-------------|----------|---------|---------|
| 结构化输出 | `json.loads + fix_incomplete_json` | `openai` `response_format=json_schema` | 已安装 | 低 |
| Function Calling | 提示词 JSON + if/elif | `openai` `tools=[...]` | 已安装 | 中 |
| Agent 基类 | 3 份 ~900 行重复代码 | `veyrafish_core.BaseResearchAgent` | 无需安装 | 中 |
| LLM 客户端 | 4 份 `llms/base.py` | `veyrafish_core.LLMClient` 或 `litellm` | `pip install litellm`（可选） | 中 |
| 状态图 | `for` 循环 + `if/elif` | `langgraph` | `pip install langgraph` | 大 |
| 工具协议 | Python 方法 + import | MCP Server/Client | `pip install mcp` | 大 |
| 评估 | 无 | `ragas` 或自定义 | `pip install ragas`（可选） | 中 |
| Skill 架构 | 巨型 `prompts.py` | 按能力拆分的 YAML/MD 包 | 无需安装 | 中 |

---

## 5. 竞赛加分建议

如果是为了**竞赛评审**加分，建议优先做：

1. **2.2 结构化输出** — 可以在技术报告中写"使用了 OpenAI 原生 JSON Schema 约束，确保输出可靠性"
2. **2.1 + 2.7 代码重构** — 可以在技术报告中写"抽取了统一的 Agent 基类与 LLM 客户端，降低维护成本"
3. **2.8 评估系统** — 可以展示"金标准对比实验结果"，量化分析质量
4. **2.6 Skill 架构** — 可以展示"模块化能力组合，支持快速扩展新分析维度"

这四项的组合能让评审看到：**不只是一个能跑的系统，而是一个有工程深度、有质量保障、可扩展的平台**。

---

## 6. 文档版本

- 编写日期：2026-04-22
- 基于代码版本：Phase 0-3 多轮升级后，pytest 61/61 通过
- 依赖审计：`requirements.txt` + `pyproject.toml` 双轨
