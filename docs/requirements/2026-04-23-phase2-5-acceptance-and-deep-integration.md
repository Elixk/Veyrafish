# Phase 2.5 需求文档：验收收口与深度接线

**状态**：已冻结  
**日期**：2026-04-23  
**基于**：`docs/implementation/PHASE_2_IMPLEMENTATION_CHECKLIST.md` + 当前 `veyrafish_core` 实现状态 + `docs/SKILL_DEVELOPMENT_GUIDE.md`

---

## 1. 目标

在 Phase 2 的 Wave 1-5 代码主路径已经补齐的基础上，推进一个 **Phase 2.5 收口阶段**，把系统从“组件存在、单测通过、主路径可跑”升级为“真实链路可验收、Skill 成为默认执行层、Evidence 成为可消费决策层”。

Phase 2.5 不再新增新的基础架构层，而是聚焦以下三件事：

1. **验收收口**：补齐 Docker、真实 LLM、浏览器前端、并发链路的真实联调验收。
2. **深度接线**：让 SkillRegistry / EvidenceStore 从“旁路能力层”变成主研究流程的默认执行底座。
3. **质量闭环**：建立最小可用的评估与回放机制，为后续 Phase 3 升级提供基线。

## 2. 交付物

| 编号 | 交付物 | 说明 |
|------|--------|------|
| D1 | Phase 2.5 验收文档与执行计划 | 明确收口范围、门禁、回滚策略 |
| D2 | Skill 深度硬化 | `query_rewrite` / `gap_finder` / `quality_gate` / `evidence_extract` contract 升级 |
| D3 | BaseResearchAgent 主链路接入 SkillRegistry | 查询改写、总结、证据提取、质量检查进入默认执行路径 |
| D4 | Evidence 深度消费 | ForumEngine / ReportEngine / Reflection 流程消费结构化证据 |
| D5 | 真实链路验收记录 | Docker、真实 LLM、前端浏览器、并发链路的通过记录 |
| D6 | 评估与回放最小闭环 | 固定样例任务、结果回放、质量门禁基线 |

## 3. 约束

- **不重开新 runtime**：Phase 2.5 是 Phase 2 的收口和加固，不引入新的调度框架或并行控制面。
- **不推倒主流程**：继续沿用 `veyrafish_core`、`BaseResearchAgent`、`SkillRegistry`、`EvidenceStore`，只做深接线与 contract 升级。
- **保持向后兼容**：现有 API 入口、研究调用方式、前端日志展示能力不能退化。
- **优先真实可交付**：验收结论以真实 Docker/LLM/浏览器链路为准，不以“文件存在”和“局部测试通过”替代。
- **Phase 3 前置基线**：Phase 2.5 必须产出可复用的评估基线，作为后续 Phase 3 质量比较依据。

## 4. 验收标准

### 4.1 技术验收

- [ ] `BaseResearchAgent` 的关键节点默认通过 `SkillRegistry` 执行，而不是仅保留独立 helper 逻辑
- [ ] `EvidenceExtractSkill` 深度接入 evidence sink，不再仅依赖启发式按句切分
- [ ] `QueryRewriteSkill` 支持更明确的工具选择规则、日期/平台约束与稳定降级路径
- [ ] `GapFinderSkill` 能区分 coverage gap / conflict gap / recency gap
- [ ] `QualityGateSkill` 按 `content_type` 使用差异化标准，而不是仅靠长度与重复度
- [ ] `ReportEngine` 可消费 `EvidenceStore` 的结构化结果生成章节上下文
- [ ] `ForumEngine` 可消费 evidence / gap 分析结果辅助主持人判断
- [ ] 存在最小可用的评估与回放命令，能对固定任务给出结构化验收结果
- [ ] `pytest tests/` 全量通过，且新增 Phase 2.5 测试不引入回归

### 4.2 产品验收

- [ ] Docker 容器内 `/api/system/start` 正常工作
- [ ] 浏览器前端能看到三引擎进度与 forum 日志，不因深接线而退化
- [ ] 真实 LLM 配置下三引擎并发任务可完成一次完整研究
- [ ] `/api/evidence/<task_id>` 返回结果可被前端或调试链路有效消费
- [ ] 报告质量不低于当前 Phase 2 主路径，且关键引用/冲突呈现更稳定

