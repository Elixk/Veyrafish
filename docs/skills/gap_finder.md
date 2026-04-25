# Gap Finder Skill Spec

## 1. Skill ID

`gap_finder`

## 2. Goal

分析当前研究总结中的覆盖缺口、冲突点和时效缺口，为后续补搜或保守表达提供依据。

## 3. 适用场景

- 反思阶段决定是否继续补搜
- Forum 主持人判断当前研究是否存在冲突或信息盲区
- 后续报告生成前对研究覆盖度做保守评估

代码入口：[gap_finder.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/gap_finder.py:1)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:163)

- `summaries`
- `research_question`
- `engine_names`

## 5. Outputs

- `gaps`
- `conflict_notes`
- `overall_coverage`

其中每条 gap 至少包含：

- `description`
- `suggested_query`
- `gap_type`
- `priority`

## 6. 决策规则

- `gap_type` 只允许 `coverage / conflict / recency`
- `priority` 只允许 `high / medium / low`
- 如果模型没有给出合法 `gap_type`，规范化阶段应根据描述和建议检索词推断
- 未提供完整 `engine_names` 时，要补齐默认引擎标签，不能因为 `zip` 截断丢失总结
- `conflict_notes` 应只保留真实冲突信息，不混入运行时失败原因
- 运行时失败或回退原因应进入 `overall_coverage` 或其他说明性字段，而不是伪装成冲突
- `gaps` 和 `conflict_notes` 都需要去重与清洗

## 7. 禁止事项

- 不得把系统错误原因直接写成研究冲突
- 不得输出未知 `gap_type`
- 不得给出空描述或无法执行的补搜建议

## 8. 降级策略

- 无 LLM 时走启发式 `_fallback`
- 结构化输出失败时回退到启发式缺口分析
- fallback 仍应给出至少一个 gap 和覆盖度结论

## 9. 当前实现特点

- 已支持 `coverage / conflict / recency` 三类 gap
- 已支持方向性冲突检测
- 已支持时效缺口判断
- 已支持 gap 与 conflict note 的规范化和去重

## 10. 验证方式

- `tests/test_skill.py` 中 `GapFinderSkill` 相关测试
- `tests/test_graph_integration.py` 中反思阶段对 `gap_finder` 的调用验证

## 11. 后续建议

- 后续可考虑引入更细的冲突分类，而不是只有方向性冲突
- 可在前端调试视图中展示 `gap_type`、`priority` 和 `conflict_notes`
