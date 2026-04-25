# Phase 2 实施清单：Agent Runtime 升级（二阶段架构升级）

**状态**：进行中（已完成试点 Round 01-02；二阶段升级 5 波主路径已补齐第一轮；Phase 2.5 已冻结并进入 Wave 1：Skill contract 硬化）

> 验收校准：本清单不再把“文件存在/单元测试通过”等同于“主流程完成”。Wave 3/4/5 已完成主路径接线修复，但 Docker、真实 LLM、前端实机链路仍需单独验收。

> Phase 2.5 入口：`docs/requirements/2026-04-23-phase2-5-acceptance-and-deep-integration.md`  
> Phase 2.5 计划：`docs/plans/2026-04-23-phase2-5-acceptance-and-deep-integration-execution-plan.md`

## 1. 阶段目标

把当前隐式的 Agent 节点循环和论坛协作逻辑，升级为 **显式状态图 + Skill 注册表 + 事件驱动协作 + 共享证据层**。

核心原则：
- 零新框架依赖（StateGraph / Skill / EvidenceStore 全部自研，放在 `veyrafish_core` 内）
- 增量演进（每波独立可验证、可回滚）
- 向后兼容（`research(query)` 不传 task_id 时行为不变）

## 2. 开始条件

- [x] Phase 1 已完成（核心层 + Round 02 收尾）
- [x] 任务状态层稳定（task_store.py 测试通过）
- [x] API 与 Worker 边界清晰（Flask + Thread 模型）
- [x] veyrafish_core 基础层已建立（BaseResearchAgent + LLMClient + BaseNode + output_models）
- [x] InsightEngine 试点完成（节点事件 + 断点恢复）
- [x] 二阶段升级需求文档已冻结

## 3. 已完成的试点工作（Round 01-02）

### 3.1 单 Engine 图谱化试点（InsightEngine）

- [x] InsightEngine 节点级进度事件写入 `task_events` 表
- [x] 断点恢复：`research_with_resume()` 从已完成段落续跑
- [x] MediaEngine 节点事件推广
- [x] ForumEngine 进度事件推广（`bind_task` + `_emit`）

## 4. 二阶段架构升级：5 波计划

> 需求文档：`docs/requirements/2026-04-23-phase2-architecture-upgrade.md`
> 执行计划：`docs/plans/2026-04-23-phase2-architecture-upgrade-execution-plan.md`

### Wave 1：自研状态图引擎
- [x] `StateGraph` 类（add_node / add_edge / conditional_edge / validate）
- [x] `GraphRunner` 类（run / resume / 自动 task_events / checkpoint）
- [x] `GraphState` 基类（序列化/反序列化）
- [x] 单元测试（图构建、线性执行、条件分支、异常恢复）
- 详细规划：[WAVE_1_STATE_GRAPH.md](./phase-2-waves/WAVE_1_STATE_GRAPH.md)

### Wave 2：Skill 基类 + SkillRegistry + 核心 Skill
- [x] `Skill` ABC + `SkillContext` + `SkillBudget`
- [x] `SkillRegistry`（register / get / list / execute / 按 tag 查询）
- [x] 提取 5-8 个核心 Skill（WebSearch / QueryRewrite / LLMSummarize / EvidenceExtract / Sentiment / GapFinder / QualityGate）
- [x] Skill 开发指南文档
- [x] 单元测试
- [x] Skill 深度质量验收第一轮（Summary / EvidenceExtract 已补 schema 约束、证据来源、无 LLM 降级路径）
- [ ] 继续硬化剩余 Skill（QueryRewrite / GapFinder / QualityGate 等仍可进一步细化 contract）
- 详细规划：[WAVE_2_SKILL_REGISTRY.md](./phase-2-waves/WAVE_2_SKILL_REGISTRY.md)

### Wave 3：三引擎图谱化迁移
- [x] BaseResearchAgent `_build_graph()` 方法
- [x] `research()` 通过 `GraphRunner.run()` 执行，并复用 `_build_graph()` 主路径
- [x] `research_with_resume()` 通过 `GraphRunner.resume()` 执行（当前恢复依据仍是 paragraph_done 事件，不是完整 Agent State checkpoint）
- [x] 三引擎子类无需修改（已继承 BaseResearchAgent）
- [x] 端到端集成测试（mock LLM）（`tests/test_graph_integration.py` 14 passed）
- 详细规划：[WAVE_3_ENGINE_MIGRATION.md](./phase-2-waves/WAVE_3_ENGINE_MIGRATION.md)

