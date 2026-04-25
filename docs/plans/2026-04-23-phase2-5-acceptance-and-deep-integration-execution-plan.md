# Phase 2.5 执行计划：验收收口与深度接线

**需求文档**：`docs/requirements/2026-04-23-phase2-5-acceptance-and-deep-integration.md`  
**内部执行等级**：L（串行收口，按风险逐波推进）  
**日期**：2026-04-23

---

## 执行策略

Phase 2.5 不再按“发明新基础设施”的方式推进，而是按 **4 波（Wave）串行收口**：

1. **Wave 1：Skill contract 硬化**
2. **Wave 2：BaseResearchAgent 主链路深接线**
3. **Wave 3：Evidence 深消费与产品联调**
4. **Wave 4：评估、回放与正式验收**

每波结束后都必须通过对应门禁，未通过不得宣布阶段完成。

---

## Wave 1：Skill Contract 硬化

**目标**：把现有 Skill 从“基础可用”提升到“可作为默认主链路依赖”。

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W1.1 | 补齐 `QueryRewriteSkill` 的工具选择规则、日期/平台约束与 fallback contract | `veyrafish_core/skills/query_rewrite.py` |
| W1.2 | 扩展 `GapFinderSkill`，区分 coverage / conflict / recency gap | `veyrafish_core/skills/gap_finder.py` |
| W1.3 | 将 `QualityGateSkill` 从通用长度检查升级为按 `content_type` 的标准集 | `veyrafish_core/skills/quality_gate.py` |
| W1.4 | 强化 `EvidenceExtractSkill` 的 claim/source 对齐、来源绑定与缺口分类 | `veyrafish_core/skills/evidence_extract.py` |
| W1.5 | 按升级后的 contract 同步 `veyrafish_core/skills/_models.py` | `veyrafish_core/skills/_models.py` |
| W1.6 | 补充/更新 Skill 单测 | `tests/test_skill.py` |
| W1.7 | 更新 Skill 开发指南中的当前优先级与 contract 规范 | `docs/SKILL_DEVELOPMENT_GUIDE.md` |

### 验证门禁

```bash
pytest tests/test_skill.py -v
pytest tests/test_output_models.py -v
pytest tests/ -q
```

### 完成判定

- Skill 输出 schema 与行为 contract 已与文档一致
- 无 LLM / 外部服务时的降级路径仍可稳定执行
- 新增字段可被现有主链路安全消费

### 回滚方式

- 保留旧字段兼容一轮
- 单个 Skill 的升级可独立回退，不影响 registry 基础设施

---

## Wave 2：BaseResearchAgent 主链路深接线

**目标**：让 SkillRegistry 成为研究主流程默认执行层，而不是旁路能力集。

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W2.1 | 梳理 BaseResearchAgent 各节点的 Skill 接入点与默认回退策略 | `veyrafish_core/base_research_agent.py` |
| W2.2 | 搜索前接入 `query_rewrite` | `veyrafish_core/base_research_agent.py` |
| W2.3 | 总结阶段优先接入 `llm_summarize` | `veyrafish_core/base_research_agent.py` |
| W2.4 | 证据沉淀优先接入 `evidence_extract`，启发式切句退为 fallback | `veyrafish_core/base_research_agent.py` |
| W2.5 | 输出前接入 `quality_gate` 形成统一质量门禁 | `veyrafish_core/base_research_agent.py` |
| W2.6 | 统一构造 `SkillContext`，把 `task_id` / `llm_client` / `config` / `evidence_store` 注入主链路 | `veyrafish_core/base_research_agent.py` |
| W2.7 | 增补主链路集成测试（mock LLM） | `tests/test_graph_integration.py` / 新增测试文件 |

### 验证门禁

```bash
pytest tests/test_graph_integration.py -v
pytest tests/test_skill.py -v
pytest tests/ -q
```

### 关键设计决策

- SkillRegistry 是默认路径，但必须保留失败时的本地 fallback
- 不要求所有节点都“只”通过 Skill 实现，重点是关键研究链路默认经由 Skill
- 子引擎仍尽量保持薄壳，不重新复制接线逻辑

### 回滚方式

- 以 helper 或配置开关保留旧路径一轮
- 若深接线导致真实链路退化，可按节点粒度回切

---

## Wave 3：Evidence 深消费与产品联调

