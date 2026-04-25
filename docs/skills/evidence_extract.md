# Evidence Extract Skill Spec

## 1. Skill ID

`evidence_extract`

## 2. Goal

从原文或总结中提取结构化证据，保留来源绑定、claim 对齐关系和证据缺口。

## 3. 适用场景

- Evidence sink
- ReportEngine 或调试链路的结构化证据上下文
- 对摘要结论做来源追踪时

代码入口：[evidence_extract.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/evidence_extract.py:41)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:99)

- `content`
- `claim`
- `source_url`
- `source_title`

## 5. Outputs

- `evidences`
- `gaps`
- `gap_details`

其中每条 evidence 至少包含：

- `claim`
- `supporting_text`
- `source_url`
- `source_title`
- `confidence`
- `sentiment`
- `claim_relation`
- `tags`

## 6. 决策规则

- 来源字段优先继承输入，保证可追溯。
- `confidence` 必须收紧到 `0.0 ~ 1.0`。
- 如果提供了 `claim`，要尽量判断与提取证据的对齐关系。
- 不仅返回 `gaps` 文本摘要，还要返回可机读的 `gap_details`。
- 如果 LLM 已返回 `gaps`，规范化阶段不应直接覆盖，而应与规则推导出的缺口摘要合并。
- `supporting_text`、`claim` 和 `sentiment` 应做基础清洗和规范化。

## 7. 禁止事项

- 不得只给笼统总结而没有结构化 evidence。
- 不得丢失来源信息。
- 不得把 claim 对齐关系写成无依据的强支持。

## 8. 降级策略

- 无 LLM 时走句子级启发式提取
- 结构化提取失败时回退到 `_fallback_output`
- fallback 仍要给出来源字段、claim relation 和 gap 结果

## 9. 当前实现特点

- 已有 `_normalize_output` 补齐来源与标签
- 已有 `_build_gap_details`
- 已有基于句子拆分的启发式 fallback

## 10. 验证方式

- `tests/test_skill.py` 中 `EvidenceExtractSkill` 相关测试
- `tests/test_graph_integration.py` 中 evidence sink 偏好 skill 的测试

## 11. 后续建议

- 增加更明确的 supporting_text 截断规则
- 评估是否需要引入反向证据或多来源聚合视角
