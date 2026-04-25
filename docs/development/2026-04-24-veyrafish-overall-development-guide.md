# Veyrafish 整体项目开发指南

**文档版本**：2026-04-24  
**适用项目**：维舆 / Veyrafish  
**文档定位**：面向开发者的实际开发手册  
**相关文档**：

- 根目录开发说明：`DEVELOPMENT.md`
- 整体设计文档：`docs/design/2026-04-24-veyrafish-overall-project-design.md`
- 当前进展设计：`docs/design/2026-04-24-veyrafish-current-project-design.md`
- 总实施清单：`docs/implementation/MASTER_IMPLEMENTATION_CHECKLIST.md`
- Skill 文档：`docs/skills/README.md`

> 本文档回答“怎么开发、怎么调试、怎么扩展、怎么验证”。如果要了解系统为什么这样设计，请先看整体设计文档；如果要了解模块细节，请看 `DEVELOPMENT.md` 和 `MODULE_ANALYSIS.md`。

## 1. 当前开发状态

当前项目处在“代码主路径已大量补齐，正式验收仍在收口”的阶段。

开发时必须牢记：

- Flask + Streamlit 子进程仍是当前主运行模式。
- `task_store.py` 已提供任务状态层，但文件总线仍存在。
- `veyrafish_core` 已提供 Graph、Skill、Evidence 等新架构能力。
- 前端已拆成六页，但旧脚本兼容逻辑仍不少。
- Docker、浏览器实机、真实 LLM 端到端仍未完成正式验收。

因此，任何开发完成声明都要基于证据，不能只因为文件存在就宣称链路完成。

## 2. 快速开始

### 2.1 推荐开发顺序

1. 安装 Python 3.11 环境。
2. 安装项目依赖。
3. 配置 `.env`。
4. 运行单元测试。
5. 启动主应用。
6. 单独调试 Agent 或 ReportEngine。
7. 修改代码后按影响范围运行测试。

