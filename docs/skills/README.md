# Veyrafish Skill 总览

## 1. 定位

Veyrafish 当前的内部 skill 不是外部 `SKILL.md` 路由系统，而是基于 `Skill` 基类、`SkillRegistry`、Pydantic schema 和运行时 `SkillContext` 的**项目内业务能力模块**。

它们的主要组成：

- 基类与上下文：[veyrafish_core/skill.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skill.py:52)
- schema：[veyrafish_core/skills/_models.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_models.py:1)
- 注册表：[veyrafish_core/skills/_registry.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/_registry.py:18)
- 默认注册：[veyrafish_core/skills/__init__.py](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/veyrafish_core/skills/__init__.py:32)

## 2. 分层

### 核心 skill

这些直接影响主研究链路，优先做完整 spec 和 contract 硬化。

| Skill | 当前状态 | 当前定位 |
|------|----------|----------|
| `query_rewrite` | 已接入搜索前规划 | 搜索意图收敛、工具选择、时间/平台约束 |
| `llm_summarize` | 已接入首轮总结和反思总结 | 证据压缩与增量修订 |
| `evidence_extract` | 已接入 evidence sink | 结构化证据提取、来源绑定、缺口识别 |
| `quality_gate` | 已接入摘要门禁 | 输出质量检查、问题报告、降级护栏 |

### 增强型 skill

这些有价值，但当前不是最核心的 Phase 3 第一批硬化对象。

| Skill | 当前状态 | 当前定位 |
|------|----------|----------|
| `gap_finder` | 已接入反思阶段 | coverage / conflict / recency gap 分析 |
| `sentiment_analysis` | 第二批增强已完成 | 情感判断与统计型增强能力 |

### 适配层 skill

这些主要负责统一接口和 provider 适配，不按“完整知识 skill”规格打磨。

| Skill | 当前状态 | 当前定位 |
|------|----------|----------|
| `web_search` | 适配层稳定化第一轮已完成 | 搜索服务适配层 |

## 3. 为什么不七个一起补全

- 核心 4 个决定主链路质量，投入产出最高。
- `gap_finder` 和 `sentiment_analysis` 适合第二批增强，不会阻塞当前演示链路；当前两者的增强型 contract 已完成第一轮对齐。
- `web_search` 更接近稳定 adapter，不值得用同样成本写成长篇 skill 资产。

## 4. 第一批 spec

- [query_rewrite](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/docs/skills/query_rewrite.md)
- [llm_summarize](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/docs/skills/llm_summarize.md)
- [evidence_extract](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/docs/skills/evidence_extract.md)
- [quality_gate](d:/user/landx/Desktop/computer%20design%20competition/Veyrafish-main/docs/skills/quality_gate.md)

## 5. 第二批建议

- `gap_finder`：补成增强型 skill spec，并接入更清晰的冲突展示。当前已进入第二批增强。
- `sentiment_analysis`：增强型 skill spec 与代码 contract 已完成第一轮对齐；是否接入报告统计或 Forum 辅助判断留到 UI/产品链路阶段再决定。
- `web_search`：provider 归一化、缺配置错误前置、结果清洗与去重已完成第一轮；后续继续盯 provider 差异和真实联调，不做重型 spec。

## 6. 当前残余风险

- 部分 skill 的完整 contract 还主要存在于代码实现里，文档与代码需要持续对齐。
- 还没有独立的 skill 示例集和回放样例目录。
- 还没有前端直接展示 skill 输出的稳定调试界面。
