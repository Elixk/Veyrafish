# Veyrafish（微舆）二次开发完整指南

> 版本: v1.2.1 | 许可证: GPL-2.0 | 最后更新: 2026-04-08

本文档面向准备对 Veyrafish 进行二次开发的开发者，从系统架构、技术栈、数据流、扩展点到部署方案进行全面阐述。

---

## 目录

- [1. 系统全景](#1-系统全景)
- [2. 技术栈总览](#2-技术栈总览)
- [3. 项目目录结构详解](#3-项目目录结构详解)
- [4. 配置系统](#4-配置系统)
- [5. 主应用入口 app.py](#5-主应用入口-apppy)
- [6. 五大引擎深度解析](#6-五大引擎深度解析)
  - [6.1 QueryEngine — 国内外新闻搜索 Agent](#61-queryengine--国内外新闻搜索-agent)
  - [6.2 MediaEngine — 多模态内容分析 Agent](#62-mediaengine--多模态内容分析-agent)
  - [6.3 InsightEngine — 私有数据库挖掘 Agent](#63-insightengine--私有数据库挖掘-agent)
  - [6.4 ForumEngine — Agent 论坛协作机制](#64-forumengine--agent-论坛协作机制)
  - [6.5 ReportEngine — 智能报告生成 Agent](#65-reportengine--智能报告生成-agent)
- [7. MindSpider 爬虫系统](#7-mindspider-爬虫系统)
- [8. 情感分析模型集合](#8-情感分析模型集合)
- [9. 数据库设计](#9-数据库设计)
- [10. 报告中间表示（Document IR）](#10-报告中间表示document-ir)
- [11. HTTP API 与 WebSocket 接口参考](#11-http-api-与-websocket-接口参考)
- [12. 前端架构](#12-前端架构)
- [13. 完整数据流](#13-完整数据流)
- [14. 二次开发常见场景](#14-二次开发常见场景)
- [15. Docker 部署与开发](#15-docker-部署与开发)
- [16. 测试](#16-测试)
- [17. 已知约束与注意事项](#17-已知约束与注意事项)

---

## 1. 系统全景

Veyrafish 是一个**多智能体舆情分析系统**，采用纯 Python 模块化架构，核心思路为：

```
用户提问 → Flask 主应用编排 → 3 个分析 Agent 并行工作 → ForumEngine 引导协作
         → ReportEngine 收集结果 → 生成交互式 HTML 报告
```

### 核心 Agent 分工

| Agent | 职责 | 搜索工具 | 推荐 LLM |
|-------|------|----------|-----------|
| **Query Agent** | 国内外新闻广度搜索 | Tavily API | DeepSeek |
| **Media Agent** | 多模态内容深度分析 | Bocha/Anspire API | Gemini 2.5 Pro |
| **Insight Agent** | 私有舆情数据库挖掘 | 本地 DB 查询 | Kimi K2 |
| **Forum Host** | 论坛主持人，协调讨论 | 无 | Qwen Plus |
| **Report Agent** | 多轮报告生成与渲染 | 无 | Gemini 2.5 Pro |

### 协作机制

三个分析 Agent 并行启动后，各自将分析中间结果写入日志文件。ForumEngine 的 `LogMonitor` 实时监控三份日志（`insight.log`、`media.log`、`query.log`），从中提取 `SummaryNode` 的输出写入 `forum.log`。每积累 5 条 Agent 发言，自动触发 LLM 主持人 (`ForumHost`) 生成引导性发言，回写到 `forum.log`。三个 Agent 通过 `utils/forum_reader.py` 读取主持人的最新发言，据此调整后续研究方向。

---

## 2. 技术栈总览

### 后端

| 分类 | 技术 | 说明 |
|------|------|------|
| Web 框架 | Flask 2.3 + Flask-SocketIO | 主应用，SSE 实时推送 |
| 独立 UI | Streamlit 1.28 | 三个 Agent 的独立界面 |
| LLM 调用 | OpenAI Python SDK | 所有 LLM 统一使用 OpenAI 兼容格式 |
| 异步引擎 | SQLAlchemy 2.x + asyncpg/aiomysql | 数据库异步访问 |
| 配置管理 | Pydantic Settings | `.env` 文件驱动，类型安全 |
| 搜索 API | Tavily / Bocha / Anspire | 三种网络搜索供应商 |
| 爬虫 | Playwright + MediaCrawler | 社媒数据采集 |
| ML | PyTorch + Transformers + scikit-learn | 情感分析模型 |
| 日志 | Loguru | 结构化日志 |
| PDF | WeasyPrint | HTML→PDF 导出 |

### 数据库

支持 **PostgreSQL**（推荐）和 **MySQL**，通过 `DB_DIALECT` 环境变量切换。

### 部署

- Docker Compose（PostgreSQL 15 + 应用容器）
- 源码部署（Conda/uv + 手动数据库）

---

## 3. 项目目录结构详解

```
Veyrafish/
├── app.py                        # Flask 主应用入口（进程编排、API 路由、WebSocket）
├── config.py                     # 全局配置（Pydantic Settings，读取 .env）
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python 依赖清单
├── docker-compose.yml            # Docker 多服务编排
├── Dockerfile                    # 镜像构建
│
├── QueryEngine/                  # 🔍 Query Agent
│   ├── agent.py                  #   Agent 主调度类 DeepSearchAgent
│   ├── llms/                     #   LLM 客户端封装（OpenAI 兼容）
│   │   └── base.py
│   ├── nodes/                    #   处理节点管道
│   │   ├── base_node.py          #     节点基类
│   │   ├── first_search_node.py  #     首次搜索查询生成
│   │   ├── reflection_node.py    #     反思搜索查询生成
│   │   ├── first_summary_node.py #     首次总结
│   │   ├── reflection_summary_node.py  # 反思总结
│   │   ├── report_structure_node.py    # 报告结构规划
│   │   └── report_formatting_node.py   # 最终报告格式化
│   ├── tools/                    #   搜索工具集
│   │   └── search.py             #     TavilyNewsAgency（6 种搜索方法）
│   ├── state/                    #   Agent 状态管理
│   │   └── state.py
│   ├── prompts/                  #   提示词模板
│   │   └── prompts.py
│   └── utils/                    #   配置与工具函数
│       └── config.py
│
├── MediaEngine/                  # 📷 Media Agent（结构与 QueryEngine 平行）
│   ├── agent.py                  #   DeepSearchAgent + AnspireSearchAgent
│   ├── tools/
│   │   └── search.py             #   BochaMultimodalSearch / AnspireAISearch
│   └── ...                       #   （同上：llms/nodes/state/prompts/utils）
│
├── InsightEngine/                # 📊 Insight Agent
│   ├── agent.py                  #   DeepSearchAgent（含聚类采样 + 情感分析）
│   ├── tools/
│   │   ├── search.py             #   MediaCrawlerDB（5 种 DB 查询方法）
│   │   ├── keyword_optimizer.py  #   Qwen 关键词优化中间件
│   │   └── sentiment_analyzer.py #   情感分析集成工具
│   ├── utils/
│   │   ├── config.py             #   InsightEngine 专属配置
│   │   └── db.py                 #   SQLAlchemy 异步引擎与只读查询封装
│   └── ...
│
├── ForumEngine/                  # 💬 论坛引擎
│   ├── monitor.py                #   LogMonitor：日志监控 + 发言捕获 + 主持人触发
│   └── llm_host.py               #   ForumHost：LLM 主持人发言生成
│
├── ReportEngine/                 # 📝 Report Agent
│   ├── agent.py                  #   ReportAgent 总调度器
│   ├── flask_interface.py        #   Flask Blueprint（/api/report/*）
│   ├── llms/
│   │   └── base.py               #   统一 LLM 客户端（流式 + 重试）
│   ├── core/
│   │   ├── template_parser.py    #   Markdown 模板切片与 slug 生成
│   │   ├── chapter_storage.py    #   章节 JSON 缓存与 manifest 管理
│   │   └── stitcher.py           #   Document IR 装订器
│   ├── ir/
│   │   ├── schema.py             #   IR JSON Schema 定义（块类型常量）
│   │   └── validator.py          #   章节 JSON 结构校验器
│   ├── nodes/
│   │   ├── template_selection_node.py  # LLM 模板筛选
│   │   ├── document_layout_node.py     # 标题/目录/主题设计
│   │   ├── word_budget_node.py         # 篇幅规划
│   │   └── chapter_generation_node.py  # 章节级 JSON 生成 + 校验
│   ├── renderers/
│   │   ├── html_renderer.py      #   Document IR → 交互式 HTML
│   │   ├── pdf_renderer.py       #   HTML → PDF（WeasyPrint）
│   │   ├── pdf_layout_optimizer.py  # PDF 布局优化
│   │   └── chart_to_svg.py       #   图表转 SVG
│   ├── report_template/          #   Markdown 模板库
│   │   ├── 企业品牌声誉分析报告.md
│   │   └── ...
│   ├── state/
│   │   └── state.py              #   ReportState 与序列化
│   └── utils/
│       ├── config.py             #   ReportEngine 专属配置
│       ├── json_parser.py        #   JSON 解析/修复工具
│       └── chart_validator.py    #   图表数据校验
│
├── MindSpider/                   # 🕷️ 社交媒体爬虫系统
│   ├── main.py                   #   爬虫主入口
│   ├── config.py                 #   爬虫配置
│   ├── BroadTopicExtraction/     #   话题提取模块
│   ├── DeepSentimentCrawling/    #   深度舆情爬取模块
│   │   └── MediaCrawler/         #   Git 子模块：社媒爬虫核心
│   └── schema/                   #   数据库表结构定义
│       ├── mindspider_tables.sql #     DDL 文件
│       ├── init_database.py      #     异步建表脚本
│       ├── models_bigdata.py     #     社媒内容表 ORM
│       └── models_sa.py          #     扩展表 ORM
│
├── SentimentAnalysisModel/       # 🧠 情感分析模型集
│   ├── WeiboSentiment_Finetuned/ #   微调模型（BERT/GPT-2 LoRA）
│   ├── WeiboMultilingualSentiment/  # 多语言情感分析
│   ├── WeiboSentiment_SmallQwen/ #   小参数 Qwen3 微调
│   └── WeiboSentiment_MachineLearning/  # 传统 ML 方法
│
├── SingleEngineApp/              # 🖥️ 单 Agent Streamlit 应用
│   ├── query_engine_streamlit_app.py
│   ├── media_engine_streamlit_app.py
│   └── insight_engine_streamlit_app.py
│
├── utils/                        # 🔧 全局工具函数
│   ├── forum_reader.py           #   Agent 间论坛通信工具
│   ├── github_issues.py          #   Issue 链接生成
│   └── retry_helper.py           #   网络请求重试机制
│
├── templates/index.html          # Flask 主界面（单页 HTML + JS）
├── static/                       # 静态资源
├── logs/                         # 运行日志目录
├── final_reports/                # 最终报告输出
│   ├── ir/                       #   Document IR JSON
│   ├── chapters/                 #   章节 JSON 缓存
│   ├── pdf/                      #   PDF 输出
│   └── md/                       #   Markdown 输出
├── tests/                        # 测试套件
└── *_streamlit_reports/          # 三个 Agent 的 Markdown 中间报告
```

---

## 4. 配置系统

### 4.1 统一配置架构

所有配置统一通过根目录 `.env` 文件管理，由 `config.py` 中的 `Settings(BaseSettings)` 类加载。

```python
# config.py 核心结构
class Settings(BaseSettings):
    # Flask
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # 数据库
    DB_DIALECT: str = "postgresql"  # 或 "mysql"
    DB_HOST: str = "your_db_host"
    DB_PORT: int = 3306
    DB_USER: str = "your_db_user"
    DB_PASSWORD: str = "your_db_password"
    DB_NAME: str = "your_db_name"

    # LLM（每个 Agent 独立配置）
    INSIGHT_ENGINE_API_KEY: Optional[str] = None
    INSIGHT_ENGINE_BASE_URL: Optional[str] = "https://api.moonshot.cn/v1"
    INSIGHT_ENGINE_MODEL_NAME: str = "kimi-k2-0711-preview"
    # ... Media / Query / Report / Forum / Keyword 同理

    # 搜索工具
    SEARCH_TOOL_TYPE: Literal["AnspireAPI", "BochaAPI"] = "AnspireAPI"
    TAVILY_API_KEY: Optional[str] = None
    ANSPIRE_API_KEY: Optional[str] = None
    BOCHA_WEB_SEARCH_API_KEY: Optional[str] = None

    # Insight 搜索参数
    DEFAULT_SEARCH_TOPIC_GLOBALLY_LIMIT_PER_TABLE: int = 50
    DEFAULT_GET_COMMENTS_FOR_TOPIC_LIMIT: int = 500
    MAX_REFLECTIONS: int = 3
    # ...
```

### 4.2 子 Engine 配置继承

每个 Engine 内部也有 `utils/config.py`，定义 Engine 专属的配置（如 `OUTPUT_DIR`、`MAX_REFLECTIONS`、`SEARCH_CONTENT_MAX_LENGTH` 等）。这些 **子配置同样从根 `.env` 读取**，不需要额外配置文件。

### 4.3 运行时热更新

`app.py` 提供 `POST /api/config` 接口，前端可直接修改 `.env` 文件并触发 `reload_settings()` 热加载。

### 4.4 关键配置项速查

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DB_DIALECT` | 数据库类型 | `postgresql` |
| `SEARCH_TOOL_TYPE` | 搜索 API 选择 | `AnspireAPI` |
| `MAX_REFLECTIONS` | Agent 反思循环次数 | `3` |
| `MAX_PARAGRAPHS` | 最大报告段落数 | `6` |
| `DEFAULT_GET_COMMENTS_FOR_TOPIC_LIMIT` | 单话题评论获取上限 | `500` |
| `CHAPTER_JSON_MAX_ATTEMPTS` | 章节 JSON 解析重试次数 | `2`（实际最少 3 次）|

---

## 5. 主应用入口 app.py

`app.py` 是系统的**总编排器**，承担以下职责：

### 5.1 进程管理

- 通过 `subprocess.Popen` 启动三个 Streamlit 子应用（端口 8501/8502/8503）
- 维护全局进程表 `processes`，跟踪每个子应用的 PID、端口、状态
- 提供健康检查（轮询 `/_stcore/health` 端点）
- 支持优雅关机（并发终止 + 强制超时保护）

### 5.2 组件生命周期

```
app.py 启动
  ├── 初始化数据库（MindSpider.initialize_database()）
  ├── 注册 ReportEngine Blueprint
  ├── 初始化 forum.log
  ├── 启动 Forum 日志监听线程
  └── 等待前端 POST /api/system/start 指令
        ├── 启动 Insight Streamlit (8501)
        ├── 启动 Media Streamlit (8502)
        ├── 启动 Query Streamlit (8503)
        ├── 启动 ForumEngine 监控
        └── 初始化 ReportEngine
```

### 5.3 日志架构

每个子应用的 stdout 通过独立线程捕获并写入 `logs/{app_name}.log`，同时通过 Socket.IO `console_output` 事件实时推送到前端。

---

## 6. 五大引擎深度解析

### 6.1 QueryEngine — 国内外新闻搜索 Agent

**职责**：通过 Tavily API 搜索国内外新闻，进行多轮搜索-反思-总结循环。

**核心流程**：

```
research(query)
  ├── Step 1: ReportStructureNode → 规划段落结构
  ├── Step 2: 遍历每个段落
  │     ├── FirstSearchNode → 生成搜索查询 + 选择工具
  │     ├── execute_search_tool() → 调用 Tavily API
  │     ├── FirstSummaryNode → 生成初始总结
  │     └── 反思循环（MAX_REFLECTIONS 次）
  │           ├── ReflectionNode → 生成反思搜索查询
  │           ├── execute_search_tool() → 补充搜索
  │           └── ReflectionSummaryNode → 更新总结
  └── Step 3: ReportFormattingNode → 生成最终 Markdown 报告
```

**搜索工具集**（6 种）：

| 方法 | 功能 |
|------|------|
| `basic_search_news` | 基础新闻搜索（默认） |
| `deep_search_news` | 深度新闻分析 |
| `search_news_last_24_hours` | 24h 内新闻 |
| `search_news_last_week` | 本周新闻 |
| `search_images_for_news` | 新闻图片搜索 |
| `search_news_by_date` | 按日期范围搜索 |

**二开扩展点**：
- 添加新搜索工具：在 `tools/search.py` 中添加方法，在 `agent.py` 的 `execute_search_tool()` 中注册
- 修改搜索策略：编辑 `prompts/prompts.py` 中的提示词，影响 LLM 的工具选择
- 调整反思深度：修改 `MAX_REFLECTIONS` 配置

### 6.2 MediaEngine — 多模态内容分析 Agent

**职责**：通过 Bocha/Anspire 多模态搜索引擎分析视频、图片等内容。

**与 QueryEngine 的区别**：
- 使用 **Bocha/Anspire** 替代 Tavily 作为搜索后端
- 根据 `SEARCH_TOOL_TYPE` 配置自动选择 `DeepSearchAgent` 或 `AnspireSearchAgent`
- 搜索结果包含多模态内容（结构化数据卡片、视觉信息）

**搜索工具集**（5 种）：

| 方法 | 功能 |
|------|------|
| `comprehensive_search` | 全面综合搜索（默认） |
| `web_search_only` | 纯网页搜索 |
| `search_for_structured_data` | 结构化数据查询 |
| `search_last_24_hours` | 24h 内信息 |
| `search_last_week` | 本周信息 |

**二开扩展点**：
- 接入新的多模态搜索引擎：参考 `AnspireSearchAgent` 的实现模式，继承 `DeepSearchAgent` 并覆盖 `execute_search_tool()`
- 在 `create_agent()` 工厂函数中根据配置分发

### 6.3 InsightEngine — 私有数据库挖掘 Agent

**职责**：从本地舆情数据库中挖掘话题、评论、情感数据。

**独特能力**：
1. **关键词优化中间件** (`keyword_optimizer.py`)：用 Qwen 模型将自然语言查询优化为多个数据库搜索关键词
2. **聚类采样** (`_cluster_and_sample_results`)：使用 `paraphrase-multilingual-MiniLM-L12-v2` 对大量结果做 KMeans 聚类，每簇取代表性样本
3. **情感分析集成**：自动对搜索结果执行情感分析（多语言 BERT 模型）

**数据库查询工具集**（6 种）：

| 方法 | 功能 |
|------|------|
| `search_hot_content` | 查找热点内容 |
| `search_topic_globally` | 全局话题搜索 |
| `search_topic_by_date` | 按日期搜索话题 |
| `get_comments_for_topic` | 获取话题评论 |
| `search_topic_on_platform` | 平台定向搜索 |
| `analyze_sentiment` | 独立情感分析 |

**二开扩展点**：
- 接入自定义业务数据库：在 `tools/search.py` 中增加新的查询方法
- 替换情感分析模型：修改 `tools/sentiment_analyzer.py` 中的模型加载逻辑
- 调整聚类参数：修改 `ENABLE_CLUSTERING`、`MAX_CLUSTERED_RESULTS`、`RESULTS_PER_CLUSTER` 常量

### 6.4 ForumEngine — Agent 论坛协作机制

**职责**：实现三个 Agent 之间的异步协作，通过 LLM 主持人引导讨论方向。

**架构**：

```
insight.log ──┐
media.log   ──┼──→ LogMonitor.monitor_logs() ──→ forum.log
query.log   ──┘         │                            ↑
                         │ 每5条Agent发言              │
                         ↓                            │
                  ForumHost.generate_host_speech() ───┘
                         │
                    Agent 通过 forum_reader.py 读取 HOST 发言
```

**核心组件**：

1. **LogMonitor** (`monitor.py`)：
   - 维护各日志文件的读取位置
   - 识别 `SummaryNode` 输出（`FirstSummaryNode` / `ReflectionSummaryNode`）
   - 解析多行 JSON 内容，提取段落总结
   - 过滤 ERROR 块，防止错误信息污染论坛
   - 触发主持人发言

2. **ForumHost** (`llm_host.py`)：
   - 系统提示词定义六项职责：事件梳理、引导讨论、纠正错误、整合观点、趋势预测、推进分析
   - 输出结构化为四部分：事件梳理、观点整合、深层分析、问题引导

**forum.log 格式**：
```
[HH:MM:SS] [SYSTEM] === ForumEngine 系统初始化 ===
[HH:MM:SS] [QUERY] {Agent发言内容}
[HH:MM:SS] [INSIGHT] {Agent发言内容}
[HH:MM:SS] [MEDIA] {Agent发言内容}
[HH:MM:SS] [HOST] {主持人引导发言}
```

**二开扩展点**：
- 修改主持人触发阈值：调整 `host_speech_threshold`（默认 5 条）
- 自定义主持人风格：修改 `_build_system_prompt()` 和 `_build_user_prompt()`
- 添加新的 Agent 参与论坛：在 `monitored_logs` 中添加新的日志文件监控

### 6.5 ReportEngine — 智能报告生成 Agent

**职责**：将三个 Agent 的分析结果 + 论坛日志整合为交互式 HTML 报告。

**完整生成管道**：

```
generate_report(query, reports, forum_logs)
  ├── 1. 归一化三引擎报告
  ├── 2. TemplateSelectionNode → LLM 选择最佳模板
  ├── 3. parse_template_sections() → 将模板切片为章节
  ├── 4. DocumentLayoutNode → 设计标题/目录/配色
  ├── 5. WordBudgetNode → 规划各章字数与重点
  ├── 6. 遍历章节
  │     └── ChapterGenerationNode → LLM 生成章节 JSON（IR 格式）
  │           ├── 校验：IRValidator
  │           ├── 失败重试（最多 3 次 + 跨引擎 LLM 修复）
  │           └── 存盘：ChapterStorage
  ├── 7. DocumentComposer → 装订所有章节为完整 Document IR
  └── 8. HTMLRenderer → 渲染为交互式 HTML
```

**关键设计**：

- **模板系统**：`ReportEngine/report_template/` 目录下的 Markdown 文件作为报告骨架，LLM 自动选择最匹配的模板
- **Document IR**：中间表示层，解耦内容生成与渲染，支持 HTML/PDF/Markdown 多格式输出
- **跨引擎 LLM 修复**：章节 JSON 解析失败时，依次尝试 Report/Forum/Insight/Media 四个 LLM 进行修复
- **内容稀疏兜底**：当章节字数过低时保留最佳候选，插入温馨提示

**Flask Blueprint 路由** (`/api/report/*`)：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/generate` | POST | 启动报告生成任务 |
| `/progress/<task_id>` | GET | 查询任务进度 |
| `/stream/<task_id>` | GET | SSE 流式进度 |
| `/result/<task_id>` | GET | 获取 HTML 结果 |
| `/result/<task_id>/json` | GET | 获取 IR JSON |
| `/download/<task_id>` | GET | 下载报告 |
| `/templates` | GET | 列出可用模板 |
| `/export/pdf/<task_id>` | GET | 导出 PDF |
| `/export/md/<task_id>` | GET | 导出 Markdown |

**二开扩展点**：
- 添加自定义报告模板：在 `report_template/` 目录下创建 Markdown 文件
- 扩展 IR 块类型：在 `ir/schema.py` 中添加新的 block 定义，在 `renderers/html_renderer.py` 中添加渲染逻辑
- 自定义渲染器：参考 `html_renderer.py` 实现新的输出格式
- 调整报告质量：修改 `prompts/prompts.py` 中的章节生成提示词

---

## 7. MindSpider 爬虫系统

### 7.1 架构

MindSpider 分为两个阶段：

1. **BroadTopicExtraction**（话题提取）：
   - 从多平台热榜获取当日新闻
   - 使用 LLM 提取核心话题和关键词
   - 写入 `daily_news`、`daily_topics` 表

2. **DeepSentimentCrawling**（深度爬取）：
   - 基于话题关键词到各社媒平台搜索
   - 使用 MediaCrawler（Git 子模块）执行实际爬取
   - 写入各平台数据表（`xhs_note`、`douyin_aweme`、`weibo_note` 等）

### 7.2 支持的平台

小红书(xhs)、抖音(dy)、快手(ks)、哔哩哔哩(bili)、微博(wb)、贴吧(tieba)、知乎(zhihu)

### 7.3 初始化

```bash
cd MindSpider
python main.py --setup          # 初始化数据库和配置
python main.py --broad-topic    # 获取热点话题
python main.py --complete --date 2024-01-20  # 完整爬取流程
```

> **注意**：完整爬虫功能需要执行 `git submodule update --init` 拉取 MediaCrawler 子模块。

---

## 8. 情感分析模型集合

`SentimentAnalysisModel/` 包含多种情感分析方案，各自独立：

| 方案 | 路径 | 特点 |
|------|------|------|
| BERT 中文 LoRA | `WeiboSentiment_Finetuned/BertChinese-Lora/` | 中文微博数据微调 |
| GPT-2 LoRA | `WeiboSentiment_Finetuned/GPT2-Lora/` | 生成式模型微调 |
| 多语言情感 | `WeiboMultilingualSentiment/` | 支持 22 种语言 |
| Qwen3 小参数 | `WeiboSentiment_SmallQwen/` | 轻量级微调 |
| 传统 ML | `WeiboSentiment_MachineLearning/` | SVM/XGBoost/随机森林 |

**InsightEngine 默认使用**多语言情感分析模型，通过 `tools/sentiment_analyzer.py` 集成。

---

## 9. 数据库设计

### 9.1 MindSpider 扩展表

```sql
-- 每日新闻表
daily_news (id, news_id, source_platform, title, url, description, crawl_date, rank_position, ...)

-- 每日话题表
daily_topics (id, topic_id, topic_name, keywords[JSON], extract_date, relevance_score, processing_status, ...)

-- 话题-新闻关联表
topic_news_relation (id, topic_id, news_id, relation_score, extract_date, ...)

-- 爬取任务表
crawling_tasks (id, task_id, topic_id, platform, search_keywords[JSON], task_status, total_crawled, ...)
```

### 9.2 MediaCrawler 核心表（由子模块创建）

每个平台一张内容表 + 一张评论表：

| 平台 | 内容表 | 评论表 |
|------|--------|--------|
| 小红书 | `xhs_note` | `xhs_note_comment` |
| 抖音 | `douyin_aweme` | `douyin_aweme_comment` |
| 快手 | `kuaishou_video` | `kuaishou_video_comment` |
| B站 | `bilibili_video` | `bilibili_video_comment` |
| 微博 | `weibo_note` | `weibo_note_comment` |
| 贴吧 | `tieba_note` | `tieba_note_comment` |
| 知乎 | `zhihu_content` | `zhihu_content_comment` |

所有内容表已通过 ALTER TABLE 添加 `topic_id` 和 `crawling_task_id` 字段以关联 MindSpider 扩展表。

### 9.3 InsightEngine 数据访问

`InsightEngine/utils/db.py` 提供异步只读查询封装：

```python
from InsightEngine.utils.db import fetch_all

results = await fetch_all(
    "SELECT * FROM xhs_note WHERE title LIKE :keyword LIMIT :limit",
    {"keyword": "%舆情%", "limit": 100}
)
```

底层通过 `DB_DIALECT` 自动切换 `asyncpg`（PostgreSQL）或 `aiomysql`（MySQL）驱动。

---

## 10. 报告中间表示（Document IR）

### 10.1 概述

ReportEngine 使用自定义的 **Document IR** 作为内容与渲染之间的中间层。每份报告先生成 IR JSON，再由渲染器转换为 HTML/PDF/Markdown。

### 10.2 章节 IR 结构

```json
{
  "chapterId": "S1",
  "title": "执行摘要",
  "anchor": "section-1",
  "order": 10,
  "summary": "本章概述...",
  "blocks": [
    { "type": "heading", "level": 2, "text": "...", "anchor": "..." },
    { "type": "paragraph", "inlines": [{ "text": "...", "marks": [] }] },
    { "type": "table", "rows": [...], "caption": "..." },
    { "type": "kpiGrid", "items": [...] },
    { "type": "callout", "tone": "warning", "blocks": [...] },
    { "type": "engineQuote", "engine": "insight", "title": "Insight Agent", "blocks": [...] }
  ]
}
```

### 10.3 支持的块类型

| 类型 | 说明 |
|------|------|
| `heading` | 标题（1-6 级） |
| `paragraph` | 段落（含内联样式：粗体/斜体/链接/代码/颜色等） |
| `list` | 列表（有序/无序/任务） |
| `table` | 表格（支持合并单元格） |
| `swotTable` | SWOT 分析表 |
| `pestTable` | PEST 分析表 |
| `blockquote` | 引用块 |
| `engineQuote` | Agent 引用块（标注来源 Agent） |
| `callout` | 提示框（info/warning/success/danger） |
| `kpiGrid` | KPI 指标网格 |
| `figure` | 图表/图片 |
| `code` | 代码块 |
| `math` | 数学公式（LaTeX） |
| `widget` | 自定义交互组件 |
| `toc` | 目录 |
| `hr` | 分隔线 |

### 10.4 扩展新块类型

1. 在 `ir/schema.py` 中定义新块的 JSON Schema
2. 将其加入 `block_variants` 列表和 `ALLOWED_BLOCK_TYPES`
3. 在 `renderers/html_renderer.py` 中添加渲染方法
4. 在 `nodes/chapter_generation_node.py` 的提示词中告知 LLM 新块类型的用法

---

## 11. HTTP API 与 WebSocket 接口参考

### 11.1 主应用 API（app.py）

| 端点 | 方法 | 功能 |
|------|------|------|
| `GET /` | GET | 主页 |
| `GET /api/status` | GET | 获取所有子应用状态 |
| `GET /api/start/<app_name>` | GET | 启动指定应用 |
| `GET /api/stop/<app_name>` | GET | 停止指定应用 |
| `GET /api/output/<app_name>` | GET | 获取应用日志 |
| `POST /api/search` | POST | 向运行中的 Agent 发送搜索请求 |
| `GET /api/config` | GET | 读取当前配置 |
| `POST /api/config` | POST | 更新配置（写入 .env） |
| `GET /api/system/status` | GET | 系统启动状态 |
| `POST /api/system/start` | POST | 启动完整系统 |
| `POST /api/system/shutdown` | POST | 优雅关机 |
| `GET /api/forum/log` | GET | 获取论坛日志 |
| `GET /api/forum/start` | GET | 启动论坛监控 |
| `GET /api/forum/stop` | GET | 停止论坛监控 |

### 11.2 WebSocket 事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `connect` | 服务器→客户端 | 连接建立 |
| `status_update` | 服务器→客户端 | 各应用状态更新 |
| `console_output` | 服务器→客户端 | 实时日志推送 |
| `forum_message` | 服务器→客户端 | 论坛消息推送 |
| `request_status` | 客户端→服务器 | 请求状态刷新 |

### 11.3 ReportEngine API（/api/report/）

详见 [6.5 节](#65-reportengine--智能报告生成-agent) 的路由表。

---

## 12. 前端架构

前端为**单个 HTML 文件**（`templates/index.html`），约 5900 行，包含完整的 CSS + JavaScript。

### 核心功能模块

1. **系统控制台**：显示子应用状态、启动/停止按钮
2. **配置面板**：动态读取/修改 `.env` 配置
3. **搜索输入**：用户提问入口
4. **Agent 日志查看器**：实时显示各 Agent 的输出
5. **论坛面板**：展示 Agent 间的讨论和主持人发言
6. **报告预览**：SSE 流式展示报告生成进度

### 通信方式

- **Socket.IO**：日志实时推送、状态更新
- **REST API**：配置管理、搜索请求、报告生成
- **SSE**：报告生成流式进度

### 二开扩展点

- 替换为现代前端框架：将 `index.html` 改造为 React/Vue 应用，API 接口保持不变
- 添加新的面板/功能：在 HTML 中新增 tab 页，调用现有或新增的 API

---

## 13. 完整数据流

```
                                    ┌─────────────┐
                                    │  用户提问    │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │  Flask app  │
                                    │  (app.py)   │
                                    └──────┬──────┘
                                           │
                  ┌────────────────────────┼────────────────────────┐
                  │                        │                        │
          ┌───────▼───────┐      ┌─────────▼────────┐    ┌────────▼────────┐
          │ Query Agent   │      │  Media Agent      │    │ Insight Agent   │
          │ (Streamlit    │      │  (Streamlit       │    │ (Streamlit      │
          │  :8503)       │      │   :8502)          │    │  :8501)         │
          └───────┬───────┘      └─────────┬────────┘    └────────┬────────┘
                  │                        │                       │
                  │  搜索 Tavily           │  搜索 Bocha/Anspire   │  查询本地 DB
                  │  + 反思循环            │  + 反思循环            │  + 聚类 + 情感分析
                  │                        │                       │
          ┌───────▼───────┐      ┌─────────▼────────┐    ┌────────▼────────┐
          │ query.log     │      │  media.log        │    │ insight.log     │
          └───────┬───────┘      └─────────┬────────┘    └────────┬────────┘
                  │                        │                       │
                  └────────────────┬───────┘───────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  ForumEngine    │
                          │  (LogMonitor)   │
                          │  ↕ LLM Host    │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  forum.log      │
                          └────────┬────────┘
                                   │
        ┌──────────────────────────▼───────────────────────────┐
        │                   ReportEngine                        │
        │  模板选择 → 布局设计 → 篇幅规划 → 章节生成 → IR装订  │
        └──────────────────────────┬───────────────────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                 │
          ┌───────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
          │  HTML 报告   │ │  PDF 报告   │ │ Markdown 报告│
          └──────────────┘ └─────────────┘ └──────────────┘
```

---

## 14. 二次开发常见场景

### 14.1 更换/添加搜索 API

以添加 Google Custom Search 为例：

1. 在 `QueryEngine/tools/` 下新建 `google_search.py`，实现与 `TavilyNewsAgency` 相同的接口
2. 在 `QueryEngine/agent.py` 的 `__init__` 中根据配置选择搜索引擎
3. 在 `config.py` 中添加 `GOOGLE_SEARCH_API_KEY` 等配置项
4. 在 `.env.example` 中添加对应的环境变量说明

### 14.2 添加新的分析 Agent

1. 以 `QueryEngine/` 为模板复制一份，如 `FinanceEngine/`
2. 实现自己的 `tools/search.py`（例如调用金融 API）
3. 修改 `prompts/prompts.py` 中的提示词以适配金融场景
4. 在 `SingleEngineApp/` 下创建对应的 Streamlit 应用
5. 在 `app.py` 中的 `STREAMLIT_SCRIPTS` 和 `processes` 字典中注册新 Agent
6. 在 `ForumEngine/monitor.py` 的 `monitored_logs` 中添加日志监控

### 14.3 接入自定义业务数据库

1. 在 `InsightEngine/tools/search.py` 中添加新的查询方法
2. 在 `InsightEngine/agent.py` 的 `execute_search_tool()` 中注册新工具
3. 在对应的提示词中告知 LLM 新工具的存在和用法
4. 也可以创建独立的 `custom_db_tool.py`，实现全新的数据访问层

### 14.4 自定义报告模板

1. 在 `ReportEngine/report_template/` 下创建 Markdown 文件
2. 使用 `#`/`##` 标题划分章节（会被 `template_parser.py` 自动解析）
3. Agent 会根据查询内容自动选择最合适的模板
4. 也可通过 API 参数 `custom_template` 指定自定义模板

### 14.5 替换 LLM 模型

所有 LLM 调用统一使用 OpenAI 兼容格式，只需修改 `.env` 中对应 Agent 的三个参数：

```env
# 以 Query Agent 为例
QUERY_ENGINE_API_KEY=your_new_key
QUERY_ENGINE_BASE_URL=https://your-provider.com/v1
QUERY_ENGINE_MODEL_NAME=your-model-name
```

支持的 LLM 供应商包括但不限于：OpenAI、DeepSeek、Moonshot (Kimi)、Google Gemini（通过中转）、Qwen (通义千问)、硅基流动等。

### 14.6 扩展报告渲染格式

当前支持 HTML、PDF、Markdown 三种格式。添加新格式（如 DOCX）：

1. 在 `ReportEngine/renderers/` 下新建渲染器文件
2. 实现 `render(document_ir: Dict) -> bytes/str` 方法
3. 在 `flask_interface.py` 中添加导出 API 端点

---

## 15. Docker 部署与开发

### 15.1 docker-compose.yml 结构

```yaml
services:
  veyrafish:      # 主应用容器
    ports:
      - "5000:5000"     # Flask 主应用
      - "8501:8501"     # Insight Streamlit
      - "8502:8502"     # Media Streamlit
      - "8503:8503"     # Query Streamlit
    volumes:
      - ./.env:/app/.env
      - ./logs:/app/logs
      - ./final_reports:/app/final_reports
      - ./*_streamlit_reports:/app/*_streamlit_reports

  db:             # PostgreSQL 15
    ports:
      - "${POSTGRES_PORT:-5444}:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-veyrafish}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-veyrafish}
      POSTGRES_DB: ${POSTGRES_DB:-veyrafish}
```

### 15.2 开发模式建议

- 使用源码启动（`python app.py`）进行开发，便于热重载和调试
- 数据库使用 Docker 运行的 PostgreSQL，应用本地运行
- 单独调试某个 Agent 时使用 `SingleEngineApp/` 下的 Streamlit 应用
- 仅调试报告生成时使用 `report_engine_only.py` CLI 工具

---

## 16. 测试

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定测试
pytest tests/test_monitor.py -v
pytest tests/test_report_engine_sanitization.py -v
```

测试主要覆盖：
- `ForumEngine` 日志监控与解析
- `ReportEngine` HTML 输出安全性（XSS 防护）

---

## 17. 已知约束与注意事项

### 17.1 技术约束

1. **子模块**：`MindSpider/DeepSentimentCrawling/MediaCrawler` 是 Git 子模块，克隆后需执行 `git submodule update --init`
2. **数据库方言**：`mindspider_tables.sql` 使用 MySQL 语法（`ENGINE=InnoDB`），PostgreSQL 环境需要 `init_database.py` 异步建表
3. **PDF 导出**：依赖 WeasyPrint 及其系统级 GTK/Pango 库，需单独安装
4. **端口占用**：系统同时使用 5000、8501、8502、8503 四个端口，确保无冲突
5. **进程模型**：三个 Streamlit 子应用以子进程方式运行，非线程内

### 17.2 开发建议

1. **LLM 调试**：修改提示词后建议用 `SingleEngineApp` 单独测试效果
2. **报告调试**：使用 `regenerate_latest_html.py` 从缓存的章节 JSON 重新渲染，无需重跑 LLM
3. **日志排查**：每个组件的日志独立存放在 `logs/` 目录，Report Engine 有专属 `report.log`
4. **配置隔离**：每个 Engine 的 `utils/config.py` 支持独立的参数覆盖，但基础配置始终从根 `.env` 继承
5. **数据安全**：InsightEngine 的数据库访问为只读模式（`fetch_all`），写入操作仅通过 MindSpider

### 17.3 性能参考

- 一次完整分析（含三 Agent 并行 + 论坛协作 + 报告生成）通常耗时 5-15 分钟
- 报告生成阶段（仅 ReportEngine）约 2-5 分钟，取决于章节数和 LLM 响应速度
- ForumEngine 无活动 7200 秒（2 小时）后自动结束当前会话

---

## 附录 A：Agent 节点管道统一接口

所有 Agent 的节点均遵循相同的设计模式：

```python
class BaseNode:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def run(self, input_data: dict) -> dict:
        """执行节点逻辑，返回结构化结果"""
        ...

    def mutate_state(self, input_data, state: State, paragraph_index: int) -> State:
        """执行节点逻辑并更新全局状态"""
        ...
```

### 节点类型

| 节点 | 输入 | 输出 |
|------|------|------|
| `ReportStructureNode` | query | paragraphs (标题+内容) |
| `FirstSearchNode` | title, content | search_query, search_tool, reasoning |
| `ReflectionNode` | title, content, latest_summary | search_query, search_tool, reasoning |
| `FirstSummaryNode` | title, content, search_results | paragraph_latest_state |
| `ReflectionSummaryNode` | title, content, search_results, latest_summary | updated_paragraph_latest_state |
| `ReportFormattingNode` | report_data list | formatted_report (Markdown) |

---

## 附录 B：环境变量完整清单

```env
# === Flask 服务器 ===
HOST=0.0.0.0
PORT=5000

# === 数据库 ===
DB_DIALECT=postgresql          # postgresql 或 mysql
DB_HOST=localhost
DB_PORT=5432
DB_USER=veyrafish
DB_PASSWORD=veyrafish
DB_NAME=veyrafish
DB_CHARSET=utf8mb4

# === LLM（6 组，各 3 个参数）===
INSIGHT_ENGINE_API_KEY=
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=kimi-k2-0711-preview

MEDIA_ENGINE_API_KEY=
MEDIA_ENGINE_BASE_URL=https://aihubmix.com/v1
MEDIA_ENGINE_MODEL_NAME=gemini-2.5-pro

QUERY_ENGINE_API_KEY=
QUERY_ENGINE_BASE_URL=https://api.deepseek.com
QUERY_ENGINE_MODEL_NAME=deepseek-chat

REPORT_ENGINE_API_KEY=
REPORT_ENGINE_BASE_URL=https://aihubmix.com/v1
REPORT_ENGINE_MODEL_NAME=gemini-2.5-pro

MINDSPIDER_API_KEY=
MINDSPIDER_BASE_URL=
MINDSPIDER_MODEL_NAME=

FORUM_HOST_API_KEY=
FORUM_HOST_BASE_URL=
FORUM_HOST_MODEL_NAME=

KEYWORD_OPTIMIZER_API_KEY=
KEYWORD_OPTIMIZER_BASE_URL=
KEYWORD_OPTIMIZER_MODEL_NAME=

# === 搜索工具 ===
TAVILY_API_KEY=
SEARCH_TOOL_TYPE=AnspireAPI     # AnspireAPI 或 BochaAPI
ANSPIRE_BASE_URL=https://plugin.anspire.cn/api/ntsearch/search
ANSPIRE_API_KEY=
BOCHA_BASE_URL=https://api.bocha.cn/v1/ai-search
BOCHA_WEB_SEARCH_API_KEY=

# === Docker PostgreSQL ===
POSTGRES_USER=veyrafish
POSTGRES_PASSWORD=veyrafish
POSTGRES_DB=veyrafish
POSTGRES_PORT=5444
```

---

## 附录 C：快速开发工作流

```bash
# 1. 克隆并初始化
git clone https://github.com/666ghj/Veyrafish.git
cd Veyrafish
git submodule update --init      # 拉取 MediaCrawler 子模块

# 2. 创建环境
conda create -n veyrafish python=3.11
conda activate veyrafish
pip install -r requirements.txt
playwright install chromium

# 3. 配置
cp .env.example .env
# 编辑 .env 填入数据库和 API Key

# 4. 启动（完整系统）
python app.py
# 访问 http://localhost:5000

# 5. 单独调试某个 Agent
streamlit run SingleEngineApp/query_engine_streamlit_app.py --server.port 8503

# 6. 仅重新生成报告
python report_engine_only.py --query "你的分析主题"

# 7. 从缓存重新渲染
python regenerate_latest_html.py
python regenerate_latest_pdf.py
```

---

*本文档基于 Veyrafish v1.2.1 源码分析生成，如有源码更新请以实际代码为准。*
