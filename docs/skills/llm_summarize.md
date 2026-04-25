# LLM Summarize Skill Spec

## 1. Skill ID

`llm_summarize`

## 2. Goal

基于输入证据生成结构化摘要，并支持反思阶段的增量修订，而不是每次全文重写。

## 3. 适用场景

- 首轮搜索结果压缩
- 反思阶段对旧结论进行增量修订

代码入口：[llm_summarize.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/llm_summarize.py:53)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:68)

- `content`
- `paragraph_title`
- `existing_summary`
- `existing_key_points`
- `mode`

## 5. Outputs

- `summary`
- `key_points`
- `confidence`
- `conflicts`
- `uncertainties`
- `entities`
- `retained_points`
- `new_points`
- `revised_points`
- `change_log`

## 6. 决策规则

- 只压缩输入证据，不引入外部常识。
- 有冲突时保留冲突，不强行统一。
- `reflection_summary` 模式必须体现更新痕迹。
- `confidence` 必须在 `0.0 ~ 1.0` 之间。
- 如果 `key_points` 缺失，至少从 `summary` 回填一个关键点。
- `reflection_summary` 模式下，如果 LLM 未明确给出 delta 字段，规范化阶段需要尽量补齐 `retained_points`、`new_points` 和最小 `change_log`。
- 列表字段应去重、裁剪和清洗，避免重复堆叠。

## 7. 禁止事项

- 不得把摘要写成泛泛空话。
- 不得在反思模式里完全丢失旧结论痕迹。
- 不得把不确定信息写成明确结论。

## 8. 降级策略

- 无 LLM 时，走 `_fallback_output`
- 结构化输出失败时，尝试普通 `invoke`
- 普通调用仍失败时，回到规则压缩路径

## 9. 当前实现特点

- 已区分首轮压缩 prompt 与反思更新 prompt
- 已有 `_normalize_output`
- 已有无 LLM 的保守降级

## 10. 验证方式

- `tests/test_skill.py` 中 `LLMSummarizeSkill` 相关测试
- `tests/test_graph_integration.py` 中 Wave 2.5 skill integration 测试

## 11. 后续建议

- 增加固定回放样例，比较首轮摘要与反思摘要差异
- 考虑把 `conflicts` / `uncertainties` 暴露给前端调试视图
