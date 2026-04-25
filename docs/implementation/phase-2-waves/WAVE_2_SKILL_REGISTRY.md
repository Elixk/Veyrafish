# Wave 2：Skill 基类 + SkillRegistry + 核心 Skill

**所属**：Phase 2 二阶段架构升级  
**前置**：Wave 1（StateGraph 已实现）  
**产出**：`veyrafish_core/skill.py` + `veyrafish_core/skills/` + `tests/test_skill.py` + `docs/SKILL_DEVELOPMENT_GUIDE.md`

---

## 1. 目标

建立 Veyrafish 的 **Skill 层基础设施**，从现有引擎提取 5-8 个跨引擎共享的核心 Skill。

设计灵感来源：
- **Vibe-Skills-3.0.0**：YAML front matter（name/description/version/tags）+ 结构化工作流
- **Semantic Kernel Plugin**：函数组 + 语义描述 + DI + 可注册可替换
- **Veyrafish 自身**：`veyrafish_core.output_models` 的 Pydantic 类型化输出

## 2. 核心类设计

### 2.1 Skill（能力基类）

```python
class Skill(ABC):
    name: str                       # 唯一标识，如 "web_search"
    description: str                # 语义描述，供 LLM / 路由理解
    version: str = "0.1.0"
    tags: list[str] = []            # 能力标签，如 ["search", "web"]
    input_schema: type[BaseModel]   # Pydantic 输入模型
    output_schema: type[BaseModel]  # Pydantic 输出模型

    @abstractmethod
    def execute(self, input: BaseModel, ctx: SkillContext) -> BaseModel: ...

    def validate_input(self, input: BaseModel) -> bool:
        """可选的额外校验（默认仅 Pydantic schema 校验）"""
        return True

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> BaseModel | None:
        """错误降级处理（默认不降级，抛出原异常）"""
        return None

    def to_metadata(self) -> dict:
        """导出 Skill 元信息（用于 registry 列表 / 文档生成）"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "input_schema": self.input_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }
```

### 2.2 SkillContext（运行上下文）

```python
@dataclass
class SkillContext:
    task_id: str | None = None
    llm_client: LLMClient | None = None
    config: Any = None               # Settings 实例
    evidence_store: Any = None       # Wave 5 才引入
    budget: SkillBudget | None = None

@dataclass
class SkillBudget:
    max_tokens: int | None = None
    max_seconds: float | None = None
    max_retries: int = 3
```

### 2.3 SkillRegistry（注册表）

```python
class SkillRegistry:
    def register(self, skill: Skill) -> None: ...
    def get(self, name: str) -> Skill | None: ...
    def list(self, tag: str | None = None) -> list[dict]: ...
    def execute(self, name: str, input: BaseModel, ctx: SkillContext) -> BaseModel: ...
    def has(self, name: str) -> bool: ...
    def unregister(self, name: str) -> bool: ...
```

设计要点：
- 内部用 `dict[str, Skill]` 存储
- `list()` 返回所有 Skill 的 `to_metadata()` 列表
- `execute()` 是便捷方法：`get(name).execute(input, ctx)`
- 全局单例 `default_registry` 供各模块导入使用

## 3. 核心 Skill 清单

### 3.1 WebSearchSkill

| 属性 | 值 |
|------|---|
| 来源 | 各引擎 `tools/` 里的 Anspire/Bocha/Tavily 调用 |
| 灵感 | Vibe-Skills `defuddle`（内容清洗提取） |
| 输入 | `WebSearchInput(query, provider, max_results, date_range)` |
| 输出 | `WebSearchOutput(results: list[SearchResult], provider_used, total_found)` |
| 说明 | 统一搜索 Provider 适配层，根据 config 自动选择 Anspire/Bocha/Tavily |

### 3.2 QueryRewriteSkill

| 属性 | 值 |
|------|---|
| 来源 | 各引擎 `FirstSearchNode` 的查询优化逻辑 |
| 灵感 | Vibe-Skills `research-ideation`（研究规划） |
| 输入 | `QueryRewriteInput(original_query, context, search_tools_available)` |
| 输出 | `QueryRewriteOutput(rewritten_query, search_tool, reasoning)` |
| 说明 | LLM 驱动的查询改写 + 工具选择 |

### 3.3 LLMSummarizeSkill

| 属性 | 值 |
|------|---|
| 来源 | 各引擎 `FirstSummaryNode` / `ReflectionSummaryNode` |
| 灵感 | Vibe-Skills `results-analysis`（结构化分析） |
| 输入 | `SummarizeInput(content, paragraph_title, existing_summary, mode)` |
| 输出 | `SummarizeOutput(summary, key_points, confidence)` |
| 说明 | mode 区分 "first_summary" / "reflection_summary" |

### 3.4 EvidenceExtractSkill

