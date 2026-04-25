# Veyrafish 总实施清单

> 本文档是升级实施总入口。先看这里，再进入每个阶段的独立清单。

## 0. 当前进度总览

| 阶段 | 状态 | 已完成轮次 | 备注 |
|------|------|-----------|------|
| Phase 0 | **进行中** | 1 + Core | Round 01 完成依赖/配置/测试治理；跨阶段 Agent Core 完成 veyrafish_core 基础层 + Agent 基类 + 结构化输出 |
| Phase 1 | **完成（核心）** | 2 | Round 02 收尾：zombie 清理 + 25 个单元测试，pytest 61/61 通过 |
| Phase 2 | **进行中（二阶段升级）** | 2 + 5W | 已完成：节点事件试点 + 断点恢复。5 波架构升级已有库层实现，但 Wave 3/4/5 产品接线仍需校准 |
| Phase 3 | **进行中** | 5 | 前端规划 → 首页重构 → SVG 图标 → 系统菜单/SVG 资产 → 多页拆分 |

> **说明**：Phase 3（前端/产品化）已经先于 Phase 0-2 启动。这是因为项目参加设计竞赛，前端视觉改造有时间压力，所以先做可见产出。Phase 0-2 的工程治理、运行架构、Agent runtime 升级后续再补。
>
> **验收校准（2026-04-23）**：本文档区分“核心完成”“库层完成”“产品路径已接线”。未实机验证或未接入主流程的事项不得写成完整完成。

## 1. 实施原则

- 不做大爆炸重构，按阶段推进
- 每个阶段结束后必须能独立验证
- 每个阶段结束后必须写阶段日志和本轮任务日志
- 没有通过阶段门禁，不进入下一阶段
- 优先收敛工程边界，再升级运行时，再升级 Agent runtime，最后做产品化

## 2. 阶段划分

### Phase 0：工程治理与可验证性建设

目标：

- 让项目进入"可安装、可配置、可测试、可追踪"的状态

对应文档：

- [PHASE_0_IMPLEMENTATION_CHECKLIST.md](./PHASE_0_IMPLEMENTATION_CHECKLIST.md)

### Phase 1：运行架构升级

目标：

- 把当前 `Flask + Streamlit 子进程 + 文件总线` 升级为 `API + Worker + 任务状态层`

对应文档：

- [PHASE_1_IMPLEMENTATION_CHECKLIST.md](./PHASE_1_IMPLEMENTATION_CHECKLIST.md)

### Phase 2：Agent runtime 升级（二阶段架构升级）

目标：

- 把隐式 Agent 循环升级为显式状态图和可恢复运行时
- 新增自研状态图引擎（StateGraph + GraphRunner）
- 建立 Skill 注册表，从现有引擎提取 5-8 个共享 Skill
- ForumEngine 从日志监听升级为事件驱动
- 三引擎并发调度 + 共享证据层

对应文档：

- [PHASE_2_IMPLEMENTATION_CHECKLIST.md](./PHASE_2_IMPLEMENTATION_CHECKLIST.md)
- [需求文档](../requirements/2026-04-23-phase2-architecture-upgrade.md)
- [执行计划](../plans/2026-04-23-phase2-architecture-upgrade-execution-plan.md)

Wave 详细规划：

- [Wave 1：自研状态图引擎](./phase-2-waves/WAVE_1_STATE_GRAPH.md)
- [Wave 2：Skill 基类 + Registry](./phase-2-waves/WAVE_2_SKILL_REGISTRY.md)
- [Wave 3：三引擎图谱化迁移](./phase-2-waves/WAVE_3_ENGINE_MIGRATION.md)
- [Wave 4：ForumEngine 事件驱动 + 并发](./phase-2-waves/WAVE_4_EVENT_DRIVEN_CONCURRENT.md)
- [Wave 5：共享证据层](./phase-2-waves/WAVE_5_EVIDENCE_STORE.md)

### Phase 3：产品化与平台化增强

目标：

- 在稳定工程基础上，补前端、插件化、评估与平台能力

对应文档：

- [PHASE_3_IMPLEMENTATION_CHECKLIST.md](./PHASE_3_IMPLEMENTATION_CHECKLIST.md)

前端专项子文档：

- [前端功能清单](./frontend/FRONTEND_FUNCTION_INVENTORY.md)
- [前端页面信息架构](./frontend/FRONTEND_PAGE_ARCHITECTURE.md)
- [前端重构总规划](./frontend/FRONTEND_RESTRUCTURE_PLAN.md)

## 3. 跨阶段共通要求

### 3.1 开始前检查

- 当前阶段是否有明确范围
- 当前阶段是否有明确负责人
- 当前阶段是否有可验收的输出物
- 当前阶段是否定义了测试方式
- 当前阶段是否定义了回滚方式

### 3.2 完成后必须输出的内容

- 代码或文档产物
- 阶段结果总结
- 测试结果
- bug 风险与遗留问题
- 本轮任务日志

### 3.3 阶段门禁

进入下一个阶段前，必须满足：

- 当前阶段关键清单已完成
- 当前阶段关键测试已通过
- 当前阶段重大阻塞 bug 已清零或明确降级处理
- 当前阶段日志已归档

## 4. 建议实施顺序

1. 完成 Phase 0
2. 只在 Phase 0 通过后进入 Phase 1
3. 只在 Phase 1 任务状态层稳定后进入 Phase 2
4. 只在 Phase 2 图谱化运行稳定后进入 Phase 3

> 注：当前因竞赛时间压力，Phase 3 前端部分已先行启动。

## 5. 阶段总览表

| 阶段 | 重点 | 核心产出 | 核心测试 | 进入下一阶段的条件 |
|------|------|----------|----------|--------------------|
| Phase 0 | 工程治理 | 依赖治理、配置治理、测试基线、日志与 trace 基线 | 安装、配置、单元/契约测试基线 | 项目进入可开发可测试状态 |
| Phase 1 | 运行架构 | FastAPI API 层、Worker 层、任务状态层 | API、任务流、事件流、回归 | 文件总线不再是主通道 |
| Phase 2 | Agent runtime（二阶段升级） | 自研 StateGraph + Skill Registry + 图谱化迁移 + 事件驱动协作 + 共享证据层 | 图执行、Skill CRUD、迁移回归、并发调度、证据查询 | 引擎执行可视可控 + Skill 可复用 + 协作不依赖日志 |
| Phase 3 | 产品平台 | API-first 前端、插件化、评估与回放 | 前后端集成、插件装载、评估回归 | 项目具备持续产品化基础 |

## 6. 每轮任务日志要求

每一轮任务结束后，必须记录：

- 本轮任务编号
- 所属阶段
- 目标
- 实际完成项
- 未完成项
- 测试结果
- 新发现 bug / 已修复 bug / 遗留风险
- 下一轮建议

统一模板见：

- [ROUND_LOG_TEMPLATE.md](./templates/ROUND_LOG_TEMPLATE.md)

统一规范见：

- [ROUND_LOGGING_GUIDE.md](./ROUND_LOGGING_GUIDE.md)