### 2.2 最小命令

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/
python app.py
```

访问：

```text
http://localhost:5000
```

说明：

- 如果只改文档，不需要启动服务。
- 如果只改 ReportEngine 渲染，优先用重渲染脚本，不要每次重跑三引擎。
- 如果只改某个 Agent，优先单独启动对应 Streamlit 应用。

## 3. 环境和依赖

### 3.1 Python 版本

推荐：

```text
Python 3.11
```

项目声明支持 Python 3.9+，但当前开发和缓存文件显示主要运行在 Python 3.12/3.11 环境附近。为了减少依赖兼容问题，建议新环境使用 Python 3.11。

### 3.2 依赖文件

| 文件 | 用途 |
|---|---|
| `requirements.txt` | 当前传统安装入口 |
| `pyproject.toml` | 新依赖治理入口，已定义 optional dependency groups |
| `MindSpider/requirements.txt` | 爬虫子系统依赖 |

### 3.3 依赖分组

`pyproject.toml` 中已按用途分组：

| 分组 | 用途 |
|---|---|
| core | Flask、配置、LLM、SQLAlchemy、HTTP、JSON 修复 |
| web | Streamlit、FastAPI、uvicorn |
| db | MySQL/PostgreSQL/SQLite/Redis 等驱动 |
| crawler | Playwright、爬虫解析、图像处理 |
| ml | torch、transformers、sentence-transformers、sklearn |
| report | weasyprint、plotly、matplotlib、wordcloud |
| dev | pytest、black、flake8、mypy 等开发工具 |
| full | 除重型 ml/crawler 外的常用完整集合 |

可选安装方式：

```powershell
python -m pip install -e ".[dev]"
python -m pip install -e ".[web,db,report,dev]"
```

注意：

- 干净环境安装成功率仍需单独验证。
- PDF 导出依赖 WeasyPrint 系统库，Windows 下可能需要额外安装 GTK/Pango。
- 爬虫依赖 Playwright 浏览器驱动，需要执行 `playwright install chromium`。

## 4. 配置策略

### 4.1 配置入口

主配置入口：

```text
config.py
.env
.env.example
```

`config.py` 使用 Pydantic Settings。前端配置弹窗通过 `/api/config` 读取和写入 `.env`，随后调用 `reload_settings()` 热加载。

### 4.2 必配项

开发时至少要关注：

| 配置 | 说明 |
|---|---|
| `DB_DIALECT` | `postgresql` 或 `mysql` |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | 数据库连接 |
| `INSIGHT_ENGINE_API_KEY` | Insight LLM |
| `MEDIA_ENGINE_API_KEY` | Media LLM |
| `QUERY_ENGINE_API_KEY` | Query LLM |
| `REPORT_ENGINE_API_KEY` | Report LLM |
| `FORUM_HOST_API_KEY` | Forum 主持人 LLM |
| `TAVILY_API_KEY` | QueryEngine 搜索 |
| `SEARCH_TOOL_TYPE` | `AnspireAPI` 或 `BochaAPI` |
| `ANSPIRE_API_KEY` / `BOCHA_WEB_SEARCH_API_KEY` | MediaEngine 搜索 |

### 4.3 开发配置建议

- 本地开发先复制 `.env.example` 为 `.env`。
- 不要把真实 API Key 写入文档或提交。
- 只调前端时可以不填完整 LLM Key。
- 只跑单元测试时通常不需要真实 LLM Key。
- 真实端到端演示前必须检查每个 Agent 的 Key、Base URL、Model Name。

### 4.4 新增配置项步骤

1. 在 `config.py::Settings` 中新增字段，使用 `Field(default=..., description=...)`。
2. 在 `.env.example` 中补说明。
3. 如果前端需要可编辑，在 `app.py` 的 `CONFIG_KEYS` 加入字段。
4. 如果子 Engine 有局部配置，也要检查对应 `utils/config.py` 是否需要读取。
5. 补配置加载测试或至少手工验证 `/api/config`。

## 5. 启动和调试

### 5.1 启动完整系统

```powershell
python app.py
```

访问：

```text
http://localhost:5000
```

完整系统涉及端口：

| 组件 | 端口 |
|---|---|
| Flask | 5000 |
| Insight Streamlit | 8501 |
| Media Streamlit | 8502 |
| Query Streamlit | 8503 |

### 5.2 单独启动 Agent

```powershell
streamlit run SingleEngineApp/insight_engine_streamlit_app.py --server.port 8501
streamlit run SingleEngineApp/media_engine_streamlit_app.py --server.port 8502
streamlit run SingleEngineApp/query_engine_streamlit_app.py --server.port 8503
```

适用场景：

- 只调某个 Agent 的 prompt。
- 只调搜索工具。
- 只看单引擎报告输出。
- 排查某个 API Key 或搜索 provider 问题。

### 5.3 调试 ReportEngine

无需重跑三引擎时：

```powershell
python report_engine_only.py --query "测试主题"
```

使用缓存章节重渲染：

```powershell
python regenerate_latest_html.py
python regenerate_latest_md.py
python regenerate_latest_pdf.py
```

适用场景：

- 调 HTML Renderer。
- 调 Document IR。
- 调 PDF/Markdown 导出。
- 调报告模板。

### 5.4 调试 MindSpider

```powershell
cd MindSpider
python main.py --setup
python main.py --broad-topic
python main.py --complete --date 2024-01-20
```

注意：

- 完整爬虫可能依赖 MediaCrawler 子模块。
- 需要遵守目标平台规则和合规要求。
- 开发 InsightEngine 查询时，先确认数据库表和样例数据存在。

## 6. 目录责任

| 路径 | 责任 |
|---|---|
| `app.py` | Flask 编排、路由、子进程、配置、Socket.IO |
| `config.py` | 全局配置 |
| `task_store.py` | SQLite 任务、事件、证据表 |
| `veyrafish_core/` | Agent Runtime、Graph、Skill、Evidence、Dispatcher |
| `QueryEngine/` | 新闻/网页广度搜索 Agent |
| `MediaEngine/` | 多模态搜索 Agent |
| `InsightEngine/` | 本地舆情数据库 Agent |
| `ForumEngine/` | Agent 论坛协作 |
| `ReportEngine/` | 报告生成、IR、渲染、导出 |
| `MindSpider/` | 数据采集和数据库 schema |
| `SentimentAnalysisModel/` | 情感分析模型集合 |
| `SingleEngineApp/` | 三个 Streamlit 子应用 |
| `templates/` | Flask 前端模板 |
| `static/` | 静态 CSS/JS/图片资源 |
| `logs/` | 运行日志、SQLite 任务库 |
| `final_reports/` | 最终报告产物 |
| `tests/` | 单元、集成、回归测试 |
| `docs/implementation/` | 阶段实施清单和轮次日志 |
| `docs/skills/` | 内部 Skill spec |
| `docs/design/` | 设计文档 |
| `docs/development/` | 开发文档 |

## 7. 开发流程

### 7.1 标准工作流

1. 明确任务属于哪一层：前端、Web 编排、Agent、Skill、Report、爬虫、测试、文档。
2. 阅读对应模块已有实现。
3. 检查是否会改变接口契约。
4. 小步修改。
5. 运行对应测试。
6. 如涉及运行链路，做手工验证。
7. 更新文档或实施日志。

### 7.2 修改边界原则

- 改前端模板时，不随意删除旧 DOM id。
- 改 `app.py` 路由时，不破坏旧 API。
- 改三引擎时，优先复用 `BaseResearchAgent` 和已有节点接口。
- 改 Skill 时，同步更新 schema、spec 和测试。
- 改 Report IR 时，同步 schema、validator、renderer、测试和示例。
- 改数据库 schema 时，同步 MindSpider ORM、DDL、Insight SQL。

### 7.3 何时必须补测试

以下改动必须补或运行相关测试：

- `task_store.py`
- `veyrafish_core/graph.py`
- `veyrafish_core/skills/`
- `veyrafish_core/evidence_store.py`
- `ForumEngine/monitor.py`
- `ReportEngine/ir/`
- `ReportEngine/renderers/`
- `InsightEngine/tools/search.py`
- 修改日志协议或输出目录协议

## 8. 常见开发任务 Recipes

### 8.1 新增搜索工具

适用：接入新的 Web 搜索、多模态搜索或行业 API。

步骤：

1. 在对应 Engine 的 `tools/` 下新增工具类。
2. 返回结构要能被 Agent 节点和 summary 节点消费。
3. 在 `agent.py` 的工具分发逻辑中注册。
4. 修改 prompt 中的工具描述。
5. 在 `config.py` 和 `.env.example` 增加 API Key。
6. 单独启动对应 Streamlit App 测试。

验证：

```powershell
streamlit run SingleEngineApp/query_engine_streamlit_app.py --server.port 8503
```

或：

```powershell
streamlit run SingleEngineApp/media_engine_streamlit_app.py --server.port 8502
```

### 8.2 新增 Agent

步骤：

1. 以 `QueryEngine/` 为模板新建 Engine 目录。
2. 尽量继承 `veyrafish_core.base_research_agent.BaseResearchAgent`。
3. 实现对应工具、prompt、state 和节点。
4. 新增 `SingleEngineApp/<new>_streamlit_app.py`。
5. 在 `app.py` 中注册 `STREAMLIT_SCRIPTS` 和 `processes`。
6. 为新 Agent 分配端口。
7. 如果参与 Forum，更新 Forum 监控配置。
8. 如果参与 Report，更新 Report 输入归一化逻辑。

风险：

- 日志协议不兼容会导致 Forum 无法识别。
- 报告输出目录不符合约定会导致 ReportEngine 读不到。

### 8.3 新增 Skill

步骤：

1. 在 `veyrafish_core/skills/_models.py` 定义输入输出模型。
2. 在 `veyrafish_core/skills/` 新增实现文件。
3. 继承 `Skill`，实现 `run()`。
4. 在 `veyrafish_core/skills/__init__.py` 或 registry 初始化处注册。
5. 在 `docs/skills/` 写 spec。
6. 在 `tests/test_skill.py` 添加测试。
7. 若接入主链路，在 `BaseResearchAgent` 中调用 `_execute_skill()`。

必须说明：

- 适用场景。
- 输入输出。
- 决策规则。
- 禁止事项。
- fallback。
- 测试方式。

### 8.4 新增 Report IR 块类型

步骤：

1. 修改 `ReportEngine/ir/schema.py`。
2. 修改 `ReportEngine/ir/validator.py`。
3. 修改 `ReportEngine/renderers/html_renderer.py`。
4. 如需导出 PDF/MD，同步修改对应 renderer。
5. 修改章节生成 prompt，让 LLM 知道新块。
6. 在 `ReportEngine/scripts/generate_all_blocks_demo.py` 加示例。
7. 添加或更新测试。

验证：

```powershell
python ReportEngine/scripts/generate_all_blocks_demo.py
python ReportEngine/scripts/validate_ir.py <ir_json_path>
python regenerate_latest_html.py
```

### 8.5 新增前端页面

步骤：

1. 在 `templates/` 新增页面模板。
2. 复用 `static/engine-shared.css` 和 `static/engine-shared.js`。
3. 在 `app.py` 添加 Flask 路由。
4. 更新首页或导航入口。
5. 保留必要的状态显示和错误态。
6. 手工浏览器检查。

注意：

- 不要把新页面做成纯展示页，必须保留真实操作入口或真实状态。
- 不要破坏系统菜单和配置弹窗。
- 不要让装饰图遮挡日志、按钮和 iframe。

### 8.6 修改数据库 Schema

步骤：

1. 修改 `MindSpider/schema/models_sa.py` 或 `models_bigdata.py`。
2. 修改 `MindSpider/schema/mindspider_tables.sql`。
3. 修改 `MindSpider/schema/init_database.py`。
4. 修改 `InsightEngine/tools/search.py` 中相关 SQL 和映射。
5. 准备迁移或重建策略。
6. 用测试数据库验证。

风险：

- InsightEngine 中表名和字段名有硬编码。
- MySQL/PostgreSQL 方言差异需要检查。

### 8.7 修改配置弹窗字段

步骤：

1. 改 `config.py`。
2. 改 `.env.example`。
3. 改 `app.py::CONFIG_KEYS`。
4. 前端打开配置弹窗，确认字段可读写。
5. 保存后检查 `.env`。

## 9. 测试策略

### 9.1 全量测试

```powershell
python -m pytest tests/
```

### 9.2 重点测试文件

| 文件 | 覆盖 |
|---|---|
| `tests/test_task_store.py` | 任务状态层 |
| `tests/test_graph.py` | StateGraph / GraphRunner |
| `tests/test_graph_integration.py` | BaseResearchAgent 图集成 |
| `tests/test_skill.py` | Skill Registry 和核心 Skill |
| `tests/test_evidence_store.py` | EvidenceStore |
| `tests/test_forum_events.py` | Forum 事件驱动 |
| `tests/test_monitor.py` | Forum 日志解析 |
| `tests/test_output_models.py` | 输出模型 |
| `tests/test_replay_eval.py` | 回放评估 |
| `tests/test_report_engine_sanitization.py` | ReportEngine HTML/IR 安全清洗 |

### 9.3 按改动选择测试

| 改动范围 | 建议测试 |
|---|---|
| TaskStore | `python -m pytest tests/test_task_store.py` |
| Graph | `python -m pytest tests/test_graph.py tests/test_graph_integration.py` |
| Skill | `python -m pytest tests/test_skill.py` |
| Evidence | `python -m pytest tests/test_evidence_store.py` |
| Forum | `python -m pytest tests/test_monitor.py tests/test_forum_events.py` |
| Report 安全/IR | `python -m pytest tests/test_report_engine_sanitization.py` |
| 回放 | `python -m pytest tests/test_replay_eval.py` |
| 多模块改动 | `python -m pytest tests/` |

### 9.4 手工验收

手工验收必须覆盖：

- `/` 首页打开。
- 配置弹窗打开、读取、保存。
- `/api/system/start` 返回 task_id。
- 三个 Streamlit 子应用状态。
- `/forum` 可显示消息。
- `/report` 可创建报告任务。
- 报告可预览和导出。

当前注意：

- 浏览器实机验收仍是待完成项。
- Docker 正式验收仍是待完成项。
- 真实 LLM live replay 仍是待完成项。

## 10. 日志和排障

### 10.1 日志文件

| 文件 | 用途 |
|---|---|
| `logs/insight.log` | InsightEngine 日志 |
| `logs/media.log` | MediaEngine 日志 |
| `logs/query.log` | QueryEngine 日志 |
| `logs/forum.log` | Forum 协作日志 |
| `logs/report.log` | ReportEngine 日志 |
| `logs/tasks.db` | SQLite 任务、事件、证据 |

### 10.2 常见问题

#### 端口占用

症状：

- 子应用启动失败。
- 8501/8502/8503 已被占用。

处理：

- 查找占用端口进程。
- 停止残留 Streamlit 进程。
- 再通过前端或 `app.py` 启动。

#### API Key 缺失

症状：

- Streamlit 页面提示缺少 API Key。
- 搜索或 LLM 调用失败。

处理：

- 检查 `.env`。
- 打开前端配置弹窗。
- 检查对应 `*_API_KEY`、`*_BASE_URL`、`*_MODEL_NAME`。

#### ReportEngine 找不到输入

症状：

- 报告生成提示输入文件未准备就绪。

处理：

- 检查三个 `*_streamlit_reports/` 目录是否有 `.md`。
- 检查文件修改时间。
- 需要快速调试时使用 `report_engine_only.py`。

#### Forum 没有主持人发言

可能原因：

- 三引擎日志没有 SummaryNode 输出。
- `forum.log` 未初始化。
- ForumEngine 未启动。
- 事件驱动模式未绑定 task_id。

排查：

- 看 `/api/forum/log`。
- 看 `logs/forum.log`。
- 看 `ForumEngine/monitor.py` 中触发阈值。

#### Insight 数据库查询为空

可能原因：

- 数据库未初始化。
- MindSpider 未采集数据。
- 表名或字段与 SQL 不一致。
- DB 方言配置不对。

排查：

- 检查 `.env` 的 DB 配置。
- 检查 `MindSpider/schema`。
- 检查 `InsightEngine/tools/search.py` 的表名。

### 10.3 任务状态排障

`logs/tasks.db` 包含：

- `tasks`
- `task_events`
- `evidence`

常见用途：

- 查系统启动任务是否失败。
- 查 Agent 段落事件。
- 查 Evidence 是否写入。

建议后续增加一个开发调试脚本，用于打印指定 task_id 的任务、事件和证据。

## 11. Docker 调试

### 11.1 当前状态

项目已有：

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.local.yml`

