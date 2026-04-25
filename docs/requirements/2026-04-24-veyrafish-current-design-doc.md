# 当前项目设计文档需求冻结

**状态**：已冻结  
**日期**：2026-04-24  
**运行模式**：`$vibe` interactive_governed  
**主题**：根据当前项目修改和进展，形成一份可用于答辩、交接、后续开发的详细设计文档。

## 1. Goal

编写一份基于当前仓库真实状态的设计文档，覆盖 Veyrafish 当前的系统架构、阶段进展、模块职责、运行链路、数据契约、前端设计、Skill/Evidence 资产化、验收状态、风险和后续路线。

文档必须反映当前修改后的项目，而不是只复述原始 README。

## 2. Deliverable

- 新增详细设计文档：`docs/design/2026-04-24-veyrafish-current-project-design.md`
- 文档需要能支持：
  - 比赛设计说明
  - 技术答辩
  - 后续 Phase 2.5 / Phase 3 收口
  - Docker 调试前的系统边界确认

## 3. Constraints

- 当前目录不是 Git 工作树，不能依赖 `git diff` 判断修改范围。
- 以已有文档、文件时间、源码、模板和实施日志为事实来源。
- 必须区分“已完成”“代码主路径完成但正式验收未完成”“规划中”。
- 不改业务代码，只新增文档和 `$vibe` 运行收据。
- 不声称 Docker、浏览器实机、真实 LLM 联调已经完成。

## 4. Acceptance Criteria

- 文档包含当前阶段进度账本。
- 文档包含系统总体架构和运行流程。
- 文档覆盖 `app.py`、`task_store.py`、`veyrafish_core/`、三引擎、ForumEngine、ReportEngine、前端模板、Skill、Evidence。
- 文档说明当前 UI 水墨多页重构状态。
- 文档列出关键 API、数据表、事件、证据和报告 IR 契约。
- 文档给出验证状态、残余风险和下一步路线。

## 5. Non-goals

- 不生成最终操作手册、部署手册或用户手册。
- 不运行完整真实分析任务。
- 不重构代码。
- 不把规划中的 FastAPI/Celery/LangGraph 等路线写成当前已完成架构。

## 6. Delivery Truth Contract

本次文档以以下证据为准：

- `README.md`
- `DEVELOPMENT.md`
- `MODULE_ANALYSIS.md`
- `UPGRADE_DIRECTIONS.md`
- `docs/implementation/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/implementation/PHASE_*.md`
- `docs/requirements/*.md`
- `docs/plans/*.md`
- `docs/skills/*.md`
- `app.py`
- `task_store.py`
- `veyrafish_core/`
- `templates/`
- `static/`

