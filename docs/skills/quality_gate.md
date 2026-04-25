# Quality Gate Skill Spec

## 1. Skill ID

`quality_gate`

## 2. Goal

在内容进入下游主链路前做质量门禁，识别空内容、过短、重复、缺少支撑信号等问题。

## 3. 适用场景

- 摘要输出前检查
- 报告章节草稿检查
- 证据型内容检查

代码入口：[quality_gate.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/quality_gate.py:51)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:189)

- `content`
- `content_type`
- `criteria`
- `min_length`

## 5. Outputs

- `passed`
- `score`
- `content_type_used`
- `criteria_used`
- `issues`
- `suggestions`

## 6. 决策规则

- 先走规则检查，再可选地用 LLM 做深度评分。
- `content_type` 决定默认 profile。
- 未识别的 `content_type` 统一回退到 `summary` profile，并在输出中明确 `content_type_used`。
- `score` 范围必须在 `0.0 ~ 1.0`。
- 有 `error` 级问题时，不应判定通过。
- 输出不能只有分数，必须给出 `issues` 或建议。

## 7. 禁止事项

- 不得只用长度判断质量。
- 不得在检查失败时静默通过。
- 不得让 LLM 评分覆盖掉基本规则的护栏。

## 8. 降级策略

- 无 LLM 时只用规则检查
- LLM 评分失败时保留基础分数
- `on_error` 返回结构化失败结果，而不是抛空异常给上游

## 9. 当前实现特点

- 已按 `summary / report_section / evidence` 区分 profile
- 已检查重复、支撑信号和摘要焦点
- 已支持非阻塞式 LLM 深评估

## 10. 验证方式

- `tests/test_skill.py` 中 `QualityGateSkill` 相关测试
- 主链路集成测试中对摘要门禁的调用验证

## 11. 后续建议

- 把 `issues` 和 `score` 暴露给调试界面
- 视需要增加更细的 `content_type` profile
