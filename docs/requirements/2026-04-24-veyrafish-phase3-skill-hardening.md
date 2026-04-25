# Phase 3 Skill 专项需求文档：Skill Hardening 与资产化

**状态**：已冻结  
**日期**：2026-04-24  
**运行模式**：`$vibe` interactive_governed  
**基于**：Phase 3 总规划、`docs/SKILL_DEVELOPMENT_GUIDE.md`、`veyrafish_core/skills/` 当前实现、`docs/二阶段升级/reference/skill参考与选择/Vibe-Skills-3.0.0`

---

## 1. Goal

本轮目标不是简单“新增更多 skill”，而是把 Veyrafish 当前已有的 7 个内部业务 skill 从“可运行的 Python 能力模块”提升到“有明确分层、有可追踪 contract、有验收标准的 skill 资产”。

本轮优先完成三件事：

1. 明确当前 7 个 skill 的定位分层：核心、增强、适配层。
2. 为核心 skill 冻结详细 spec，使其不再只存在于代码注释和 prompt 字符串里。
3. 按规划开始落地第一批资产化成果，并为后续主链路增强和前端展示留出稳定接口。

## 2. Deliverables

| 编号 | 交付物 | 说明 |
|------|--------|------|
| D1 | Skill 专项需求文档与执行计划 | 冻结本轮范围、优先级、门禁和回滚策略 |
| D2 | `docs/skills/README.md` | skill 分层状态总览与演进规则 |
| D3 | 核心 skill 详细 spec | 首批包含 `query_rewrite`、`llm_summarize`、`evidence_extract`、`quality_gate` |
| D4 | 代码与文档对齐改造第一批 | 根据 spec 对代码、测试或接线做最小必要修正 |
| D5 | Skill 验证记录 | 测试命令、手动检查项、残余风险说明 |

## 3. Constraints

- 不把项目内部 skill 误改造成外部 `SKILL.md` 路由系统；Veyrafish 当前 skill 仍以 Python 模块为主。
- 参考 `Vibe-Skills-3.0.0` 的优质写法，但不引入其完整路由/准入体系。
- 只把最关键的 skill 先做完整资产化，不追求七个一次性全部补齐。
- skill spec 必须能映射回现有代码、schema、fallback 和测试，不能写成空泛说明文。
- 本轮如需改代码，优先做“增强可解释性、稳固 contract、补测试”的改动，不重开大架构。

## 4. Acceptance Criteria

### 4.1 文档层

- 存在一个 Skill 总览文档，说明 7 个 skill 的当前状态和优先级。
- 核心 4 个 skill 都有详细 spec，包含目标、适用场景、输入、输出、决策规则、禁止事项、失败降级、验证方式。
- 文档内容与当前代码实现大体一致，若不一致，计划中必须明确列出待对齐项。

### 4.2 代码层

- 核心 skill 的实现与 spec 不出现明显冲突。
- 至少一批核心 skill 的输出字段可被主链路、调试链路或日志稳定消费。
- 新增或调整的字段、规则、fallback 有测试覆盖。

### 4.3 产品层

- 后续前端展示或调试时，能用文档明确解释每个核心 skill 在系统中的作用。
- 演示或答辩时，能讲清楚 skill 的价值，而不只是说“这里调了一个 LLM prompt”。

## 5. Product Acceptance Criteria

- 核心 skill 的职责边界足够清楚，适合对外讲解。
- 失败时的降级路径可解释，不会让系统因为一个 skill 失效而整体不可用。
- 至少一个调试或展示场景能体现 skill 输出的结构化价值。

## 6. Manual Spot Checks

- 随机检查一个核心 skill，能在文档中找到其完整 contract。
- 随机检查一个输出字段，能从 spec 追溯到 `_models.py` 和实现文件。
- 检查一个 fallback 路径，确认不是“失败即空字符串”这种不可解释行为。
- 检查 `web_search`，确认其被归类为适配层而不是强行包装成知识型 skill。

## 7. Completion Language Policy

- 只完成文档，不改实现：`Skill 资产文档已冻结，代码对齐待完成`
- 完成文档并完成首批代码对齐：`Skill 第一批硬化已完成`
- 若仅核心 4 个完成：`核心 skill 已资产化，增强与适配层待后续处理`
- 未完成真实测试前，不表述为：`skill 体系已完成`

## 8. Delivery Truth Contract

本轮完成声明必须基于：

- `veyrafish_core/skills/` 当前真实代码
- `veyrafish_core/skills/_models.py` 的 schema
- `tests/test_skill.py` 与相关集成测试
- `docs/skills/` 新增资产文档
- 参考技能库中的优秀结构，而不是抽象印象

## 9. Non-goals

- 不把 7 个 skill 全部补成外部 `SKILL.md` 格式
- 不引入复杂 skill 路由、manifest、自动发现系统
- 不在本轮完成前端可视化展示全部 skill 输出
- 不把 `web_search` 强行包装成完整知识 skill

## 10. Autonomy Mode

本轮采用 `L` 级串行推进：

1. 先冻结规划
2. 再产出 skill 文档资产
3. 再根据文档修正最关键的代码和测试
4. 最后验证并记录残余风险

## 11. Inferred Assumptions

- 当前 7 个 skill 里，真正值得先补全的是核心 4 个：`query_rewrite`、`llm_summarize`、`evidence_extract`、`quality_gate`
- `gap_finder` 和 `sentiment_analysis` 更适合作为增强型能力，在第二批处理
- `web_search` 更像稳定适配层，不适合投入同等规格的 spec 打磨
- 先把 skill 文档化，会让后续前端展示、Docker 验收和答辩表达都更顺