| 属性 | 值 |
|------|---|
| 来源 | 各引擎 `ReflectionNode` 的证据提取逻辑 |
| 灵感 | Vibe-Skills `citation-verification`（引用验证） |
| 输入 | `EvidenceExtractInput(content, claim, source_url)` |
| 输出 | `EvidenceExtractOutput(evidences: list[Evidence], gaps: list[str])` |
| 说明 | 从原文提取结构化证据 + 发现证据缺口 |

### 3.5 SentimentAnalysisSkill

| 属性 | 值 |
|------|---|
| 来源 | `InsightEngine.tools.multilingual_sentiment_analyzer` |
| 输入 | `SentimentInput(texts: list[str], language)` |
| 输出 | `SentimentOutput(results: list[SentimentResult])` |
| 说明 | 从 InsightEngine 泛化，其他引擎也可调用 |

### 3.6 GapFinderSkill

| 属性 | 值 |
|------|---|
| 来源 | 新建（部分逻辑来自 ForumEngine 主持人） |
| 灵感 | Vibe-Skills `research-ideation` 的 Gap Analysis |
| 输入 | `GapFinderInput(current_evidence: list[Evidence], research_question)` |
| 输出 | `GapFinderOutput(gaps: list[Gap], suggested_queries: list[str])` |
| 说明 | 分析当前证据缺口，建议补充检索方向 |

### 3.7 QualityGateSkill

| 属性 | 值 |
|------|---|
| 来源 | 新建 |
| 灵感 | Vibe-Skills `verification-loop`（质量门禁） |
| 输入 | `QualityGateInput(content, content_type, criteria)` |
| 输出 | `QualityGateOutput(passed: bool, issues: list[str], score: float)` |
| 说明 | 通用输出质量检查，可配置检查标准 |

## 4. 文件结构

```
veyrafish_core/
    skill.py                    # Skill ABC + SkillContext + SkillBudget
    skills/
        __init__.py             # 导出 default_registry + 自动注册所有 Skill
        _registry.py            # SkillRegistry 实现
        _models.py              # 所有 Skill 共用的 Pydantic I/O 模型
        web_search.py           # WebSearchSkill
        query_rewrite.py        # QueryRewriteSkill
        llm_summarize.py        # LLMSummarizeSkill
        evidence_extract.py     # EvidenceExtractSkill
        sentiment_analysis.py   # SentimentAnalysisSkill
        gap_finder.py           # GapFinderSkill
        quality_gate.py         # QualityGateSkill
```

## 5. 任务分解

| 编号 | 任务 | 预估行数 |
|------|------|---------|
| W2.1 | `Skill` ABC + `SkillContext` + `SkillBudget` | ~80 行 |
| W2.2 | `SkillRegistry` 实现 | ~60 行 |
| W2.3 | `_models.py` 共用 Pydantic 模型 | ~120 行 |
| W2.4 | `WebSearchSkill` | ~80 行 |
| W2.5 | `QueryRewriteSkill` | ~60 行 |
| W2.6 | `LLMSummarizeSkill` | ~70 行 |
| W2.7 | `EvidenceExtractSkill` | ~70 行 |
| W2.8 | `SentimentAnalysisSkill` | ~50 行 |
| W2.9 | `GapFinderSkill` | ~60 行 |
| W2.10 | `QualityGateSkill` | ~50 行 |
| W2.11 | 单元测试 | ~200 行 |
| W2.12 | Skill 开发指南 | ~150 行 MD |

预估总量：**~700 行代码 + ~200 行测试 + ~150 行文档**

## 6. 测试计划

```python
# tests/test_skill.py

class TestSkillBase:
    def test_skill_metadata_export(self): ...
    def test_skill_input_validation(self): ...
    def test_skill_error_handling(self): ...

class TestSkillRegistry:
    def test_register_and_get(self): ...
    def test_list_all(self): ...
    def test_list_by_tag(self): ...
    def test_execute_via_registry(self): ...
    def test_unregister(self): ...
    def test_duplicate_register_raises(self): ...

class TestWebSearchSkill:
    def test_anspire_provider(self): ...
    def test_fallback_provider(self): ...

class TestQueryRewriteSkill:
    def test_rewrite_with_mock_llm(self): ...

class TestQualityGateSkill:
    def test_pass_criteria(self): ...
    def test_fail_criteria(self): ...
```

## 7. 验证门禁

```bash
pytest tests/test_skill.py -v     # 全部通过
pytest tests/ -q                  # 无回归
python -c "from veyrafish_core.skills import default_registry; print([s['name'] for s in default_registry.list()])"
```

## 8. 回滚方式

删除 `veyrafish_core/skill.py` + `veyrafish_core/skills/` + `tests/test_skill.py`。

## 9. 与后续 Wave 的接口

- Wave 3 的图节点可以内部调用 `SkillRegistry.execute()` 来复用 Skill
- Wave 4 的 GapFinderSkill 会被 ForumEngine 使用
- Wave 5 的 EvidenceExtractSkill 会自动沉淀证据到 EvidenceStore
