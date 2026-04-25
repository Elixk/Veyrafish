# Query Rewrite Skill Spec

## 1. Skill ID

`query_rewrite`

## 2. Goal

把原始搜索查询改写成更适合检索的表达，并给出推荐搜索工具与可解释约束。

## 3. 适用场景

- BaseResearchAgent 搜索前规划阶段
- 需要根据主题、时效、平台来优化搜索策略时

代码入口：[query_rewrite.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/query_rewrite.py:34)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:43)

- `original_query`：原始查询
- `context`：段落标题或研究背景
- `search_tools_available`：当前可用搜索工具列表

## 5. Outputs

- `rewritten_query`
- `search_tool`
- `reasoning`
- `selection_rule`
- `constraints`
- `start_date`
- `end_date`
- `platform`
- `time_period`

## 6. 决策规则

- 优先保证查询更具体，而不是更花哨。
- 如果检测到平台信号，尽量带上平台约束。
- 如果检测到时效信号，尽量带上时间约束或近期标识。
- 搜索工具选择要有可解释规则，不能随机选。
- LLM 输出不完整时，用启发式规则补齐字段。
- `constraints` 不应只是原样转抄，应根据最终归一化后的平台和时间字段补齐。

## 7. 禁止事项

- 不得编造不存在的平台或日期。
- 不得输出未在 `search_tools_available` 中声明的工具名。
- 不得把推断当成确定事实。

## 8. 降级策略

- `ctx.llm_client` 不可用时，走启发式 `_fallback`
- `invoke_structured` 失败时，仍返回完整 `QueryRewriteOutput`
- 输出字段为空时，由 `_normalize_output` 用启发式结果回填

## 9. 当前实现特点

- 已有 `_SYSTEM_PROMPT`
- 已有平台识别、日期识别、工具选择规则
- 已有 `_normalize_output` 作为结构化补全层

## 10. 验证方式

- `tests/test_skill.py` 中 `QueryRewriteSkill` 相关测试
- 主链路集成测试中对搜索前改写的调用验证

## 11. 后续建议

- 增加样例集，覆盖微博、新闻、近期、全球舆情等典型场景
- 把 `reasoning` / `selection_rule` 通过调试接口暴露给前端
