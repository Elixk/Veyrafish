# Wave 5：共享证据层

**所属**：Phase 2 二阶段架构升级  
**前置**：Wave 3（三引擎图谱化）+ Wave 4（ForumEngine 事件驱动）  
**产出**：`veyrafish_core/evidence_store.py` + `task_store.py` 扩展 + `tests/test_evidence_store.py`

---

## 1. 目标

让三引擎在研究过程中 **持续沉淀结构化证据**，而非仅在最后输出 Markdown 报告。ReportEngine 在生成报告时可以同时读取结构化证据，提升章节生成、引用绑定和矛盾检测的准确性。

### 为什么需要这一层

当前流程：
```
InsightEngine → insight_report.md ─┐
MediaEngine  → media_report.md  ──┤──→ ReportEngine（读 Markdown）──→ 最终报告
QueryEngine  → query_report.md  ──┘
ForumEngine  → forum.log       ───┘
```

问题：
- ReportEngine 只能读最终 Markdown，丢失了大量中间证据粒度
- 无法做跨引擎的矛盾检测（A 引擎说涨、B 引擎说跌）
- 引用绑定全靠 LLM 自行匹配，不可靠

目标流程：
```
InsightEngine ──┐                    ┌─ insight_report.md
MediaEngine  ───┤──→ evidence 表 ───┤─ media_report.md    ──→ ReportEngine ──→ 最终报告
QueryEngine  ───┘                    └─ query_report.md
                                     + evidence 表（结构化证据）
```

## 2. 核心数据模型

### 2.1 Evidence（Pydantic 模型）

```python
class Evidence(BaseModel):
    """单条结构化证据。"""
    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    engine: str                     # "insight" / "media" / "query"
    paragraph_index: int | None = None
    claim: str                      # 证据声明（一句话）
    supporting_text: str = ""       # 原文摘录
    source_url: str = ""            # 来源 URL
    source_title: str = ""          # 来源标题
    confidence: float = 0.5         # 0.0 ~ 1.0
    sentiment: str | None = None    # "positive" / "negative" / "neutral" / None
    tags: list[str] = []            # 自定义标签
    created_at: str = ""            # ISO 时间戳
```

### 2.2 EvidenceAggregate（聚合结果）

```python
class EvidenceAggregate(BaseModel):
    """跨引擎证据聚合摘要。"""
    total_count: int
    by_engine: dict[str, int]       # {"insight": 12, "media": 8, "query": 15}
    by_sentiment: dict[str, int]    # {"positive": 10, "negative": 5, "neutral": 20}
    avg_confidence: float
    top_claims: list[str]           # confidence 最高的 N 条 claim
    conflicts: list[dict]           # 相互矛盾的证据对
```

## 3. 存储层设计

### 3.1 SQLite 表结构（扩展 task_store.py）

```sql
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id   TEXT PRIMARY KEY,
    task_id       TEXT NOT NULL,
    engine        TEXT NOT NULL,
    paragraph_index INTEGER,
    claim         TEXT NOT NULL,
    supporting_text TEXT DEFAULT '',
    source_url    TEXT DEFAULT '',
    source_title  TEXT DEFAULT '',
    confidence    REAL DEFAULT 0.5,
    sentiment     TEXT,
    tags          TEXT DEFAULT '[]',     -- JSON array
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence(task_id);
CREATE INDEX IF NOT EXISTS idx_evidence_engine ON evidence(task_id, engine);
```

### 3.2 EvidenceStore 类

```python
class EvidenceStore:
    """证据存储与查询。复用 TaskStore 的 SQLite 连接。"""
    
    def __init__(self, db_path: str = "logs/tasks.db"): ...
    
    # ---- 写入 ----
    def add(self, evidence: Evidence) -> str: ...
    def add_batch(self, evidences: list[Evidence]) -> int: ...
    
    # ---- 查询 ----
    def query_by_task(self, task_id: str, engine: str | None = None, limit: int = 200) -> list[Evidence]: ...
    def query_by_claim(self, task_id: str, keyword: str) -> list[Evidence]: ...
    def get(self, evidence_id: str) -> Evidence | None: ...
    
    # ---- 聚合 ----
    def aggregate(self, task_id: str) -> EvidenceAggregate: ...
    def find_conflicts(self, task_id: str) -> list[dict]: ...
    
    # ---- 清理 ----
    def delete_by_task(self, task_id: str) -> int: ...
```

设计要点：
- 与 `TaskStore` 共用同一个 SQLite 文件（`logs/tasks.db`），避免多数据库
- `_init_db()` 时自动 `CREATE TABLE IF NOT EXISTS`
- `find_conflicts()` 初版可以简单地找"同一 task_id 下 sentiment 相反的 claim 对"
- 全局单例 `get_evidence_store()` 供各模块导入

