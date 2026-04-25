# 二阶段升级需求文档：Agent 架构升级

**状态**：已冻结  
**日期**：2026-04-23  
**基于**：ChatGPT 参考文档 + 当前 veyrafish_core 实际代码 + Vibe-Skills-3.0.0 参考库

---

## 1. 目标

在现有 `veyrafish_core` 基础上增量升级 Veyrafish 的 Agent 运行时架构，使其从"隐式节点循环"进化为"显式状态图 + Skill 注册表 + 事件驱动协作"，同时保持项目"零外部框架依赖"的核心定位。

## 2. 交付物

| 编号 | 交付物 | 说明 |
|------|--------|------|
| D1 | `veyrafish_core/graph.py` | 自研轻量状态图引擎（StateGraph + GraphRunner） |
| D2 | `veyrafish_core/skill.py` | Skill 基类 + SkillRegistry |
| D3 | `veyrafish_core/skills/` | 5-8 个从现有引擎提取的共享 Skill |
| D4 | 三引擎图谱化 | Insight/Media/Query 的 research 流程迁移到 StateGraph |
| D5 | ForumEngine 事件驱动 | 从日志文件监听升级为 task_events 订阅 |
| D6 | 三引擎并发调度 | 研究任务真正并发执行 |
| D7 | 共享证据层 | evidence 表 + 结构化证据沉淀 |
| D8 | 测试 + 文档 | 新增单元测试、迁移文档、Skill 开发指南 |

## 3. 约束

- **零新框架依赖**：不引入 LangGraph / LangChain / CrewAI 等。图引擎、Skill 层全部自研，放在 `veyrafish_core` 内。
- **增量演进**：不创建 `veyrafish_next/`，不推倒重来。每个改造独立可验证、可回滚。
- **向后兼容**：`research(query)` 不传 `task_id` 时行为不变；现有 72 个测试不能回归。
- **竞赛友好**：自研组件是答辩加分项；代码量可控，不做过度设计。

## 4. 验收标准

### 技术验收
- [ ] `StateGraph` 支持：add_node / add_edge / conditional_edge / run / checkpoint
- [ ] `SkillRegistry` 支持：register / get / list / execute
- [ ] 三引擎 `research()` 通过 StateGraph 执行，输出与原版一致
- [ ] ForumEngine 不再读 .log 文件，改为轮询 task_events
- [ ] 三引擎可并发执行（`ThreadPoolExecutor` + 共享 evidence）
- [ ] `pytest tests/` 全部通过（原有 + 新增）

### 产品验收
- [ ] Docker 容器内启动后 `/api/system/start` 仍正常工作
- [ ] 前端控制台仍能看到各引擎日志
- [ ] 报告质量不因架构变化而下降

## 5. Skill 设计规范

### 5.1 Skill 接口（借鉴 Vibe-Skills-3.0.0 的 SKILL.md 结构 + Semantic Kernel Plugin 思路）

```python
class Skill(ABC):
    name: str                    # 唯一标识，如 "web_search"
    description: str             # 语义描述，供 LLM 理解
    version: str                 # 版本号
    tags: list[str]              # 能力标签，如 ["search", "web"]
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]

    @abstractmethod
    def execute(self, input: BaseModel, ctx: SkillContext) -> BaseModel: ...

    def validate_input(self, input: BaseModel) -> bool: ...
    def on_error(self, error: Exception, input: BaseModel) -> BaseModel | None: ...
```

### 5.2 SkillContext（运行上下文）

```python
@dataclass
class SkillContext:
    task_id: str | None
    llm_client: LLMClient
    config: Settings
    evidence_store: EvidenceStore | None
    budget: SkillBudget | None       # token/时间预算
```

### 5.3 计划提取的核心 Skill（参考 Vibe-Skills 的模块化思路）

| Skill | 来源 | 灵感参考 |
|-------|------|---------|
| `WebSearchSkill` | 各引擎 tools/ 的 Anspire/Bocha/Tavily 适配 | defuddle（内容提取） |
| `LLMSummarizeSkill` | 各引擎 FirstSummaryNode | results-analysis（结构化分析） |
| `SentimentAnalysisSkill` | InsightEngine 情感分析 | results-analysis（统计严谨性） |
| `EvidenceExtractSkill` | 各引擎 ReflectionNode | citation-verification（证据验证） |
| `QueryRewriteSkill` | 各引擎 FirstSearchNode 的查询优化 | research-ideation（研究规划） |
| `ReportSectionSkill` | ReportEngine 章节生成 | — |
| `GapFinderSkill` | ForumEngine 缺口发现 | research-ideation（Gap Analysis） |
| `QualityGateSkill` | 新增：输出质量检查 | verification-loop（质量门禁） |

### 5.4 Skill 文件结构

```
veyrafish_core/skills/
    __init__.py
    _registry.py          # SkillRegistry 实现
    web_search.py          # WebSearchSkill
    llm_summarize.py       # LLMSummarizeSkill
    sentiment_analysis.py  # SentimentAnalysisSkill
    evidence_extract.py    # EvidenceExtractSkill
    query_rewrite.py       # QueryRewriteSkill
    gap_finder.py          # GapFinderSkill
    quality_gate.py        # QualityGateSkill
```

## 6. 状态图设计规范

### 6.1 StateGraph 核心 API

```python
graph = StateGraph(name="insight_research")
graph.add_node("generate_structure", generate_structure_fn)
graph.add_node("process_paragraph", process_paragraph_fn)
graph.add_node("reflection", reflection_fn)
graph.add_node("format_report", format_report_fn)

graph.add_edge("generate_structure", "process_paragraph")
graph.add_conditional_edge("process_paragraph", 
    condition=has_more_paragraphs,
    true_target="process_paragraph",
    false_target="format_report")
graph.add_conditional_edge("reflection",
    condition=should_continue_reflecting,
    true_target="reflection",
    false_target="process_paragraph")

graph.set_entry("generate_structure")
graph.set_finish("format_report")
```

### 6.2 GraphRunner

```python
runner = GraphRunner(graph, checkpoint_store=task_store)
result = runner.run(initial_state, task_id="xxx")
# 支持：节点事件自动写入 task_events、异常时自动 checkpoint、resume
```

## 7. 非目标

- 不做 UI 改造（属于 Phase 3）
- 不做 ReportEngine 重构（保持现有 IR + renderer 架构）
- 不引入 Redis / NATS / 消息队列
- 不做分布式部署
- 不做模型路由 / A-B 测试

## 8. 推断假设

- 当前 `veyrafish_core` 的 `BaseResearchAgent` 可以逐步迁移到 StateGraph，不需要一次性全改
- `task_store.task_events` 表足以支撑 ForumEngine 的事件驱动需求
- 三引擎并发的最大瓶颈是 LLM API 调用，不是本地 CPU/内存
- Skill 的粒度以"可被多个引擎复用"为标准，不做更细的拆分
