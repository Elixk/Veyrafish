# Veyrafish 整体项目开发文档需求冻结

**状态**：已冻结  
**日期**：2026-04-24  
**运行模式**：`$vibe` interactive_governed  
**主题**：编写面向开发者的整体项目开发文档。

## 1. Goal

在已有 `DEVELOPMENT.md` 和整体设计文档基础上，新增一份更偏实际开发操作的项目级开发文档，覆盖环境搭建、启动调试、目录责任、开发流程、模块扩展、测试门禁、日志排障、Docker 调试和提交前检查。

## 2. Deliverable

- `docs/development/2026-04-24-veyrafish-overall-development-guide.md`

## 3. Constraints

- 不替代 `DEVELOPMENT.md`，而是补充“怎么开发、怎么改、怎么验证”。
- 必须基于当前真实仓库结构和已有测试入口。
- 必须区分当前可执行命令、建议命令、待验收命令。
- 不修改业务代码。
- 不声称 Docker / 浏览器 / 真实 LLM 验收已完成。

## 4. Acceptance Criteria

- 包含开发环境准备。
- 包含源码启动、单引擎启动、报告调试、Docker 调试路径。
- 包含配置说明和 `.env` 开发策略。
- 包含目录责任和修改边界。
- 包含常见开发任务 recipes：新增搜索工具、新 Agent、新 Skill、新 Report 块、新前端页、新配置项。
- 包含测试与验收命令。
- 包含日志、任务状态和 Evidence 排障方法。
- 包含提交/交付前检查清单。

## 5. Non-goals

- 不写用户操作手册。
- 不写最终部署运维手册。
- 不运行真实端到端任务。
- 不新增测试或代码。

## 6. Delivery Truth Contract

事实来源：

- `DEVELOPMENT.md`
- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `tests/`
- `docs/implementation/`
- `docs/skills/`
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
- `SingleEngineApp/`
- `templates/`
- `static/`

