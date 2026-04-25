# Phase 0 实施清单：工程治理与可验证性建设

**状态**：进行中（Round 01 完成依赖/测试/配置治理核心项；跨阶段 Agent Core 已补齐部分数据契约基础）

## 1. 阶段目标

把项目从"能跑但环境脆弱"的状态，升级到"可安装、可配置、可测试、可观测"的基础工程状态。

## 2. 开始条件

- [x] 已确认 Phase 0 是当前优先级最高阶段（2026-04-22 Round 01）
- [x] 暂不启动大规模架构迁移
- [x] 团队接受先做治理、后做大改的节奏

## 3. 本阶段必须完成的任务

### 3.1 依赖治理

- [x] 新建 `pyproject.toml`（2026-04-22 Round 01）
- [x] 将现有 `requirements.txt` 迁移为标准依赖组（在 `pyproject.toml` 的 `[project.optional-dependencies]` 中完成）
- [x] 明确 `core` / `web` / `crawler` / `ml` / `dev` / `report` / `db` 分组
- [x] 补齐 `pytest`、`black`、`flake8`、`mypy` 工具（`dev` 分组）
- [x] 定义本地开发安装命令（`pip install -e ".[dev]"`）
- [ ] 验证干净环境安装成功率（需在新 conda 环境下验证）

### 3.2 配置治理

- [x] 梳理根配置与各 Engine 配置重复字段（`config.py` 已统一用 `pydantic-settings`，无需大改）
- [x] 统一配置模型已实现（`config.py::Settings`，基于 `pydantic-settings`）
- [x] 统一路径、环境变量命名和默认值策略（通过 `Field(default=...)` 统一管理）
- [x] 明确了运行时配置（LLM Key、DB 连接）与部署时配置（HOST、PORT）的边界
- [x] 验证 `.env` 覆盖：`model_validator` 在缺失关键字段时打印警告（2026-04-22 Round 01）
- [ ] 各 Engine 子模块是否有重复配置字段需收敛（待后续 Round 评估）

### 3.3 数据契约治理

- [ ] 抽取 Agent 输入模型（Pydantic Schema）
- [x] 抽取 Agent 输出模型（`veyrafish_core/output_models.py` 已定义 Search/Summary/ReflectionSummary/ReportStructureItem）
- [ ] 抽取 Forum 消息模型
- [ ] 抽取任务状态模型
- [ ] 抽取 Report 输入模型（IR Schema 已有，需评估是否对齐）

### 3.4 测试治理

- [x] 建立单元测试目录约定（`tests/` 已有标准结构）
- [ ] 建立契约测试目录约定（待补充 `tests/contract/`）
- [ ] 建立集成测试样例结构（待补充）
- [x] 补至少一套最小可运行测试基线（`test_monitor.py` 30 项 + `test_report_engine_sanitization.py` 6 项）
- [x] 让 `pytest` 命令能在标准环境中直接执行（2026-04-22 Round 01，`pyproject.toml` 配置完成）
- [x] 确认现有 `tests/` 下的 `test_monitor.py`、`test_report_engine_sanitization.py` 可正常运行（**36/36 通过**）

### 3.5 可观测性基线

- [x] 统一日志格式（全局使用 `loguru`，格式已统一）
- [ ] 统一 trace id / task id / report id（ReportEngine 有 task_id，全链路 trace id 尚未贯通）
- [ ] 为核心路径加结构化日志（当前用 loguru 文本日志，无结构化字段）
- [ ] 接入最小版 OpenTelemetry（评估后暂不引入，性价比低）

## 4. 应交付的结果

- [x] 标准化依赖管理文件（`pyproject.toml`）
- [x] 统一配置设计或实现（`config.py` + 缺失配置警告）
- [ ] 明确的数据模型边界（Agent 输出模型已完成；Agent 输入、Forum 消息、任务状态模型仍待补）
- [x] 可运行的测试基线（36/36 通过）
- [ ] 最小版日志与 trace 基线（loguru 已有，trace id 尚未贯通）

## 5. 完成后的理想结果

- 新开发者能按文档完成安装
- 测试命令可以直接跑起来
- 配置修改不再需要同时改多处
- 关键运行链路可以通过日志和 trace 追踪

## 6. 建议测试

### 安装与环境测试

- [ ] 新环境安装是否成功（`pip install -e ".[dev]"` 后运行 pytest）
- [x] 开发依赖是否安装完整（当前 conda base 环境已安装 loguru + pytest）
- [x] 测试命令是否可执行（`python -m pytest tests/` → 36 passed）

### 配置测试

- [x] 默认配置加载（`from config import settings` 正常）
- [ ] `.env` 覆盖（需补充测试用例，当前仅手工验证）
- [x] 缺失关键配置时的警告提示（`model_validator` 输出警告日志）

### 契约测试

- [ ] Agent 输出结构是否稳定（待补充 `tests/contract/`）
- [ ] Forum 消息结构是否稳定（待补充）
- [ ] Report 输入模型是否可校验（IR Schema 已有，待对齐测试）

### 回归测试

- [x] 现有 `ForumEngine` 解析测试仍可通过（30 passed）
- [x] `ReportEngine` IR 清洗测试仍可通过（6 passed）

## 7. 本阶段重点 bug 检查

- [ ] 安装命令能否在干净环境复现（待新环境验证）
- [x] 配置字段无重名语义冲突（已确认 `pydantic-settings` 统一管理）
- [x] 测试基线不依赖私有路径（`tests/test_monitor.py` 使用相对路径 `tests/test_logs`）
- [ ] 日志与 trace id 尚未贯穿全链路（遗留）

## 8. 完成判定

- [x] 依赖治理完成（`pyproject.toml` 已建立，分组清晰）
- [x] 配置治理完成（缺失配置警告已加，文档已补全）
- [x] 至少一套标准测试入口可用（`python -m pytest tests/` → 36 passed）
- [ ] 可观测性基线可验证（loguru 已有，trace id 未贯通，暂不阻塞）
- [x] 本轮日志已归档（见 `docs/implementation/logs/phase-0/2026-04-22-round-01.md`）

## 9. 已完成轮次日志

| 轮次 | 日期 | 范围 | 日志文件 |
|------|------|------|---------|
| Round 01 | 2026-04-22 | 依赖治理、测试治理、配置治理 | [round-01](./logs/phase-0/2026-04-22-round-01.md) |
| Agent Core | 2026-04-22 | veyrafish_core 基础层、共享 Agent 基类、结构化输出模型 | [agent-core-upgrade](./logs/phase-0/2026-04-22-agent-core-upgrade.md) |

## 10. 本阶段结束后必须写的日志

- Phase 0 阶段总结
- 本轮任务执行日志
- 依赖/配置/测试遗留问题
- 下一轮建议
