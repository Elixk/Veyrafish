# Veyrafish 整体项目设计文档需求冻结

**状态**：已冻结  
**日期**：2026-04-24  
**运行模式**：`$vibe` interactive_governed  
**主题**：编写覆盖 Veyrafish 整体项目的系统设计文档。

## 1. Goal

形成一份从产品目标、需求范围、系统架构、模块设计、数据设计、Agent 流程、前端设计、部署、测试、安全和演进路线全覆盖的整体项目设计文档。

该文档不是“当前修改总结”，而是项目级概要设计 + 详细设计，能直接服务竞赛答辩、技术说明、后续开发交接和部署调试。

## 2. Deliverable

- `docs/design/2026-04-24-veyrafish-overall-project-design.md`

## 3. Constraints

- 保持事实边界：已实现、部分实现、规划能力必须分开写。
- 当前目录不是 Git 工作树，不能使用 git diff 作为事实来源。
- 不能把 Docker、浏览器实机、真实 LLM 验收写成已完成。
- 不修改业务代码。
- 文档语言以中文为主，面向评委、开发者和答辩场景。

## 4. Acceptance Criteria

- 包含项目背景、目标用户、应用场景和功能需求。
- 包含非功能需求：性能、可靠性、可扩展性、安全、可观测性。
- 包含总体架构、部署架构、运行架构和模块拓扑。
- 覆盖所有主要模块：Web 编排、配置、任务状态、三分析引擎、Forum、Report、MindSpider、Sentiment、Core Runtime、Skill、Evidence、前端。
- 包含关键数据设计：业务数据库、SQLite 任务库、文件产物、Document IR、Forum 协议。
- 包含端到端流程：启动、采集、分析、协作、报告生成、导出、回放。
- 包含 API 概览、测试策略、部署方案、风险与后续路线。

## 5. Non-goals

- 不写用户操作手册的逐步截图版。
- 不写 Docker 最终部署手册。
- 不替代源码注释和 API 文档。
- 不运行真实端到端任务。

## 6. Delivery Truth Contract

事实来源包括：

- `README.md`
- `DEVELOPMENT.md`
- `MODULE_ANALYSIS.md`
- `UPGRADE_DIRECTIONS.md`
- `docs/implementation/*`
- `docs/requirements/*`
- `docs/plans/*`
- `docs/skills/*`
- `app.py`
- `config.py`
- `task_store.py`
- `veyrafish_core/`
- `QueryEngine/`
- `MediaEngine/`
- `InsightEngine/`
- `ForumEngine/`
- `ReportEngine/`
- `MindSpider/`
- `SentimentAnalysisModel/`
- `SingleEngineApp/`
- `templates/`
- `static/`

