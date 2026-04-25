# 二阶段升级执行计划：Agent 架构升级

**需求文档**：`docs/requirements/2026-04-23-phase2-architecture-upgrade.md`  
**内部执行等级**：L（串行分波推进，每波独立可验证）  
**日期**：2026-04-23

---

## 执行策略

分 **5 波（Wave）** 推进，每波结束后必须通过验证门禁才进入下一波。
前 3 波是核心改造（本次对话完成），后 2 波是增强层（可跨对话）。

---

## Wave 1：自研状态图引擎

**目标**：在 `veyrafish_core` 内实现零依赖的 StateGraph + GraphRunner

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W1.1 | 实现 `StateGraph` 类（add_node / add_edge / add_conditional_edge / set_entry / set_finish / validate） | `veyrafish_core/graph.py` |
| W1.2 | 实现 `GraphRunner` 类（run / resume / 自动写入 task_events / 异常 checkpoint） | `veyrafish_core/graph.py` |
| W1.3 | 实现 `GraphState` 基类（带 `to_dict` / `from_dict` 序列化） | `veyrafish_core/graph.py` |
| W1.4 | 单元测试：图构建、线性执行、条件分支、异常恢复、checkpoint | `tests/test_graph.py` |

### 验证门禁

```bash
pytest tests/test_graph.py -v     # 全部通过
pytest tests/ -q                  # 原有测试无回归
```

### 回滚方式

删除 `veyrafish_core/graph.py` + `tests/test_graph.py`，不影响任何现有代码。

---

## Wave 2：Skill 基类 + SkillRegistry + 核心 Skill 提取

**目标**：建立 Skill 层基础设施，从现有引擎提取 5-8 个共享 Skill

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W2.1 | 实现 `Skill` ABC + `SkillContext` + `SkillBudget` | `veyrafish_core/skill.py` |
| W2.2 | 实现 `SkillRegistry`（register / get / list / execute + 按 tag 查询） | `veyrafish_core/skills/_registry.py` |
| W2.3 | 提取 `WebSearchSkill`：统一 Anspire/Bocha/Tavily 适配 | `veyrafish_core/skills/web_search.py` |
| W2.4 | 提取 `QueryRewriteSkill`：LLM 驱动的查询优化 | `veyrafish_core/skills/query_rewrite.py` |
| W2.5 | 提取 `LLMSummarizeSkill`：搜索结果摘要 | `veyrafish_core/skills/llm_summarize.py` |
| W2.6 | 提取 `EvidenceExtractSkill`：结构化证据提取 | `veyrafish_core/skills/evidence_extract.py` |
| W2.7 | 提取 `SentimentAnalysisSkill`：情感分析（从 InsightEngine 泛化） | `veyrafish_core/skills/sentiment_analysis.py` |
| W2.8 | 新建 `GapFinderSkill`：证据缺口发现（参考 research-ideation 的 Gap Analysis） | `veyrafish_core/skills/gap_finder.py` |
| W2.9 | 新建 `QualityGateSkill`：输出质量检查（参考 verification-loop） | `veyrafish_core/skills/quality_gate.py` |
| W2.10 | 单元测试：registry CRUD、Skill 执行、错误处理 | `tests/test_skill.py` |
| W2.11 | Skill 开发指南文档 | `docs/SKILL_DEVELOPMENT_GUIDE.md` |

### 验证门禁

```bash
pytest tests/test_skill.py -v     # 全部通过
pytest tests/ -q                  # 无回归
python -c "from veyrafish_core.skills import registry; print(registry.list())"  # 能列出已注册 Skill
```

### 回滚方式

删除 `veyrafish_core/skill.py` + `veyrafish_core/skills/` + `tests/test_skill.py`。

---

## Wave 3：三引擎图谱化迁移

**目标**：把 Insight/Media/Query 的 `research()` 流程从 BaseResearchAgent 硬编码迁移到 StateGraph

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W3.1 | 为 BaseResearchAgent 新增 `_build_graph()` 方法，返回 `StateGraph` | `veyrafish_core/base_research_agent.py` |
| W3.2 | 重构 `research()` 方法：通过 `GraphRunner.run()` 执行图 | `veyrafish_core/base_research_agent.py` |
| W3.3 | 重构 `research_with_resume()` 方法：通过 `GraphRunner.resume()` 执行 | `veyrafish_core/base_research_agent.py` |
| W3.4 | 确保三引擎子类不需要修改（图的节点绑定通过 `_initialize_nodes()` 已有方法完成） | `InsightEngine/agent.py` 等（验证不改动） |
| W3.5 | 端到端集成测试（mock LLM） | `tests/test_graph_integration.py` |

### 验证门禁

```bash
pytest tests/test_graph_integration.py -v  # 图谱化流程通过
pytest tests/ -q                           # 全量无回归（含原有 72 个）
```