### Wave 4：ForumEngine 事件驱动 + 三引擎并发
- [x] ForumEngine `poll_events()` 从 task_events 读取结构化事件
- [x] 主持人触发条件改为 `paragraph_done` 事件数
- [x] 三引擎并发调度（ThreadPoolExecutor，库层 `ResearchDispatcher` 已实现）
- [x] 保留 forum.log 作为 UI 兼容层
- [x] `/api/search` 主入口接入并发 HTTP 转发，并过滤 forum 非搜索子应用
- 详细规划：[WAVE_4_EVENT_DRIVEN_CONCURRENT.md](./phase-2-waves/WAVE_4_EVENT_DRIVEN_CONCURRENT.md)

### Wave 5：共享证据层
- [x] `evidence` 表 + `Evidence` Pydantic 模型
- [x] `EvidenceStore` 类（add / query / aggregate）
- [x] BaseResearchAgent 自动沉淀证据（真实三引擎默认开启；当前为轻量启发式切句）
- [x] `/api/evidence/<task_id>` 暴露证据查询与聚合摘要
- [x] ReportEngine 可选读取证据（`evidence_task_ids` 可进入 generation_context / manifest）
- [ ] EvidenceExtractSkill 与 BaseResearchAgent evidence sink 的深度集成仍可继续升级
- 详细规划：[WAVE_5_EVIDENCE_STORE.md](./phase-2-waves/WAVE_5_EVIDENCE_STORE.md)

## 5. 应交付的结果

- [x] InsightEngine 节点事件 + 断点恢复（试点完成）
- [x] `veyrafish_core/graph.py`（StateGraph + GraphRunner）
- [x] `veyrafish_core/skill.py` + `veyrafish_core/skills/`
- [x] 三引擎图谱化迁移
- [x] ForumEngine 事件驱动
- [x] 三引擎并发调度
- [x] 共享证据层
- [x] 测试 + 文档清单同步

## 6. 完成判定

- [x] 试点阶段完成（Round 01-02）
- [x] Wave 1-5 代码门禁通过第一轮
- [x] `pytest tests/` 全量通过（含新增测试）
- [ ] Docker 容器内 `/api/system/start` 正常工作
- [ ] 真实 LLM + 浏览器前端 + Docker 联调验收

## 6.5 Phase 2.5 收口状态

- [x] Phase 2.5 需求文档已冻结
- [x] Phase 2.5 执行计划已冻结
- [x] Wave 1：Skill contract 硬化
- [x] Wave 2：BaseResearchAgent 主链路深接线
- [ ] Wave 3：Evidence 深消费与产品联调
- [ ] Wave 4：评估、回放与正式验收

当前说明：
- Phase 2 主路径代码层已基本补齐，但不能直接等同于阶段彻底完成。
- Phase 2.5 用于承接真实验收、Skill 深度硬化、Evidence 深消费与最小评估闭环。
- Phase 2.5 Wave 1 已完成：`tests/test_skill.py` 与全量 `pytest tests/` 门禁通过（见 Round 04）。
- Phase 2.5 Wave 2 已完成：主链路默认接入 `query_rewrite` / `llm_summarize` / `quality_gate` / `evidence_extract`，并通过 `tests/test_graph_integration.py` 与全量回归。
- Phase 2.5 Wave 3 已完成代码与测试侧深接线（Reflection + Forum + Report evidence context），但 Docker / 浏览器联调门禁尚未通过，暂不勾选完成。
- Phase 2.5 Wave 4 已完成最小评估闭环（固定样例、回放脚本、评分维度、离线回放产物）；真实 LLM + Docker 正式验收仍受环境阻塞，暂不勾选完成。
- 在 Phase 2.5 Wave 4 未通过前，系统状态应表述为“代码主路径完成，正式验收未完成”。

## 7. 已完成轮次日志

| 轮次 | 日期 | 范围 | 日志文件 |
|------|------|------|---------|
| Round 01 | 2026-04-22 | task_events 表 + InsightEngine 节点事件 + 断点恢复 | [round-01](./logs/phase-2/2026-04-22-round-01.md) |
| Round 02 | 2026-04-22 | MediaEngine 节点事件 + Forum 进度事件推广 | [round-02](./logs/phase-2/2026-04-22-round-02.md) |
| Round 03 | 2026-04-24 | Phase 2.5 Wave 3 首轮：反思 gap/evidence 决策信号 + Forum 事件摘要消费 | [round-03](./logs/phase-2/2026-04-24-round-03.md) |
| Round 04 | 2026-04-24 | Phase 2.5 Wave 4：固定样例回放与评分闭环 + 全量回归 + 正式验收阻塞记录 | [round-04](./logs/phase-2/2026-04-24-round-04.md) |