但 Docker 正式验收未完成。开发文档只能把 Docker 作为调试路径，不能声明“已可部署”。

### 11.2 建议调试顺序

1. 检查 Docker daemon 是否可用。
2. 检查 `.env` 是否完整。
3. 构建镜像。
4. 启动数据库容器。
5. 启动应用容器。
6. 检查 5000、8501、8502、8503 端口。
7. 打开首页。
8. 执行 `/api/system/start`。
9. 生成或读取报告。

### 11.3 必查项

- `.env` 是否挂载。
- `logs/` 是否挂载。
- `final_reports/` 是否挂载。
- 数据库服务名是否与 `DB_HOST` 一致。
- WeasyPrint 系统依赖是否满足。
- Playwright 浏览器是否安装。

## 12. 前端开发注意事项

### 12.1 当前结构

当前有六个页面：

- `templates/index.html`
- `templates/insight.html`
- `templates/media.html`
- `templates/query.html`
- `templates/forum.html`
- `templates/report.html`

共享层：

- `static/engine-shared.css`
- `static/engine-shared.js`
- `static/veyu-ui.css`

### 12.2 修改原则

- 保留真实功能入口。
- 保留旧 JS 依赖的 DOM id。
- 页面装饰不能遮挡交互。
- 按页面职责拆，不把所有逻辑重新塞回首页。
- 不引入前端构建链，除非另开专项。

