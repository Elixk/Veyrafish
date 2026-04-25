# 溯源与可靠性体系

## 三层溯源标注

所有分析结论必须标注来源层级:

| 层级 | 来源 | 置信度 | 标注格式 |
|------|------|--------|---------|
| L1 元数据 | Semantic Scholar/PubMed API | 高 | `[来源: API元数据]` |
| L2 内容 | 论文摘要或全文 | 中-高 | `[来源: 论文全文, Section X]` 或 `[来源: 摘要]` |
| L3 推理 | AI基于L1/L2的推断 | 低-中 | `[推断: 基于[来源], 置信度: X]` |

## 链接要求

每篇论文必须附带至少一个可访问的链接:
- Semantic Scholar: `https://www.semanticscholar.org/paper/{paper_id}`
- DOI: `https://doi.org/{doi}`
- arXiv: `https://arxiv.org/abs/{arxiv_id}`
- PubMed: `https://pubmed.ncbi.nlm.nih.gov/{pmid}`

优先级: DOI > arXiv > Semantic Scholar > PubMed

## 置信度声明模板

### 高置信度（基于全文分析）
```
✅ 此分析基于论文全文。[来源: 论文全文, Section 3.2]
```

### 中置信度（基于摘要）
```
⚠️ 此分析基于论文摘要，未阅读全文。建议获取全文后验证。
[来源: 摘要]
```

### 低置信度（AI推断）
```
⚠️⚠️ 此为AI推断，基于有限信息。置信度较低，需要用户验证。
[推断: 基于Paper A摘要和Paper B摘要的交叉分析, 置信度: 低]
```

## 证据链格式

在Idea卡片和分析报告中，每条结论都应附带证据链:

```
- [结论] ← 来源: [论文X, Section Y] [链接] (置信度: 高/中/低)
```

示例:
```
- A的attention机制可以解决B的长距离依赖问题
  ← 来源: Paper A, Section 3 "Multi-head Attention"
  ← 来源: Paper B, Section 5.1 "Limitations"
  ← [https://doi.org/10.xxxx] (置信度: 高，基于全文分析)
```