## 4. 引擎集成方式

### 4.1 BaseResearchAgent 自动沉淀

在图节点执行过程中，当搜索结果被总结时，自动提取并沉淀证据：

```python
# BaseResearchAgent._node_process_paragraph()
def _node_process_paragraph(self, state):
    # ... 执行搜索、总结 ...
    
    # 自动沉淀证据（如果 evidence_store 可用）
    if self._evidence_store and state.task_id:
        evidences = self._extract_evidences_from_summary(
            summary=state.current_paragraph_summary,
            search_results=state.current_search_results,
            paragraph_index=state.current_paragraph_index,
        )
        self._evidence_store.add_batch(evidences)
    
    return state
```

### 4.2 证据提取方式

两种方案（可共存）：

**方案 A：基于 EvidenceExtractSkill（推荐）**
```python
skill_output = registry.execute("evidence_extract", EvidenceExtractInput(
    content=summary,
    source_url=search_results[0].url,
), ctx)
```

**方案 B：基于 LLM 结构化输出**
```python
evidences = self.llm_client.invoke_structured(
    prompt="从以下总结中提取结构化证据...",
    output_model=list[Evidence],
)
```

初版推荐方案 B（更简单），后续可迁移到方案 A。

### 4.3 ReportEngine 可选读取

ReportEngine 的改动**最小化**——不强制依赖 evidence 表，而是**可选增强**：

```python
# ReportEngine 章节生成时，额外传入结构化证据
if evidence_store:
    evidences = evidence_store.query_by_task(task_id)
    aggregate = evidence_store.aggregate(task_id)
    # 追加到章节生成的上下文中
    section_context["structured_evidence"] = evidences
    section_context["evidence_summary"] = aggregate
```

## 5. 任务分解

| 编号 | 任务 | 文件 | 预估行数 |
|------|------|------|---------|
| W5.1 | `Evidence` + `EvidenceAggregate` Pydantic 模型 | `veyrafish_core/output_models.py` | ~50 行 |
| W5.2 | `evidence` 表 DDL + 索引 | `task_store.py`（扩展 `_init_db`） | ~15 行 |
| W5.3 | `EvidenceStore` 类（add / query / aggregate / conflicts / delete） | `veyrafish_core/evidence_store.py` | ~180 行 |
| W5.4 | `get_evidence_store()` 全局单例 | `veyrafish_core/evidence_store.py` | ~15 行 |
| W5.5 | BaseResearchAgent 集成：`_extract_evidences_from_summary()` | `veyrafish_core/base_research_agent.py` | ~40 行 |
| W5.6 | BaseResearchAgent 集成：在 `_node_process_paragraph` 中调用沉淀 | `veyrafish_core/base_research_agent.py` | ~15 行 |
| W5.7 | ReportEngine 可选读取（最小改动） | `ReportEngine/` | ~20 行 |
| W5.8 | 单元测试 | `tests/test_evidence_store.py` | ~180 行 |

预估总量：**~335 行代码 + ~180 行测试**

## 6. 测试计划

```python
# tests/test_evidence_store.py

class TestEvidenceStore:
    def test_add_single_evidence(self): ...
    def test_add_batch(self): ...
    def test_query_by_task(self): ...
    def test_query_by_task_and_engine(self): ...
    def test_query_by_claim_keyword(self): ...
    def test_aggregate_counts(self): ...
    def test_aggregate_avg_confidence(self): ...
    def test_find_conflicts_opposite_sentiment(self): ...
    def test_delete_by_task(self): ...
    def test_evidence_serialization(self): ...
    def test_empty_task_returns_empty(self): ...
    def test_coexists_with_task_store(self): ...
```

## 7. 验证门禁

```bash
pytest tests/test_evidence_store.py -v  # 全部通过
pytest tests/ -q                        # 全量无回归
```

## 8. 回滚方式

- `evidence` 表是 **新增表**，不影响现有 `tasks` / `task_events` 表
- BaseResearchAgent 中的沉淀逻辑被 `if self._evidence_store:` 守护，删除 evidence_store 模块后自动跳过
- ReportEngine 的读取是 `if evidence_store:` 可选路径，删除后不影响报告生成

## 9. 未来扩展

- **矛盾检测增强**：用 embedding 相似度 + 情感方向对比，发现语义矛盾
- **证据权重**：根据来源可信度、引用次数、时效性动态调整 confidence
- **GraphRAG 集成**：当 `GRAPHRAG_ENABLED=True` 时，证据同步写入知识图谱
- **API 暴露**：新增 `/api/evidence/<task_id>` 供前端展示证据图