## 5. 问题定义

### 5.1 当前已完成但未闭环的部分

- Phase 2 的 Graph / Skill / Evidence / Event Bus 代码主路径已补齐。
- `tests/test_skill.py`、`tests/test_graph_integration.py`、`tests/test_evidence_store.py` 等已覆盖第一轮门禁。
- `PHASE_2_IMPLEMENTATION_CHECKLIST.md` 已明确指出剩余项主要集中在真实验收与深度集成，而不是缺少新模块。

### 5.2 当前核心缺口

1. **Skill 仍偏能力层**：已可独立执行，但尚未成为各研究节点的默认执行底座。
2. **Evidence 仍偏存储层**：已可沉淀与查询，但对 Report / Forum / Reflection 的驱动还不够强。
3. **验收仍偏开发态**：真实 Docker、真实 LLM、真实浏览器链路未完成正式收口。
4. **缺少质量基线**：缺乏固定任务回放与评分，难以证明“深接线后更好”。

## 6. Phase 2.5 范围

### 6.1 Skill 深度硬化

优先硬化以下 Skill：

| Skill | 当前状态 | Phase 2.5 目标 |
|------|---------|----------------|
| `query_rewrite` | 已可改写查询并选工具 | 增加工具选择规则、日期/平台约束、稳定降级输出 |
| `gap_finder` | 已可发现缺口 | 明确 gap 类型，提升跨引擎冲突识别 |
| `quality_gate` | 已有基础规则检查 | 按 `content_type` 分层标准，形成可追踪 issue 输出 |
| `evidence_extract` | 已支持结构化证据提取 | 强化 claim/source 对齐、来源绑定、缺口分类 |

### 6.2 BaseResearchAgent 深接线

目标是让以下环节优先经由 registry 执行：

- 搜索前：`query_rewrite`
- 总结阶段：`llm_summarize`
- 证据沉淀：`evidence_extract`
- 输出前检查：`quality_gate`

这一步完成后，Skill 不再只是“可调用能力”，而成为主链路默认机制。

### 6.3 Evidence 深度消费

EvidenceStore 的角色从“沉淀仓库”升级为“决策输入”：

- ForumEngine 使用 `gap_finder` + evidence aggregate 做主持人判断
- ReportEngine 将结构化 evidence 注入章节生成上下文
- Reflection 流程根据冲突/缺口决定是否继续补搜或修订结论

### 6.4 评估与回放

建立最小闭环，不追求完整评测平台，但必须具备：

- 固定任务样例集
- 可重放命令
- 结构化输出保存
- 基础评分维度

推荐的首批评分维度：

- 结构完整性
- 关键结论覆盖率
- 冲突保留与不确定性表达
- 证据引用稳定性
- 输出质量门禁通过率

## 7. 非目标

- 不引入 LangGraph / MCP / 新消息队列
- 不做大规模 UI 重构
- 不重写 ReportEngine IR / renderer 主架构
- 不做分布式部署或多机编排
- 不在 Phase 2.5 内解决所有长期评估平台能力

## 8. 推断假设

- 当前 `BaseResearchAgent` 已具备足够的节点封装能力，可以逐步切换到 registry 驱动而不必重写节点层
- 当前 `EvidenceStore` 的聚合能力足以支撑第一轮 Report / Forum 深接线
- 当前真实链路风险主要来自配置、集成边界和回退路径，而非基础模型本身完全不可用
- Phase 2.5 若没有评估基线，Phase 3 将缺少可量化的质量对比依据

## 9. 完成定义

只有同时满足以下条件，才允许声明“Phase 2.5 完成”：

1. 代码层：Skill 深硬化 + 主流程深接线 + Evidence 深消费均已落地。
2. 测试层：单元测试、集成测试、回放测试通过，且无已知高风险回归。
3. 产品层：Docker、真实 LLM、浏览器前端链路通过正式验收。
4. 文档层：执行计划、验收记录、评估基线与未完成项都已同步。