**目标**：让 EvidenceStore 从存储层升级为 Report / Forum / Reflection 的决策输入层。

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W3.1 | Reflection 流程消费 evidence conflict / gap 信息，决定补搜或保守表达 | `veyrafish_core/base_research_agent.py` |
| W3.2 | ReportEngine 章节上下文注入 evidence 与 aggregate 信息 | `ReportEngine/` |
| W3.3 | ForumEngine 主持人判断接入 gap/evidence 摘要 | `ForumEngine/monitor.py` |
| W3.4 | 核查 `/api/evidence/<task_id>` 与前端/调试链路的消费方式 | `app.py` / 前端相关文件 |
| W3.5 | 增补 Evidence 深消费测试 | `tests/test_evidence_store.py` / `tests/test_forum_events.py` / 新增测试文件 |
| W3.6 | Docker 环境下跑通一次 evidence 全链路 | Docker 配置与联调记录 |

### 验证门禁

```bash
pytest tests/test_evidence_store.py -v
pytest tests/test_forum_events.py -v
pytest tests/ -q
```

手动联调门禁：

1. Docker 内启动系统
2. 触发一次三引擎研究任务
3. 确认 evidence API 返回非空结构化结果
4. 确认 forum / report 能消费 evidence 信息且无明显退化

### 完成判定

- Evidence 已参与真实决策，不再只是查询展示数据
- Report / Forum 至少各有一条稳定消费路径
- Docker 链路下 evidence 相关功能可完成一次正式验收

### 回滚方式

- evidence 注入保持为增强路径，可在问题定位期间降级为可选上下文

---

## Wave 4：评估、回放与正式验收

**目标**：形成 Phase 2.5 的质量证明与阶段关闭条件。

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W4.1 | 定义首批固定任务样例集（至少覆盖 2-3 个研究主题） | `docs/` / `outputs/` / 测试样例目录 |
| W4.2 | 增加最小回放脚本或测试入口，能重放固定任务 | 脚本或测试文件 |
| W4.3 | 定义结构完整性、覆盖率、冲突保留、证据引用、质量门禁等评分维度 | 文档与评分逻辑 |
| W4.4 | 在真实 LLM 配置下完成至少一轮正式回放 | 验收记录 |
| W4.5 | Docker + 浏览器前端 + 并发链路完成正式验收 | 验收记录 |
| W4.6 | 更新 `PHASE_2_IMPLEMENTATION_CHECKLIST.md`，明确 Phase 2 / 2.5 状态 | `docs/implementation/PHASE_2_IMPLEMENTATION_CHECKLIST.md` |
| W4.7 | 写 Phase 2.5 收口日志和残余风险清单 | `docs/implementation/logs/phase-2/` |

### 验证门禁

```bash
pytest tests/ -q
```

正式验收门禁：

- Docker `/api/system/start` 正常
- 浏览器前端可观察到研究进度与 forum 输出
- 至少一轮真实 LLM 研究任务完整成功
- 至少一轮固定样例回放产出结构化验收结论

### 完成语言规则

- 单波完成 → `Wave N 已完成，门禁通过`
- Phase 2.5 完成 → `Phase 2.5 已完成，验收与深接线门禁通过`
- 若仅代码完成但真实链路未过 → 必须表述为 `代码主路径完成，正式验收未完成`

### 回滚方式

- 评估与回放脚本是增量能力，可独立关闭
- 正式验收失败时不得用“理论上可用”替代真实结果

---

## 交付验收计划

### 1. 测试与导入验证

```bash
pytest tests/ -v
python -c "
from veyrafish_core.skill import SkillContext
from veyrafish_core.skills import default_registry
from veyrafish_core.evidence_store import get_evidence_store
print(default_registry.names())
print(type(get_evidence_store()).__name__)
"
```

### 2. Docker 联调

```bash
docker compose -f docker-compose.local.yml up --build
```

检查项：

- Flask 启动无报错
- `/api/system/start` 正常返回
- `/api/search` 能触发三引擎并发
- `/api/evidence/<task_id>` 可查询

### 3. 浏览器前端联调

- 页面可发起研究任务
- 进度日志可见
- forum 输出可见
- 结果页或调试链路可读取 evidence 数据

### 4. 真实 LLM 回放

- 使用正式配置完成固定样例任务
- 保存输出、评分、问题清单
- 与 Phase 2 基线做最小对比

---

## 建议实施节奏

| 波次 | 预估复杂度 | 建议 |
|------|-----------|------|
| Wave 1 | 中 | 当前阶段优先完成 |
| Wave 2 | 中-高 | 紧接 Wave 1，避免 contract 与接线脱节 |
| Wave 3 | 中 | 在 Docker 联调窗口内完成 |
| Wave 4 | 中 | 所有代码稳定后再做正式收口 |

---

## 阶段清理预期

每波结束后：

- 更新状态文档与执行记录
- 保留通过门禁所需的最小证据
- 删除临时调试残留
- 明确“已完成 / 未完成 / 已降级”的边界

Phase 2.5 结束后：

- Phase 2 主清单应标明“主路径完成”与“2.5 收口状态”
- 为 Phase 3 留下明确的质量基线与残余风险列表
