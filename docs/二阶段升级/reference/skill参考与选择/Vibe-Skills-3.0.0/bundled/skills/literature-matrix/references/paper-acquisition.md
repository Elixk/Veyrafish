# 论文获取策略

## 三级获取策略

### Level 1: 自动获取（无需用户介入）

按优先级依次尝试:

1. **arXiv预印本**
   ```
   WebFetch → https://arxiv.org/abs/{arxiv_id}
   PDF链接: https://arxiv.org/pdf/{arxiv_id}.pdf
   ```

2. **PubMed Central (PMC)**
   ```
   WebFetch → https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}
   PDF链接: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/
   ```

3. **Unpaywall API**
   ```
   WebFetch → https://api.unpaywall.org/v2/{doi}?email=user@example.com
   检查 best_oa_location.url_for_pdf 字段
   ```

4. **Semantic Scholar openAccessPdf**
   ```
   检查论文元数据中的 openAccessPdf.url 字段
   ```

找到开放获取版本后:
- 告知用户下载链接
- 建议保存路径: `./paper_matrix/papers/Paper{序号}_{第一作者}_{年份}.pdf`

### Level 2: 辅助获取（需用户配合）

当论文不是开放获取时，主动告知用户:

```
我需要阅读这篇论文的全文来评估组合可行性:
- 标题: {论文标题}
- DOI: https://doi.org/{doi}
- 建议下载路径: ./paper_matrix/papers/Paper{序号}_{作者}_{年份}.pdf
请通过学校图书馆下载后放入指定路径，我会自动检测并继续分析。
```

检测用户是否已下载:
```
使用 Glob 工具检查 ./paper_matrix/papers/ 目录
```

### Level 3: 替代方案（论文无法获取时）

- 基于摘要 + 引用网络做评估
- 明确标注: "⚠️ 此分析基于摘要，置信度较低。建议获取全文后重新评估。"
- 在Idea卡片中标注哪些结论基于全文、哪些基于摘要

## Semantic Scholar API 常用端点

### 论文搜索
```
GET https://api.semanticscholar.org/graph/v1/paper/search
参数: query, year, fieldsOfStudy, fields, limit, offset
```

### 论文详情
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}
fields: title,abstract,authors,venue,year,citationCount,
        openAccessPdf,externalIds,citations,references,
        citationStyles,fieldsOfStudy
```

### 引用网络
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references
```

### 批量查询
```
POST https://api.semanticscholar.org/graph/v1/paper/batch
Body: {"ids": ["DOI:xxx", "ArXiv:xxx", ...]}
```

## 论文命名规范

```
Paper{序号}_{第一作者姓}_{年份}.pdf
例: Paper01_Zhang_2025.pdf
    Paper15_Smith_2024.pdf
```