### 12.3 验收点

- 首页品牌、输入区、五引擎入口正常。
- 系统菜单可展开和关闭。
- 配置弹窗可打开。
- 各内页导航可返回。
- iframe 占位和运行态正常。
- Forum 消息不重叠。
- Report 预览和导出按钮可见。

## 13. ReportEngine 开发注意事项

### 13.1 不要绕过 IR

ReportEngine 的核心是 Document IR。新增能力应优先进入：

- schema
- validator
- renderer
- prompt
- demo
- tests

不要直接在 HTML Renderer 里拼特殊私有结构，否则 PDF/Markdown 和后续校验会断。

### 13.2 调试建议

- 模板选择问题：看 `ReportEngine/report_template/` 和 `template_selection_node.py`。
- 章节 JSON 问题：看 `chapter_generation_node.py` 和 `ir/validator.py`。
- HTML 问题：看 `renderers/html_renderer.py`。
- PDF 问题：看 `renderers/pdf_renderer.py` 和系统依赖。
- 图表问题：看 chart validator / repair / review service。

## 14. Skill 开发注意事项

### 14.1 当前 Skill 类型

核心：

- `query_rewrite`
- `llm_summarize`
- `evidence_extract`
- `quality_gate`

增强：

- `gap_finder`
- `sentiment_analysis`