### 关键设计决策

- `_build_graph()` 是 BaseResearchAgent 的**默认实现**，子类可以 override 自定义图结构
- 图的每个节点内部调用现有的 Node 类（FirstSearchNode 等），不改 Node 层
- `task_events` 写入从手动 `_emit()` 迁移到 GraphRunner 自动发射

### 回滚方式

保留 `research()` 旧实现为 `_research_legacy()`，通过配置开关切换。

---

## Wave 4：ForumEngine 事件驱动 + 三引擎并发

**目标**：Forum 从日志监听升级为事件订阅；三引擎研究任务并发执行

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W4.1 | ForumEngine `LogMonitor` 新增 `poll_events(task_ids)` 方法，从 task_events 表读取结构化事件 | `ForumEngine/monitor.py` |
| W4.2 | ForumEngine 主持人触发条件从"日志行数"改为"paragraph_done 事件数" | `ForumEngine/monitor.py` |
| W4.3 | ForumEngine 主持人发言写入 task_events（`forum_host_speech`） | `ForumEngine/monitor.py` |
| W4.4 | 保留 `forum.log` 写入作为 UI 兼容层（Socket.IO 仍读 forum.log 推送前端） | `ForumEngine/monitor.py` |
| W4.5 | `app.py` 新增并发调度：`/api/search` 或 `initialize_system_components` 中三引擎并发启动研究 | `app.py` |
| W4.6 | 并发调度通过 `ThreadPoolExecutor` 实现，每引擎独立 task_id | `app.py` |
| W4.7 | 测试：ForumEngine 事件轮询、并发调度 | `tests/test_forum_events.py` |

### 验证门禁

```bash
pytest tests/test_forum_events.py -v   # ForumEngine 事件驱动通过
pytest tests/ -q                       # 全量无回归
```

### 回滚方式

ForumEngine 的 `poll_events` 与旧的日志监听并存，通过 `use_event_bus=True/False` 切换。

---

## Wave 5：共享证据层

**目标**：三引擎在执行过程中沉淀结构化证据，ReportEngine 可直接读取

### 任务清单

| 编号 | 任务 | 文件 |
|------|------|------|
| W5.1 | 在 task_store 中新增 `evidence` 表 | `task_store.py` |
| W5.2 | 定义 `Evidence` Pydantic 模型（claim / source / confidence / sentiment / engine / timestamp） | `veyrafish_core/output_models.py` |
| W5.3 | BaseResearchAgent 在 `_initial_search_and_summary` 和 `_reflection_loop` 中自动沉淀证据 | `veyrafish_core/base_research_agent.py` |
| W5.4 | 新增 `EvidenceStore` 类（add / query_by_task / query_by_claim / aggregate） | `veyrafish_core/evidence_store.py` |
| W5.5 | ReportEngine 可选读取 evidence 表辅助章节生成（不强制，保持现有报告逻辑兼容） | `ReportEngine/` （最小改动） |
| W5.6 | 测试：证据写入、查询、聚合 | `tests/test_evidence_store.py` |

### 验证门禁

```bash
pytest tests/test_evidence_store.py -v  # 证据层通过
pytest tests/ -q                        # 全量无回归
```

### 回滚方式

`evidence` 表是新增表，不影响现有 `tasks` / `task_events` 表。删除相关代码即回滚。

---

## 交付验收计划

### 全量验证命令

```bash
# 1. 单元测试全量
pytest tests/ -v

# 2. 导入验证
python -c "
from veyrafish_core.graph import StateGraph, GraphRunner
from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._registry import SkillRegistry
from veyrafish_core.evidence_store import EvidenceStore
print('All Phase 2 modules imported successfully')
"

# 3. Docker 构建验证
docker compose -f docker-compose.local.yml up --build
# 验证 Flask 启动无报错、/api/system/start 正常工作
```

### 完成语言规则

- 单波完成 → "Wave N 已完成，门禁通过"
- 全部完成 → "二阶段升级核心交付完成"
- 部分完成 → 必须明确列出"已完成 / 未完成 / 降级处理"

---

## 建议实施节奏

| 波次 | 预估复杂度 | 建议 |
|------|-----------|------|
| Wave 1 | 中 | 本次对话完成 |
| Wave 2 | 中-高 | 本次对话完成核心 Skill（W2.1-W2.5），其余跨对话 |
| Wave 3 | 中 | 本次对话完成 |
| Wave 4 | 中 | 下次对话 |
| Wave 5 | 低-中 | 下次对话 |

---

## 阶段清理预期

每波结束后：
- 更新 `PHASE_2_IMPLEMENTATION_CHECKLIST.md`
- 写轮次日志到 `docs/implementation/logs/phase-2/`
- 确认无临时文件残留
- 确认测试全绿
