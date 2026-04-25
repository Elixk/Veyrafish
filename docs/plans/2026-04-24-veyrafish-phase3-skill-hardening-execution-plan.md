# Phase 3 Skill 专项执行计划：Skill Hardening 与资产化

**需求文档**：`docs/requirements/2026-04-24-veyrafish-phase3-skill-hardening.md`  
**内部执行等级**：L  
**日期**：2026-04-24  
**运行模式**：`$vibe`

---

## 1. 执行策略

本轮按 4 波推进：

1. **Wave 1：Skill 状态盘点与分层**
2. **Wave 2：核心 skill spec 资产化**
3. **Wave 3：代码与测试对齐第一批**
4. **Wave 4：验证、残余风险与下一批建议**

## 2. Wave 1：Skill 状态盘点与分层

**目标**：统一回答“哪些 skill 要补全，哪些先不补全”。

### 任务

| 编号 | 任务 | 文件 |
|------|------|------|
| W1.1 | 盘点 7 个 skill 的当前实现、接线状态、测试状态 | `veyrafish_core/skills/`, `tests/` |
| W1.2 | 按 `核心 / 增强 / 适配层` 分层 | `docs/skills/README.md` |
| W1.3 | 记录每个 skill 当前缺口与优先级 | `docs/skills/README.md` |

### 验收

- 能明确说明为什么只优先补 4 个核心 skill。
- `web_search` 被清楚归类为适配层。

## 3. Wave 2：核心 skill spec 资产化

**目标**：把核心 4 个 skill 从“代码里的 prompt 和注释”升级为“独立可读 spec”。

### 任务

| 编号 | 任务 | 文件 |
|------|------|------|
| W2.1 | 编写 `query_rewrite` spec | `docs/skills/query_rewrite.md` |
| W2.2 | 编写 `llm_summarize` spec | `docs/skills/llm_summarize.md` |
| W2.3 | 编写 `evidence_extract` spec | `docs/skills/evidence_extract.md` |
| W2.4 | 编写 `quality_gate` spec | `docs/skills/quality_gate.md` |
| W2.5 | 在总览中挂接 spec 和验收范围 | `docs/skills/README.md` |

### 验收

- 每个 spec 至少包含：目标、适用场景、输入、输出、决策规则、禁止事项、降级策略、验证方式。
- spec 能映射回代码与 schema。

## 4. Wave 3：代码与测试对齐第一批

**目标**：根据 spec 对最关键的不一致项做小步修正。

### 任务

| 编号 | 任务 | 文件 |
|------|------|------|
| W3.1 | 对齐核心 skill 的 metadata / prompt / fallback 描述 | `veyrafish_core/skills/*.py` |
| W3.2 | 如有必要，补充 `_models.py` 字段说明或默认值 | `veyrafish_core/skills/_models.py` |
| W3.3 | 补充或修正 `tests/test_skill.py` 中的关键断言 | `tests/test_skill.py` |
| W3.4 | 只做最小必要接线修正，不扩大战线 | 相关代码 |

### 验收

- 代码与 spec 不再明显冲突。
- 测试能覆盖新增 contract。

## 5. Wave 4：验证与下一批建议

**目标**：给本轮一个清晰收口，并为下一批 skill 增强留接口。

### 任务

| 编号 | 任务 | 文件 |
|------|------|------|
| W4.1 | 运行 skill 相关测试 | `tests/` |
| W4.2 | 记录残余风险 | `docs/skills/README.md` 或实现日志 |
| W4.3 | 给出第二批建议：`gap_finder`、`sentiment_analysis`、`web_search` | 文档 |

### 验收

- 能明确说出本轮完成了什么，没完成什么。
- 后续前端和 Docker 阶段可以直接消费文档成果。

## 6. Verification Commands

```powershell
python -m pytest tests/test_skill.py -v
python -m pytest tests/test_graph_integration.py -v
python -m pytest
python -c "from veyrafish_core.skills import default_registry; print(default_registry.names())"
```

## 7. Ownership Boundaries

- 文档资产：`docs/skills/`
- 核心实现：`veyrafish_core/skills/`
- 测试：`tests/test_skill.py`, `tests/test_graph_integration.py`

## 8. Rollback Rules

- 文档新增不回滚现有代码。
- 代码改动只做 contract 对齐，不重写实现框架。
- 如某个 skill 的增强破坏主链路，优先回退该 skill 的增强而不是回退整个 registry。

## 9. Phase Cleanup Expectations

本轮结束时至少留下：

- Skill 总览文档
- 核心 4 个 skill spec
- 首批代码/测试对齐记录
- 验证结果和残余风险