适配：

- `web_search`

### 14.2 开发要求

每个 Skill 必须有：

- 输入模型。
- 输出模型。
- 明确 fallback。
- 可解释错误。
- 测试。
- 文档 spec。

### 14.3 不要做的事

- 不要让 Skill 直接依赖前端。
- 不要让 Skill 静默吞掉关键错误。
- 不要返回无法被 Pydantic 校验的散文结果。
- 不要把 provider 适配逻辑和业务判断强耦合。

## 15. Agent Runtime 开发注意事项

### 15.1 Graph

改 `StateGraph` 或 `GraphRunner` 时，要特别注意：

- 节点执行顺序。
- 条件边。
- resume 行为。
- task_events 重复写入。
- 异常恢复。

测试：

```powershell
python -m pytest tests/test_graph.py tests/test_graph_integration.py
```

### 15.2 BaseResearchAgent

改 `BaseResearchAgent` 时，要考虑三引擎都会受影响。

必须检查：

- QueryEngine 是否仍可运行。
- MediaEngine 是否仍可运行。
- InsightEngine 是否仍可运行。
- Skill fallback 是否稳定。
- Evidence sink 是否写入正确。
- ReportFormattingNode 是否仍输出 Markdown。

## 16. 提交和交付检查清单

### 16.1 代码改动前

