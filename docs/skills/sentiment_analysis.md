# Sentiment Analysis Skill Spec

## 1. Skill ID

`sentiment_analysis`

## 2. Goal

对文本列表输出结构化情感判断结果，优先复用专用分析器，失败时再降级到 LLM 或规则兜底。

## 3. 适用场景

- 对舆情片段做正负向粗分
- 为后续报告统计或 Forum 辅助判断提供基础信号
- 在不引入复杂分类器链路的前提下提供稳定情感结果

代码入口：[sentiment_analysis.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/sentiment_analysis.py:1)

## 4. Inputs

定义见：[skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:141)

- `texts`
- `language`

## 5. Outputs

- `results`
- `overall_sentiment`
- `error`

其中每条结果至少包含：

- `text`
- `sentiment`
- `score`
- `confidence`

## 6. 决策规则

- 优先尝试专用情感分析器，再尝试 LLM，最后回退到 neutral 兜底。
- `sentiment` 统一归一化为 `positive / negative / neutral`
- `score` 归一化到 `-1.0 ~ 1.0`
- `confidence` 归一化到 `0.0 ~ 1.0`
- 如果 LLM 返回的 `text` 缺失，使用原输入文本兜底
- `overall_sentiment` 根据平均 `score` 推断，而不是简单多数投票

## 7. 禁止事项

- 不得把未知标签原样透传到结果中
- 不得让非法 `score` / `confidence` 进入最终输出
- 不得因为单条解析失败就让整个 skill 直接报错

## 8. 降级策略

- 专用分析器不可用时降级到 LLM 零样本分析
- LLM 失败或 JSON 无法解析时返回 neutral 兜底结果
- `on_error` 返回结构化失败结果，而不是抛裸异常

## 9. 当前实现特点

- 已支持专用分析器优先
- 已支持 LLM JSON 结果解析
- 已支持情感标签别名、分数、置信度的规范化
- 已支持整体情感的统一推断
- 已支持 LLM 返回 `text` 缺失时回填原始输入文本
- 已支持 LLM 返回条目不足时补齐 neutral 兜底结果

## 10. 验证方式

- `tests/test_skill.py` 中 `SentimentAnalysisSkill` 相关测试
- 重点覆盖：
  - 空输入时的 neutral 空输出
  - 标签别名与数值边界归一化
  - 缺失 `text` 时的 fallback 回填
  - `on_error` 的结构化失败返回

## 11. 后续建议

- 如果后续接入报告统计，可再补样例集和批量评价基线
- 如果要用于更强的产品决策，建议增加更细的情绪标签映射层
