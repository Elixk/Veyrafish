# Veyrafish（微舆）模块化分析与二开升级指南

> 版本: v1.2.1 | 最后更新: 2026-04-08

本文档从**模块边界、数据契约、耦合关系**三个维度解剖 Veyrafish 系统，帮助你精确定位要改的模块、理解模块间如何交换数据、以及改完后如何验证系统仍然正常工作。

---

## 目录

- [一、模块总览与依赖拓扑](#一模块总览与依赖拓扑)
- [二、逐模块详细分析](#二逐模块详细分析)
- [三、模块间数据交换协议](#三模块间数据交换协议)
- [四、耦合度矩阵](#四耦合度矩阵)
- [五、二开升级保障体系](#五二开升级保障体系)
- [六、按场景的二开路线图](#六按场景的二开路线图)

---

## 一、模块总览与依赖拓扑

### 1.1 模块清单

| 编号 | 模块 | 路径 | 职责概述 | 进程模型 |
|------|------|------|----------|----------|
| M1 | **Orchestrator** | `app.py` | 进程编排、HTTP/WS API、配置管理 | Flask 主进程 |
| M2 | **GlobalConfig** | `config.py` + `.env` | 全局统一配置 | 被所有模块导入 |
| M3 | **QueryEngine** | `QueryEngine/` | 国内外新闻广度搜索 | Streamlit 子进程 (:8503) |
| M4 | **MediaEngine** | `MediaEngine/` | 多模态内容深度分析 | Streamlit 子进程 (:8502) |
| M5 | **InsightEngine** | `InsightEngine/` | 私有数据库舆情挖掘 | Streamlit 子进程 (:8501) |
| M6 | **ForumEngine** | `ForumEngine/` | Agent 论坛协作引擎 | 守护线程 (in M1) |
| M7 | **ReportEngine** | `ReportEngine/` | 多轮报告生成与渲染 | Flask Blueprint (in M1) |
| M8 | **MindSpider** | `MindSpider/` | 社交媒体数据采集 | 独立 CLI / 被 M1 调用初始化 |
| M9 | **SentimentModels** | `SentimentAnalysisModel/` | 情感分析模型集合 | 被 M5 导入 |
| M10 | **SharedUtils** | `utils/` | 跨模块通信与重试工具 | 被各模块导入 |
| M11 | **Frontend** | `templates/index.html` + `static/` | Web 用户界面 | 浏览器端 |
| M12 | **SingleEngineApp** | `SingleEngineApp/` | 三个 Agent 的 Streamlit 壳 | 子进程（由 M1 管理） |
| M13 | **Database** | PostgreSQL / MySQL | 舆情数据持久化 | 独立服务 |

### 1.2 依赖拓扑图

```
                          ┌─────────────┐
                          │  M11 前端    │
                          │ (浏览器)     │
                          └──────┬──────┘
                     HTTP/WS/SSE │
                          ┌──────▼──────┐
                          │  M1 编排器   │◄──── M2 全局配置
                          │  (app.py)   │
                          └──┬──┬──┬──┬─┘
                             │  │  │  │
               ┌─────────────┘  │  │  └──────────────┐
               │                │  │                  │
        ┌──────▼──────┐  ┌─────▼──▼─────┐    ┌──────▼──────┐
        │ M12 Streamlit│  │  M6 Forum    │    │ M7 Report   │
        │  壳 (x3)     │  │  Engine      │    │ Engine      │
        └──┬──┬──┬─────┘  └──────┬───────┘    └──────┬──────┘
           │  │  │               │                    │
    ┌──────┘  │  └──────┐     读/写                 读取
    │         │         │   logs/*.log            *_reports/
    ▼         ▼         ▼        │                    │
  ┌────┐  ┌────┐  ┌─────┐       │              ┌─────▼──────┐
  │ M3 │  │ M4 │  │ M5  │◄──────┘              │ final_     │
  │Qry │  │Med │  │Ins  │                      │ reports/   │
  └─┬──┘  └─┬──┘  └──┬──┘                      └────────────┘
    │        │        │
    │        │        ├───→ M9 情感模型
    │        │        └───→ M13 数据库 ◄──── M8 MindSpider
    │        │
    ▼        ▼
 外部API   外部API           M10 SharedUtils (被 M3/M4/M5/M6/M7 导入)
(Tavily)  (Bocha/Anspire)
```

---

## 二、逐模块详细分析

### M1 — Orchestrator (`app.py`)

| 属性 | 描述 |
|------|------|
| **功能** | 系统总入口；子进程生命周期管理；HTTP/WebSocket API；配置读写 |
| **输入** | 前端 HTTP 请求、`.env` 配置文件 |
| **输出** | WebSocket 事件（日志/状态/论坛消息）、JSON API 响应 |
| **内部子模块** | 进程表(`processes`)、日志监听线程、Forum 日志解析 |
| **依赖** | M2(配置)、M6(ForumEngine)、M7(ReportEngine Blueprint)、M8(MindSpider 初始化)、M12(Streamlit 脚本路径) |
| **暴露接口** | 18 个 HTTP 端点 + 2 个 WebSocket 事件 |

**关键数据结构**：
```python
processes = {
    'insight': {'process': Popen, 'port': 8501, 'status': str, 'output': list},
    'media':   {'process': Popen, 'port': 8502, 'status': str, 'output': list},
    'query':   {'process': Popen, 'port': 8503, 'status': str, 'output': list},
    'forum':   {'process': None,  'port': None,  'status': str, 'output': list},
}
```

---

### M2 — GlobalConfig (`config.py` + `.env`)

| 属性 | 描述 |
|------|------|
| **功能** | 集中管理所有环境变量，类型安全 |
| **输入** | `.env` 文件、系统环境变量 |
| **输出** | `settings` 单例对象 |
| **被依赖方** | 所有其他模块（M1/M3-M8/M10/M12） |
| **接口** | `settings.*` 属性访问、`reload_settings()` 热加载 |

**核心契约**：所有配置字段定义在 `Settings(BaseSettings)` 类中，字段名与 `.env` 键名完全一致（大写），子模块通过 `from config import settings` 获取。

**子模块配置**：每个 Engine 内的 `utils/config.py` 也继承 `BaseSettings`，可定义 Engine 专属参数，但基础 DB/LLM 配置仍从根 `.env` 读取。

---

### M3 — QueryEngine

| 属性 | 描述 |
|------|------|
| **功能** | 通过 Tavily API 执行多轮搜索-反思-总结循环 |
| **输入** | 查询字符串 `query`（通过 Streamlit URL 参数接收） |
| **输出** | Markdown 报告 → `query_engine_streamlit_reports/*.md`；日志 → `logs/query.log` |
| **依赖** | M2(配置)、M10(forum_reader, retry_helper)、外部(Tavily API) |
| **被依赖方** | M6(读取日志)、M7(读取报告)、M1(进程管理) |

**内部子模块分解**：

| 子模块 | 路径 | 功能 | 输入/输出 |
|--------|------|------|-----------|
| `agent.py` | `QueryEngine/agent.py` | 主调度器 `DeepSearchAgent` | `query` → `final_report (str)` |
| `llms/base.py` | `QueryEngine/llms/` | OpenAI 兼容 LLM 客户端 | messages → completion |
| `nodes/` | `QueryEngine/nodes/` | 6 个处理节点管道 | 见下方节点接口表 |
| `tools/search.py` | `QueryEngine/tools/` | `TavilyNewsAgency`（6 种搜索方法） | query → `TavilyResponse` |
| `state/state.py` | `QueryEngine/state/` | Agent 状态管理 | 段落列表、搜索历史、最终报告 |
| `prompts/prompts.py` | `QueryEngine/prompts/` | 提示词模板 | 常量字符串 |
| `utils/config.py` | `QueryEngine/utils/` | Engine 专属配置 | `.env` → `Settings` |

**节点管道接口**：

```
ReportStructureNode: (query: str) → State{paragraphs[]}
FirstSearchNode:     (title, content) → {search_query, search_tool, reasoning}
FirstSummaryNode:    (title, content, search_results) → State{paragraph.latest_summary}
ReflectionNode:      (title, content, latest_summary) → {search_query, search_tool, reasoning}
ReflectionSummaryNode: (title, content, search_results, latest_summary) → State{paragraph.latest_summary}
ReportFormattingNode: (report_data[]) → formatted_report: str
```

---

### M4 — MediaEngine

| 属性 | 描述 |
|------|------|
| **功能** | 多模态内容分析（视频、图片、结构化数据卡片） |
| **输入** | 查询字符串（Streamlit URL 参数） |
| **输出** | Markdown 报告 → `media_engine_streamlit_reports/*.md`；日志 → `logs/media.log` |
| **依赖** | M2、M10、外部(Bocha API / Anspire API) |
| **被依赖方** | M6、M7、M1 |

**与 M3 的结构差异**：
- `tools/search.py` 封装 `BochaMultimodalSearch` + `AnspireAISearch`
- `agent.py` 包含 `DeepSearchAgent` 和 `AnspireSearchAgent` 两个类
- `create_agent()` 工厂函数根据 `SEARCH_TOOL_TYPE` 配置选择具体实现

**搜索工具返回数据结构**：
```python
@dataclass
class BochaResponse:
    webpages: List[BochaWebpage]  # name, url, snippet, date_last_crawled
    # ... images, videos, knowledge 等多模态字段
```

---

### M5 — InsightEngine

| 属性 | 描述 |
|------|------|
| **功能** | 私有舆情数据库深度挖掘 + 关键词优化 + 聚类采样 + 情感分析 |
| **输入** | 查询字符串（Streamlit URL 参数） |
| **输出** | Markdown 报告 → `insight_engine_streamlit_reports/*.md`；日志 → `logs/insight.log` |
| **依赖** | M2、M9(情感模型)、M10、M13(数据库) |
| **被依赖方** | M6、M7、M1 |

**独有子模块**：

| 子模块 | 功能 | 接口 |
|--------|------|------|
| `tools/keyword_optimizer.py` | 用 Qwen 将自然语言优化为 DB 搜索关键词 | `optimize_keywords(query, context)` → `{optimized_keywords[], reasoning}` |
| `tools/sentiment_analyzer.py` | 多语言情感分析集成 | `analyze_query_results(results, text_field)` → `{sentiment_analysis}` |
| `tools/search.py` | 本地数据库查询 (`MediaCrawlerDB`) | 5 种查询方法 → `DBResponse` |
| `utils/db.py` | SQLAlchemy 异步数据库访问 | `fetch_all(sql, params)` → `List[Dict]` |

**数据库查询工具返回结构**：
```python
@dataclass
class QueryResult:
    platform: str           # xhs/dy/wb/bili/ks/tieba/zhihu
    content_type: str       # post/comment
    title_or_content: str
    author_nickname: str
    url: str
    publish_time: datetime
    engagement: Dict[str, int]  # {likes, comments, shares, views}
    hotness_score: float

@dataclass
class DBResponse:
    tool_name: str
    parameters: Dict[str, Any]
    results: List[QueryResult]
    results_count: int
    metadata: Dict          # 包含 sentiment_analysis（若启用）
```

---

### M6 — ForumEngine

| 属性 | 描述 |
|------|------|
| **功能** | 监控三个 Agent 日志，提取分析总结，触发 LLM 主持人引导讨论 |
| **输入** | `logs/insight.log`、`logs/media.log`、`logs/query.log` |
| **输出** | `logs/forum.log`（Agent 发言 + 主持人发言） |
| **依赖** | M2(LLM 配置)、M10(retry_helper) |
| **被依赖方** | M1(启动/停止)、M3/M4/M5(通过 M10.forum_reader 读取主持人发言)、M7(读取论坛日志) |

**内部子模块**：

| 子模块 | 功能 | 关键接口 |
|--------|------|----------|
| `monitor.py` (`LogMonitor`) | 日志文件变化检测、SummaryNode 输出提取、JSON 多行解析 | `start_monitoring()` / `stop_monitoring()` |
| `llm_host.py` (`ForumHost`) | LLM 主持人发言生成 | `generate_host_speech(forum_logs: List[str])` → `str` |

**日志协议**（forum.log 行格式）：
```
[HH:MM:SS] [SOURCE] content_one_line
```
其中 `SOURCE` ∈ `{SYSTEM, QUERY, INSIGHT, MEDIA, HOST}`

**触发条件**：每积累 5 条 Agent 发言 → 调用 `generate_host_speech()` → 写入 `[HOST]` 行

---

### M7 — ReportEngine

| 属性 | 描述 |
|------|------|
| **功能** | 将三引擎报告 + 论坛日志整合为结构化 IR，渲染为交互式 HTML |
| **输入** | `*_streamlit_reports/*.md`（三引擎报告）、`logs/forum.log`（论坛日志）、用户 query |
| **输出** | `final_reports/*.html`、`final_reports/ir/*.json`、`final_reports/chapters/`、SSE 流式事件 |
| **依赖** | M2、外部 LLM |
| **被依赖方** | M1(Blueprint 注册) |

**内部子模块分解**：

| 子模块 | 路径 | 功能 | 核心接口 |
|--------|------|------|----------|
| `agent.py` | 总调度器 | `generate_report(query, reports, forum_logs)` → `{html_content, report_id, ...}` |
| `flask_interface.py` | HTTP API 层 | 任务队列、SSE 推送、文件下载 |
| `core/template_parser.py` | 模板 Markdown 切片 | `parse_template_sections(md)` → `List[TemplateSection]` |
| `core/chapter_storage.py` | 章节 JSON 缓存 | `start_session() / save_chapter()` |
| `core/stitcher.py` | IR 装订器 | `build_document(id, meta, chapters)` → `DocumentIR` |
| `ir/schema.py` | 16 种 IR 块类型定义 | 常量 + JSON Schema |
| `ir/validator.py` | 章节 JSON 校验 | `validate(chapter_json)` → `bool` |
| `nodes/` | 4 个推理节点 | 模板选择 / 布局设计 / 篇幅规划 / 章节生成 |
| `renderers/html_renderer.py` | IR → HTML | `render(document_ir)` → `html: str` |
| `renderers/pdf_renderer.py` | HTML → PDF | `export_pdf(html)` → `bytes` |
| `report_template/` | Markdown 模板库 | 被模板选择节点读取 |

**Document IR 顶层结构**：
```json
{
  "documentId": "report-xxxxxxxx",
  "meta": { "title", "subtitle", "themeTokens", "toc", "hero", "wordPlan" },
  "chapters": [
    {
      "chapterId": "S1",
      "title": "...",
      "anchor": "...",
      "order": 10,
      "blocks": [ { "type": "heading|paragraph|table|..." } ]
    }
  ]
}
```

---

### M8 — MindSpider

| 属性 | 描述 |
|------|------|
| **功能** | 社交媒体数据采集（话题提取 + 深度爬取） |
| **输入** | CLI 参数或 M1 调用 `initialize_database()` |
| **输出** | 数据写入 M13 数据库 |
| **依赖** | M2(配置)、M13(数据库)、外部(MediaCrawler 子模块、Playwright) |
| **被依赖方** | M1(数据库初始化)、M5(读取爬取的数据) |

**内部子模块**：

| 子模块 | 功能 |
|--------|------|
| `BroadTopicExtraction/` | 从热榜获取新闻 → LLM 提取话题 → 写入 `daily_news` / `daily_topics` |
| `DeepSentimentCrawling/` | 基于话题关键词到各平台搜索 → MediaCrawler 爬取 → 写入平台数据表 |
| `schema/` | DDL 文件 + ORM 模型 + 异步建表脚本 |

---

### M9 — SentimentModels

| 属性 | 描述 |
|------|------|
| **功能** | 5 种情感分析方案（BERT/GPT-2/多语言/Qwen3/传统 ML） |
| **输入** | 文本字符串或文本列表 |
| **输出** | 情感标签 + 置信度 |
| **被依赖方** | M5(通过 sentiment_analyzer.py 集成) |

**标准化输出接口**：
```python
@dataclass
class SentimentResult:
    text: str
    label: str            # positive / negative / neutral
    confidence: float     # 0.0 ~ 1.0
    success: bool
    analysis_performed: bool
    error_message: Optional[str]
```

---

### M10 — SharedUtils (`utils/`)

| 属性 | 描述 |
|------|------|
| **功能** | 跨模块通信工具和通用辅助函数 |
| **被依赖方** | M3、M4、M5、M6、M7 |

**三个工具的接口**：

| 工具 | 功能 | 关键接口 |
|------|------|----------|
| `forum_reader.py` | Agent 读取主持人发言 | `get_latest_host_speech()` → `Optional[str]` |
| | | `get_all_host_speeches()` → `List[{timestamp, content}]` |
| | | `get_recent_agent_speeches(limit)` → `List[{timestamp, agent, content}]` |
| | | `format_host_speech_for_prompt(speech)` → `str`（格式化为 Prompt 片段） |
| `retry_helper.py` | 通用重试机制 | `@with_retry(config)` / `@with_graceful_retry(config, default_return)` |
| | | 预定义配置：`LLM_RETRY_CONFIG` / `SEARCH_API_RETRY_CONFIG` / `DB_RETRY_CONFIG` |
| `github_issues.py` | 错误信息格式化 | `error_with_issue_link(error)` → 含 GitHub Issue 链接的提示 |

---

### M11 — Frontend

| 属性 | 描述 |
|------|------|
| **功能** | 用户界面（控制台、搜索、论坛、报告预览） |
| **输入** | 用户交互 |
| **输出** | HTTP 请求到 M1 |
| **通信方式** | Socket.IO（实时日志/论坛）+ REST API（配置/搜索/报告）+ SSE（报告进度） |

---

### M12 — SingleEngineApp

| 属性 | 描述 |
|------|------|
| **功能** | 三个 Streamlit 应用壳，包装 M3/M4/M5 的 `DeepSearchAgent` |
| **输入** | URL 查询参数 `?query=...&auto_search=true` |
| **输出** | Streamlit 页面 + 调用 Agent 生成报告 |
| **依赖** | M3/M4/M5(Agent 类)、M2(配置) |
| **被依赖方** | M1(子进程管理) |

**转发机制**：M1 通过 URL 参数向 Streamlit 传递搜索查询，Streamlit 接收后自动调用 Agent 的 `research(query)` 方法。

---

### M13 — Database

| 属性 | 描述 |
|------|------|
| **功能** | 舆情数据持久化存储 |
| **支持引擎** | PostgreSQL（推荐）/ MySQL |
| **数据写入方** | M8 (MindSpider) |
| **数据读取方** | M5 (InsightEngine) |
| **连接方式** | SQLAlchemy 2.x 异步引擎（asyncpg / aiomysql） |

---

## 三、模块间数据交换协议

### 3.1 数据交换方式总览

Veyrafish 的模块间通信使用了**五种机制**：

| 编号 | 方式 | 使用场景 | 数据格式 |
|------|------|----------|----------|
| D1 | **文件系统（日志）** | M3/M4/M5 → M6 | Loguru 格式文本行 |
| D2 | **文件系统（报告）** | M3/M4/M5 → M7 | Markdown 文件 |
| D3 | **文件系统（论坛）** | M6 ↔ M3/M4/M5 | `forum.log` 特定行格式 |
| D4 | **Python 导入** | M2→所有, M9→M5, M10→多方 | Python 对象 |
| D5 | **HTTP/WebSocket** | M11→M1, M1→M12 | JSON / 事件流 |
| D6 | **数据库** | M8→M13→M5 | SQL 行 / ORM 对象 |

### 3.2 协议详解

#### D1 — Agent 日志协议（M3/M4/M5 → M6）

**写入端**（Agent 的 SummaryNode）：通过 Loguru 将总结内容写入日志文件。关键特征行包含以下模式之一：
- 类名：`FirstSummaryNode` / `ReflectionSummaryNode`
- 模块路径：`*.nodes.summary_node`
- 标识文本：`正在生成首次段落总结` / `正在生成反思总结`
- JSON 内容以 `清理后的输出: {` 开头

**读取端**（M6 LogMonitor）：
1. 按文件位置增量读取新行
2. 通过 `is_target_log_line()` 匹配上述模式
3. 通过 `process_lines_for_json()` 提取多行 JSON
4. 从 JSON 中取 `updated_paragraph_latest_state` 或 `paragraph_latest_state` 字段

**二开影响**：如果修改了 SummaryNode 的类名或日志格式，必须同步更新 M6 的 `target_node_patterns` 列表。

---

#### D2 — 报告文件协议（M3/M4/M5 → M7）

**写入端**：每个 Agent 完成 `research()` 后将 Markdown 报告写入对应目录：
- `query_engine_streamlit_reports/deep_search_report_*_{timestamp}.md`
- `media_engine_streamlit_reports/deep_search_report_*_{timestamp}.md`
- `insight_engine_streamlit_reports/deep_search_report_*_{timestamp}.md`

**读取端**（M7 ReportAgent）：
1. `FileCountBaseline` 监控三个目录的 `.md` 文件数量变化
2. `get_latest_files()` 按修改时间取每个目录最新文件
3. `load_input_files()` 读取文件内容为纯字符串
4. 传入 `generate_report(query, reports=[query_md, media_md, insight_md], forum_logs)`

**契约要点**：
- 文件必须是 `.md` 后缀
- 文件内容为纯 Markdown 文本
- 目录名必须与 M7 中 `_initialize_file_baseline()` 定义的一致

---

#### D3 — 论坛协议（M6 ↔ M3/M4/M5）

**M6 → forum.log 写入格式**：
```
[HH:MM:SS] [SOURCE] 单行内容（换行符转义为\n）
```

**M3/M4/M5 读取路径**：
```python
# 在各 Agent 的 SummaryNode 中
from utils.forum_reader import get_latest_host_speech, format_host_speech_for_prompt

host_speech = get_latest_host_speech()
if host_speech:
    prompt += format_host_speech_for_prompt(host_speech)
```

**契约要点**：
- `[HOST]` 标签标识主持人发言
- `\n` 为转义换行符（非真实换行）
- `forum_reader.py` 使用正则 `\[(\d{2}:\d{2}:\d{2})\]\s*\[HOST\]\s*(.+)` 匹配

---

#### D4 — Python 导入依赖

| 导入方 | 被导入模块 | 接口 |
|--------|-----------|------|
| M1 | `from config import settings` | 配置属性 |
| M1 | `from ForumEngine.monitor import start_forum_monitoring` | `start/stop_forum_monitoring()` |
| M1 | `from ReportEngine.flask_interface import report_bp` | Flask Blueprint |
| M1 | `from MindSpider.main import MindSpider` | `MindSpider.initialize_database()` |
| M3/M4/M5 | `from utils.forum_reader import get_latest_host_speech` | `Optional[str]` |
| M3/M4/M5 | `from utils.retry_helper import with_retry` | 装饰器 |
| M5 | `from InsightEngine.tools.sentiment_analyzer import multilingual_sentiment_analyzer` | 情感分析器实例 |
| M12 | `from QueryEngine import DeepSearchAgent` | Agent 类 |

---

#### D5 — HTTP/WebSocket 协议

**M11 → M1 搜索流程**：
```
POST /api/search {query: "武汉大学舆情"}
    → M1 检查运行中的 Agent
    → 分别向 8501/8502/8503 发送 POST /api/search
    → 汇总结果返回前端
```

**M1 → M11 实时推送**：
```
Socket.IO 'console_output': {app: 'insight', line: '[12:30:45] ...'}
Socket.IO 'forum_message': {type: 'host', sender: 'Forum Host', content: '...'}
Socket.IO 'status_update': {insight: {status: 'running', port: 8501}, ...}
```

**M7 SSE 报告流**：
```
GET /api/report/stream/{task_id}
    → event: stage    data: {stage: 'template_selected', ...}
    → event: progress data: {progress: 20, message: '...'}
    → event: chapter_chunk data: {chapterId: 'S1', delta: '...'}
    → event: chapter_status data: {chapterId: 'S1', status: 'completed'}
```

---

#### D6 — 数据库协议

**M8 写入** → **M13 存储** → **M5 读取**

```
M8 (MindSpider)
    ├── BroadTopicExtraction → daily_news, daily_topics, topic_news_relation
    └── DeepSentimentCrawling → xhs_note, douyin_aweme, weibo_note, ...（7大平台表）

M5 (InsightEngine)
    └── tools/search.py (MediaCrawlerDB)
        └── utils/db.py (fetch_all) ──SQL──→ 异步查询以上所有表
```

**表命名契约**：`MediaCrawlerDB` 中硬编码了以下表名和字段名：
- 内容表：`xhs_note` / `douyin_aweme` / `kuaishou_video` / `bilibili_video` / `weibo_note` / `tieba_note` / `zhihu_content`
- 评论表：以上表名 + `_comment` 后缀
- 通用字段：`title` / `desc` / `content` / `nickname` / `liked_count` / `comment_count` / `share_count` 等

---

## 四、耦合度矩阵

以下矩阵展示模块间的耦合强度（**强**=直接 Python 导入或共享数据结构，**中**=通过文件/API 间接通信，**弱**=仅通过配置关联，**无**=无依赖）：

| | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 | M13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **M1** | - | 强 | 中 | 中 | 中 | 强 | 强 | 强 | 无 | 无 | 中 | 中 | 无 |
| **M2** | | - | 强 | 强 | 强 | 强 | 强 | 强 | 无 | 无 | 无 | 强 | 无 |
| **M3** | | | - | 无 | 无 | 中 | 中 | 无 | 无 | 强 | 无 | 强 | 无 |
| **M4** | | | | - | 无 | 中 | 中 | 无 | 无 | 强 | 无 | 强 | 无 |
| **M5** | | | | | - | 中 | 中 | 无 | 强 | 强 | 无 | 强 | 强 |
| **M6** | | | | | | - | 无 | 无 | 无 | 强 | 无 | 无 | 无 |
| **M7** | | | | | | | - | 无 | 无 | 无 | 无 | 无 | 无 |
| **M8** | | | | | | | | - | 无 | 无 | 无 | 无 | 强 |
| **M9** | | | | | | | | | - | 无 | 无 | 无 | 无 |

**关键耦合点总结**：

1. **M2 (Config) 是最高扇出模块** — 几乎所有模块都依赖它。修改配置字段名必须全局搜索替换。
2. **M6 与 M3/M4/M5 通过日志格式耦合** — 日志行格式变化会破坏论坛协作。
3. **M7 与 M3/M4/M5 通过文件目录名耦合** — 报告输出目录名变化会导致报告引擎找不到输入。
4. **M5 与 M13 通过表名/字段名耦合** — 数据库 Schema 变化需要同步修改 `tools/search.py` 的 SQL。
5. **M3/M4/M5 三引擎之间完全解耦** — 互不直接依赖，仅通过 M6 间接协作。

---

## 五、二开升级保障体系

### 5.1 升级前检查清单

```
□ 1. 确认要修改的模块编号（M1-M13）
□ 2. 从耦合度矩阵找出所有与之耦合的模块
□ 3. 列出该模块的所有输入/输出接口
□ 4. 确认修改是否改变了接口契约（函数签名、数据格式、文件路径）
□ 5. 如果改变了契约，同步修改所有依赖方
```

### 5.2 接口契约验证规则

#### 规则 1：Agent 节点接口兼容性

所有 Agent 节点必须遵循统一接口：

```python
class BaseNode:
    def __init__(self, llm_client: LLMClient): ...
    def run(self, input_data: dict) -> dict: ...
    def mutate_state(self, input_data, state: State, paragraph_index: int) -> State: ...
```

**验证方法**：新节点必须能通过以下测试：
```python
node = YourNewNode(llm_client)
result = node.run({"title": "test", "content": "test"})
assert isinstance(result, dict)
assert "search_query" in result or "paragraph_latest_state" in result
```

#### 规则 2：搜索工具返回值兼容性

M3 的搜索结果必须可转换为以下字典格式（M3/M4/M5 共用的中间格式）：

```python
search_result = {
    'title': str,           # 必须
    'url': str,             # 必须
    'content': str,         # 必须
    'score': float | None,  # 可选
    'raw_content': str,     # 必须
    'published_date': str | None  # 可选
}
```

**验证方法**：任何新搜索工具的返回值必须能成功转换为上述格式。

#### 规则 3：日志格式兼容性（M3/M4/M5 → M6）

SummaryNode 的日志输出必须满足 M6 的识别条件之一：
- 包含类名 `FirstSummaryNode` 或 `ReflectionSummaryNode`
- 包含路径模式 `*.nodes.summary_node`
- 包含文本 `正在生成首次段落总结` 或 `正在生成反思总结`

JSON 内容格式必须包含：
```json
{
  "updated_paragraph_latest_state": "...(总结文本)..."
}
```
或
```json
{
  "paragraph_latest_state": "...(总结文本)..."
}
```

**验证方法**：
```python
from ForumEngine.monitor import LogMonitor
monitor = LogMonitor()
assert monitor.is_target_log_line(your_new_log_line) == True
```

#### 规则 4：报告文件输出兼容性（M3/M4/M5 → M7）

- 文件后缀必须是 `.md`
- 文件位于对应的 `*_streamlit_reports/` 目录
- 文件内容为可读的 Markdown 文本

#### 规则 5：论坛协议兼容性（M6 ↔ M3/M4/M5）

forum.log 行格式：
```
[HH:MM:SS] [SOURCE] single_line_content_with_escaped_newlines
```
`SOURCE` 必须是 `SYSTEM`、`QUERY`、`INSIGHT`、`MEDIA`、`HOST` 之一。

Agent 读取端使用的正则：
```regex
\[(\d{2}:\d{2}:\d{2})\]\s*\[HOST\]\s*(.+)
```

#### 规则 6：Document IR 块类型兼容性（M7 内部）

新增块类型必须：
1. 在 `ir/schema.py` 的 `ALLOWED_BLOCK_TYPES` 列表中注册
2. 定义对应的 JSON Schema 并加入 `block_variants`
3. 在 `renderers/html_renderer.py` 中有对应的渲染方法
4. `ir/validator.py` 能通过校验

#### 规则 7：配置兼容性（M2）

新增配置项必须：
1. 在 `Settings(BaseSettings)` 中定义带默认值的字段
2. 在 `.env.example` 中添加说明
3. 如果前端需要编辑，在 `app.py` 的 `CONFIG_KEYS` 列表中注册

### 5.3 模块级测试策略

| 模块 | 测试方式 | 测试命令/方法 |
|------|----------|---------------|
| M3 | 单独运行 Streamlit 应用 | `streamlit run SingleEngineApp/query_engine_streamlit_app.py --server.port 8503` |
| M4 | 单独运行 Streamlit 应用 | `streamlit run SingleEngineApp/media_engine_streamlit_app.py --server.port 8502` |
| M5 | 单独运行 Streamlit 应用 | `streamlit run SingleEngineApp/insight_engine_streamlit_app.py --server.port 8501` |
| M6 | 单元测试 | `pytest tests/test_monitor.py -v` |
| M7 | CLI 工具 | `python report_engine_only.py --query "测试主题"` |
| M7 | 渲染验证 | `python regenerate_latest_html.py` |
| M7 | 安全测试 | `pytest tests/test_report_engine_sanitization.py -v` |
| M8 | CLI 工具 | `cd MindSpider && python main.py --setup` |
| 集成 | 完整系统 | `python app.py` + 前端发起搜索 |

### 5.4 回归验证流程

```
升级完成
  │
  ├── 1. 静态检查
  │     ├── grep 所有 import 路径是否仍有效
  │     ├── 检查修改模块的 __init__.py 导出是否完整
  │     └── 确认 .env.example 与 Settings 类字段一致
  │
  ├── 2. 单元级验证
  │     ├── 升级模块自身的单元测试通过
  │     └── 依赖方模块的单元测试通过
  │
  ├── 3. 接口级验证
  │     ├── 搜索工具返回值格式验证
  │     ├── 节点输入输出格式验证
  │     ├── 日志格式被 ForumEngine 正确识别
  │     └── 报告文件被 ReportEngine 正确读取
  │
  └── 4. 端到端验证
        ├── 完整流程：用户提问 → 三 Agent 分析 → 论坛协作 → 报告生成
        ├── 验证 forum.log 中出现 [HOST] 发言
        ├── 验证 final_reports/ 中生成了 HTML 报告
        └── 在浏览器中打开报告确认渲染正确
```

---

## 六、按场景的二开路线图

### 场景 A：替换/扩展搜索能力

**影响模块**：M3 或 M4 的 `tools/search.py`

**步骤**：
1. 在 `tools/` 下新建搜索类，实现与现有搜索类相同的返回结构
2. 在 `agent.py` 的 `execute_search_tool()` 中注册新工具
3. 修改 `prompts/prompts.py` 中的工具描述，让 LLM 知道新工具的存在
4. 在 `config.py` / `.env` 中添加新 API Key 配置
5. **不影响**：M6、M7、M10（它们不关心搜索工具细节）

**验证**：单独运行 Streamlit → 检查日志 → 检查生成的 Markdown 报告

---

### 场景 B：添加新 Agent

**影响模块**：M1、M6、M7、M12、新模块

**步骤**：
1. 以 `QueryEngine/` 为模板创建新 Engine 目录
2. 在 `SingleEngineApp/` 下创建对应的 Streamlit 壳
3. 在 `app.py` 中注册：
   - `STREAMLIT_SCRIPTS['new_agent'] = 'SingleEngineApp/new_app.py'`
   - `processes['new_agent'] = {'process': None, 'port': 8504, ...}`
4. 在 `ForumEngine/monitor.py` 中添加新日志监控：
   - `self.monitored_logs['new_agent'] = self.log_dir / 'new_agent.log'`
5. 在 `ReportEngine/agent.py` 中扩展报告输入：
   - `_normalize_reports()` 增加新引擎的键

**契约检查**：新 Agent 的 SummaryNode 日志格式必须符合规则 3

---

### 场景 C：修改数据库 Schema

**影响模块**：M8、M5、M13

**步骤**：
1. 修改 `MindSpider/schema/` 下的 DDL 和 ORM 模型
2. 同步修改 `InsightEngine/tools/search.py` 中的 SQL 查询和 `QueryResult` 映射
3. 如需新表，在 `MindSpider/schema/init_database.py` 中添加建表逻辑
4. **不影响**：M3、M4、M6、M7（它们不直接访问数据库）

**验证**：`python MindSpider/main.py --setup` → 检查表结构 → 运行 InsightEngine 验证查询

---

### 场景 D：自定义报告渲染

**影响模块**：M7 内部

**步骤**：
1. 新增 IR 块类型：修改 `ir/schema.py`
2. 修改章节生成提示词：`nodes/chapter_generation_node.py` 和 `prompts/prompts.py`
3. 添加渲染逻辑：`renderers/html_renderer.py`
4. **不影响**：M3、M4、M5、M6（报告引擎完全内聚）

**验证**：`python report_engine_only.py` → 检查 HTML 输出 → `python regenerate_latest_html.py`

---

### 场景 E：替换 LLM 提供商

**影响模块**：M2（仅配置）

**步骤**：修改 `.env` 中对应 Agent 的三个参数即可。所有 LLM 调用统一走 OpenAI SDK 兼容格式。

**如果新提供商不兼容 OpenAI 格式**：
1. 在对应 Engine 的 `llms/base.py` 中适配新 SDK
2. 保持 `LLMClient` 的公共接口不变（`chat()` / `stream()` 等）
3. **不影响**：Nodes 层和 Agent 层无需修改

---

### 场景 F：修改论坛协作机制

**影响模块**：M6、可能影响 M3/M4/M5（通过 M10）

**步骤**：
1. 修改主持人触发逻辑：`ForumEngine/monitor.py` 的 `host_speech_threshold`
2. 修改主持人提示词：`ForumEngine/llm_host.py` 的 `_build_system_prompt()`
3. 如果修改了 forum.log 行格式：同步更新 `utils/forum_reader.py` 的正则
4. 如果新增了 Agent 标签：更新 `app.py` 的 `parse_forum_log_line()` 中的白名单

**验证**：运行完整系统 → 观察 `logs/forum.log` 是否有 `[HOST]` 发言 → 检查 Agent 是否读到主持人引导

---

## 附录：模块健康检查脚本

以下 Python 片段可用于快速验证各模块的基本可用性：

```python
# 验证配置加载
from config import settings
assert settings.DB_HOST != "your_db_host", "数据库未配置"
assert settings.INSIGHT_ENGINE_API_KEY, "Insight Agent LLM 未配置"

# 验证 QueryEngine 节点管道完整性
from QueryEngine.nodes import (
    ReportStructureNode, FirstSearchNode, ReflectionNode,
    FirstSummaryNode, ReflectionSummaryNode, ReportFormattingNode
)

# 验证 ForumEngine 日志识别
from ForumEngine.monitor import LogMonitor
monitor = LogMonitor()
test_line = "2025-01-01 12:00:00.000 | INFO | QueryEngine.nodes.summary_node - 正在生成首次段落总结"
assert monitor.is_target_log_line(test_line), "ForumEngine 无法识别 SummaryNode 日志"

# 验证 forum_reader 协议
from utils.forum_reader import get_latest_host_speech
# 不报错即通过（返回 None 或 str 均可）

# 验证 ReportEngine IR Schema
from ReportEngine.ir.schema import ALLOWED_BLOCK_TYPES, CHAPTER_JSON_SCHEMA
assert len(ALLOWED_BLOCK_TYPES) >= 16, "IR 块类型不完整"

# 验证 InsightEngine 数据库工具
from InsightEngine.tools.search import MediaCrawlerDB, DBResponse
db = MediaCrawlerDB()
# 不报错即通过
```

---

*本文档基于 Veyrafish v1.2.1 源码结构分析生成。模块边界和接口描述以源码为准。*