- 明确改动模块。
- 阅读对应文档和测试。
- 确认是否改变外部接口。
- 确认是否涉及配置、数据库、报告 IR 或日志协议。

### 16.2 代码改动后

- 运行相关单测。
- 多模块改动运行全量测试。
- 如涉及前端，浏览器打开相关页面。
- 如涉及报告，生成或重渲染报告。
- 如涉及配置，检查 `.env.example`。
- 如涉及 Skill，更新 `docs/skills/`。
- 如涉及阶段目标，更新 `docs/implementation/` 日志。

### 16.3 最小交付证据

至少写清：

- 改了哪些文件。
- 做了哪些验证。
- 哪些验证没做。
- 是否影响旧路由。
- 是否影响 Docker。
- 是否影响真实 LLM 运行。

## 17. 当前限制和后续建议

### 17.1 当前限制

- 文件协议仍未完全降级。
- 全链路 trace id 未贯通。
- Docker 正式验收未完成。
- 浏览器/移动端验收未完成。
- 真实 LLM live replay 未通过。
- 前端部分区域仍是演示态数据。
- `templates/index.html` 仍很大，后续维护成本高。

### 17.2 后续建议

优先级从高到低：

1. 跑通 Docker + 浏览器 + 真实 LLM 最小演示。
2. 建立 task_id 全链路贯通。
3. ReportEngine 优先消费 task/evidence，而不是只扫目录。
4. ForumEngine 优先消费 task_events。
5. 建立前端真实任务列表和 Evidence 面板。
6. 给 Skill 建示例集和回放样例。
7. 拆分前端大文件，沉淀页面组件规范。
8. 再考虑 FastAPI / Worker / 插件化。

## 18. 开发者一句话原则

开发 Veyrafish 时，不要只追求“功能看起来跑了”。每个新增能力都要回答四个问题：

1. 它的数据从哪里来？
2. 它的结果写到哪里？
3. 它失败时怎么降级？
4. 它如何被测试或回放证明？

