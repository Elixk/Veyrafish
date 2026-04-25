# Literature Matrix Workflow Phases 完整行为指南

本文档定义了 literature-matrix skill 的6个阶段（Phase 0-5）的完整行为流程、工具使用、checkpoint格式和关键模板。

---

## Phase 0: 初始化

### 触发条件
用户输入 `/literature-matrix` 或相关触发词。

### 行为流程

1. **检查断点**: 检查 `./paper_matrix/checkpoint.json` 是否存在
   - 如果存在，询问用户："检测到上次的分析进度（Phase X, 已完成Y%）。是否继续？"
   - 如果不存在，开始新的分析流程

2. **收集用户信息**（通过 AskUserQuestion 工具）:
   - 研究领域和关键词
   - 时间范围（默认近2年）
   - 论文数量（默认40篇）
   - 论文来源模式：
     - 模式A: 全自动搜索（用户只需指定领域）
     - 模式B: 种子扩展（用户提供5-10篇种子论文）
     - 模式C: 用户提供完整列表
     - 混合模式（推荐）
   - 是否关联现有研究项目（读取 CLAUDE.md）
   - 评估维度权重偏好：
     - 预设方案："理论导向"/"工程导向"/"快速发表导向"
     - 或自定义5个维度的权重

3. **创建工作目录**:
```
./paper_matrix/
├── papers/           # 论文PDF存储
├── analysis/         # 分析结果
├── ideas/            # Idea卡片
├── frameworks/       # 理论框架草案
├── code/             # 代码骨架
└── checkpoint.json   # 进度存档
```

### 工具使用
- `Bash(mkdir)`: 创建目录结构
- `AskUserQuestion`: 收集用户配置信息
- `Read`: 读取 CLAUDE.md（如关联项目）
- `Write`: 保存 checkpoint.json

### Checkpoint 格式
```json
{"phase": 0, "status": "completed", "config": {"keywords": [...], "time_range": "...", "paper_count": 40, "mode": "A/B/C/mixed", "weights": {...}}}
```

---

## Phase 1: 论文收集与确认

### 行为流程

1. **论文搜索**（根据用户选择的来源模式）:

   **模式A - 全自动搜索**:
   - 使用 WebSearch 搜索领域内的顶会/顶刊论文
   - 搜索策略: `[领域关键词] site:arxiv.org OR site:openreview.net [年份]`
   - 补充搜索: `[领域关键词] oral paper [顶会名称] [年份]`
   - 使用 Semantic Scholar API（通过 WebFetch）获取元数据:
     ```
     https://api.semanticscholar.org/graph/v1/paper/search?query=[关键词]&year=[年份范围]&fieldsOfStudy=[领域]&fields=title,authors,venue,year,citationCount,openAccessPdf,externalIds
     ```

   **模式B - 种子扩展**:
   - 基于用户提供的种子论文，通过引用网络扩展
   - Semantic Scholar 引用API: `https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations`
   - 参考文献API: `https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references`
   - 按相关性和影响力排序，扩展到目标数量

   **模式C - 用户提供列表**:
   - 用户提供标题或DOI列表
   - 通过API验证并补充元数据

2. **自动筛选标准**（每篇论文评估）:
   - 开源: GitHub有代码仓库（通过 Papers With Code 或 GitHub 搜索验证）
   - 易理解: 方法描述清晰（基于摘要评估）
   - 时髦: 近期引用增长快（Semantic Scholar citationVelocity 字段）
   - 专业认可: 发表在顶会/顶刊（venue 字段验证）
   - 每个标准标注为: 满足 / 部分满足 / 不满足

3. **展示候选列表**（每篇论文展示格式）:
   ```
   [序号] 标题
   - 作者 | Venue Year | 引用数: N | 近期趋势: 上升/持平/下降
   - GitHub: [链接] (stars数)
   - 核心方法: [一句话摘要]
   - 筛选评估: 开源[Y/N] 易理解[Y/N] 时髦[Y/N] 专业认可[Y/N]
   - 来源: [Semantic Scholar链接] | [DOI链接]
   ```

4. **与用户逐步确认**:
   - 分批展示（每次10篇），用户可以：
     - 确认保留
     - 标记删除（说明原因）
     - 要求替换（skill自动搜索替代论文）
     - 手动添加遗漏的论文
   - 最终确认40篇论文列表

### 工具使用
- `WebSearch`: 论文搜索
- `WebFetch`: Semantic Scholar API调用、论文页面信息获取
- `AskUserQuestion`: 与用户确认论文列表
- `Write`: 保存论文列表到 `./paper_matrix/analysis/paper_list.md`

### Checkpoint 格式
```json
{"phase": 1, "status": "completed", "papers": [{"id": "...", "title": "...", "venue": "...", "year": 2024, "citations": 100, "github": "...", "screening": {...}}]}
```

---

## Phase 2: 矩阵构建与自动筛选

### 行为流程

1. **构建评估矩阵**:
   - 矩阵规模: N x N（N为论文数量，默认40）
   - 去除对角线: N x N - N = N^2 - N 个元素
   - 矩阵对称（A+B = B+A）: 实际独立组合 = (N^2-N)/2 = 780个（N=40时）

2. **5维评估体系**:

   | 维度 | 权重(默认) | 评估方法 |
   |------|-----------|---------|
   | 方法互补性 | 0.25 | A的方法能否解决B的limitation？基于摘要中的method和limitation描述交叉比对 |
   | 数据兼容性 | 0.20 | A和B的数据类型/格式是否可共用？基于实验设置描述 |
   | 理论统一性 | 0.20 | 是否存在自然的统一框架？基于数学形式化的结构相似度 |
   | 创新增量 | 0.20 | 组合后是否1+1>2？基于各自contribution和领域gap |
   | 实现可行性 | 0.15 | 代码开源程度、接口兼容性、集成难度 |

   **预设权重方案**:
   - 理论导向: 互补0.20, 数据0.15, 理论0.30, 创新0.25, 实现0.10
   - 工程导向: 互补0.25, 数据0.25, 理论0.10, 创新0.15, 实现0.25
   - 快速发表导向: 互补0.30, 数据0.20, 理论0.15, 创新0.20, 实现0.15

3. **3层筛选策略**:

   **第一层: 规则过滤（快速排除）**
   - 排除同一作者组的论文组合（基于作者列表交集）
   - 排除完全相同子领域的论文（增量太小）
   - 排除已有人做过的组合（通过引用关系检测：如果A引用了B或B引用了A，可能已有人探索过）
   - 预计排除30-50%的组合

   **第二层: 语义评估（AI评估）**
   - 对剩余组合，基于两篇论文的摘要进行5维评分
   - 每个维度1-5分，加权求和得到综合分
   - 评估 prompt 模板:
   ```
   论文A: [标题] - [摘要]
   论文B: [标题] - [摘要]

   请评估将A和B的方法组合的可行性:
   1. 方法互补性(1-5): A的方法能否解决B的limitation？反之呢？
   2. 数据兼容性(1-5): A和B的数据类型是否可以共用或转换？
   3. 理论统一性(1-5): 是否存在自然的统一数学框架？
   4. 创新增量(1-5): 组合后能否产生新的insight？
   5. 实现可行性(1-5): 代码集成的难度如何？

   对每个维度，给出评分和一句话理由。
   ```

   **第三层: 排序输出**
   - 按综合分排序，输出 top-30

4. **可视化输出**:
   - 生成热力图矩阵（使用 matplotlib/seaborn，通过代码执行）
   - 高分组合高亮标注
   - 保存为 `./paper_matrix/analysis/matrix_heatmap.png`

5. **与用户讨论 top-30**:
   - 展示排名表，每个组合附带:
     - 5维评分详情
     - 评估理由（附溯源）
     - 综合分和排名
   - 用户可以:
     - 调整评分（基于领域知识）
     - 标记感兴趣/不感兴趣
     - 要求对某个组合做更深入分析
   - 最终缩小到15-20个候选

### 工具使用
- `Task`(subagent): 并行评估多个组合（提高效率）
- `Write`: 保存评分矩阵到 `./paper_matrix/analysis/matrix_scores.csv`
- `Bash`(python): 生成热力图
- `AskUserQuestion`: 与用户讨论筛选结果

### Checkpoint 格式
```json
{"phase": 2, "status": "completed", "matrix": {"size": 40, "evaluated": 780, "filtered": 390}, "top_candidates": [{"paper_a": "...", "paper_b": "...", "scores": {...}, "total": 4.2}]}
```

---

## Phase 3: 论文获取与深度分析

### 论文获取策略（3个层级）

对 Phase 2 筛选出的 top-15~20 候选组合涉及的论文，主动获取全文:

**Level 1 - 自动获取（无需用户介入）**:
```
获取策略优先级:
1. 检查 arXiv 版本: WebFetch -> https://arxiv.org/abs/{arxiv_id}
2. 检查 PubMed Central: WebFetch -> https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}
3. 检查 Unpaywall: WebFetch -> https://api.unpaywall.org/v2/{doi}?email=user@example.com
4. 检查 Semantic Scholar openAccessPdf 字段
```
- 找到开放获取版本后，告知用户并建议下载到 `./paper_matrix/papers/`
- 命名格式: `Paper{序号}_{第一作者}_{年份}.pdf`

**Level 2 - 辅助获取（需用户配合）**:
- 如果论文不是开放获取，主动告知用户:
  "我需要阅读这篇论文的全文来评估组合可行性:
   - 标题: [论文标题]
   - DOI: [DOI链接]
   - 建议下载路径: `./paper_matrix/papers/Paper{序号}_{作者}_{年份}.pdf`
   请通过学校图书馆下载后放入指定路径，我会自动检测并继续分析。"

**Level 3 - 替代方案（论文无法获取时）**:
- 基于摘要+引用网络做评估
- 明确标注: "此分析基于摘要，置信度较低。建议获取全文后重新评估。"

### 全文结构化提取

对每篇获取到的论文PDF，使用 Read 工具读取并提取:

```
论文结构化摘要:
+-- 基本信息: 标题、作者、venue、年份、DOI
+-- 核心方法:
|   +-- 方法名称和类别
|   +-- 数学形式化描述（关键公式）
|   +-- 算法流程
|   +-- 关键假设和约束条件
+-- 创新点:
|   +-- 与前人工作的明确差异
|   +-- 声称的贡献（contribution list）
+-- Limitation:
|   +-- 论文明确写出的limitation
|   +-- 隐含的limitation（从实验设置推断）
+-- 实验设置:
|   +-- 数据集类型和规模
|   +-- 评估指标
|   +-- 基线方法
+-- 代码信息:
|   +-- GitHub仓库链接
|   +-- 主要编程语言和框架
|   +-- 核心接口和API
+-- 可扩展方向:
    +-- Future Work部分的建议
    +-- 从limitation推断的改进方向
```

保存到 `./paper_matrix/analysis/paper_summaries/Paper{序号}_summary.md`

### 组合深度分析（交叉比对）

对每个候选组合(A, B)，基于全文分析进行交叉比对:

```
组合分析报告:
+-- 方法互补性分析:
|   +-- A的方法能否直接解决B的limitation？具体怎么做？
|   +-- B的方法能否增强A的某个模块？
|   +-- 证据: [引用论文具体章节]
+-- 数据兼容性分析:
|   +-- A和B的数据类型是否可以共用？
|   +-- 是否需要数据转换？转换方案是什么？
|   +-- 证据: [引用论文实验设置部分]
+-- 理论统一性分析:
|   +-- A和B的数学形式化有哪些共同结构？
|   +-- 是否存在自然的统一框架？
|   +-- 建议的统一方向（凸组合/变分推断/信息论等）
|   +-- 证据: [引用论文方法部分的公式]
+-- 创新增量分析:
|   +-- 组合后解决了什么新问题？
|   +-- 是否存在1+1>2的效果？
|   +-- 证据: [引用领域gap和论文contribution]
+-- 实现可行性分析:
|   +-- 代码集成的具体方案
|   +-- 预计修改量和难度
|   +-- 证据: [引用GitHub仓库结构]
+-- 综合评估:
    +-- 更新后的5维评分（基于全文，比Phase 2更准确）
    +-- 综合推荐度: 1-5星
    +-- 置信度: 高/中/低（标注依据来源层级）
```

### Idea 卡片模板

对每个通过深度分析的候选组合，生成 Idea 卡片:

```markdown
# Idea #[序号]: [简短标题]

## 来源论文
- Paper A: [标题] | [venue year] | [Semantic Scholar链接]
- Paper B: [标题] | [venue year] | [Semantic Scholar链接]

## 动机
为什么要组合A和B？解决什么问题？
[具体描述，引用论文中的evidence]

## 方法概述
组合的具体方式是什么？
- 组合类型: 并联/串联/嵌套
- 核心思路: [一段话描述]
- 关键公式: [如果适用]

## 预期贡献
1. [贡献1]
2. [贡献2]
3. [贡献3]

## 理论框架方向
- 建议的统一框架: [描述]
- A作为特例: 当[条件]时退化为A
- B作为特例: 当[条件]时退化为B
- aA+(1-a)B的具体形式: [如果适用]

## Non-trivial论证
为什么这不是简单拼接？
- [论证角度和具体理由]

## 可行性评估
| 维度 | 评分 | 理由 |
|------|------|------|
| 方法互补性 | X/5 | [理由] |
| 数据兼容性 | X/5 | [理由] |
| 理论统一性 | X/5 | [理由] |
| 创新增量 | X/5 | [理由] |
| 实现可行性 | X/5 | [理由] |
| 综合 | X/5 | |

## 与用户项目的关联（如已关联）
- 可用数据: [描述]
- 落地方案: [描述]

## 证据链
- [结论1] <- 来源: [论文A, Section X] [链接] (置信度: 高)
- [结论2] <- 来源: [论文B, Abstract] [链接] (置信度: 中)
- [推断1] <- 来源: 基于摘要推断 (置信度: 低，建议阅读全文验证)
```

保存到 `./paper_matrix/ideas/idea_{序号}.md`

### 与用户讨论
- 逐一展示 Idea 卡片，与用户深入讨论
- 使用苏格拉底式提问引导用户思考
- 记录用户的反馈和偏好
- 最终选定3-5个最有潜力的 idea 进入 Phase 4

### 工具使用
- `WebFetch`: 获取论文开放获取版本
- `Read`: 读取论文PDF全文
- `Write`: 保存结构化摘要和 Idea 卡片
- `Task`(subagent): 并行分析多篇论文
- `AskUserQuestion`: 与用户讨论 Idea 卡片

### Checkpoint 格式
```json
{"phase": 3, "status": "completed", "selected_ideas": [1, 3, 7], "idea_cards": ["idea_1.md", "idea_3.md", "idea_7.md"]}
```

---

## Phase 4: 理论框架构建

### 组合类型识别与框架选择

首先识别每个选定 idea 的组合类型:

**并联型（A和B处理不同方面然后融合）**:
- 统一形式: `f(x) = a * g_A(x) + (1-a) * g_B(x), a in [0,1]`
- 当 a=1 时退化为A，a=0 时退化为B
- 扩展: 使用可学习的 a（注意力机制）或 Dirichlet 分布

**串联型（A的输出是B的输入）**:
- 统一形式: `f(x) = g_B(g_A(x))`
- 框架: 定义一个通用的变换管道 `T = T_n ... T_2 T_1`
- A和B是管道中的特定变换

**嵌套型（B嵌入A的某个模块中）**:
- 统一形式: `f(x) = g_A(x; module=g_B)`
- 框架: 定义一个可插拔的模块化架构
- A是主框架，B是可替换模块

### 自动生成理论框架草案

对每个选定的 idea，自动生成:

1. **统一框架定义**:
   - 定义一个通用的问题形式化
   - 定义通用的求解框架
   - 明确框架的参数空间

2. **特例推导**:
   - 证明当参数取特定值时，框架退化为A
   - 证明当参数取另一特定值时，框架退化为B
   - 如果有C，同样推导

3. **aA+(1-a)B 的具体化**:
   - 明确 a 的物理/数学含义
   - 分析 a 的最优取值（理论分析或实验建议）
   - 讨论 a=0.5 附近效果更好的理论解释:
     - 信息论角度: 最大化互信息
     - 正则化角度: 最优偏差-方差权衡
     - 博弈论角度: 纳什均衡

4. **Non-trivial 论证**:
   从内置模板库中选择最适合的论证策略:
   - 理论 non-trivial: 存在交互项 `a(1-a) * h(A,B)`
   - 实验 non-trivial: 性能曲线在 `a in (0,1)` 时超过线性插值
   - 问题 non-trivial: 组合解决了A和B各自无法解决的问题
   - 计算 non-trivial: 需要新的优化算法

5. **扩展到 A+B+C**:
   - 自动从 Phase 2 的矩阵中寻找与 A+B 互补的第三篇论文C
   - 扩展框架: `a*A + b*B + (1-a-b)*C`（单纯形约束）
   - 或使用注意力权重: `softmax(w) * [A, B, C]`

### 输出格式（理论框架草案模板）

```markdown
# 理论框架草案: [Idea标题]

## 1. 问题形式化
[通用问题定义]

## 2. 统一框架
[框架定义，包含参数空间]

## 3. 特例推导
### 3.1 退化为方法A
当[参数条件]时，框架退化为A: [推导过程]

### 3.2 退化为方法B
当[参数条件]时，框架退化为B: [推导过程]

## 4. 组合形式
f(x) = a * g_A(x) + (1-a) * g_B(x)
- a的含义: [解释]
- 最优a的理论分析: [分析]

## 5. Non-trivial论证
[选择的论证策略和具体推导]

## 6. 扩展方向
[A+B+C的扩展方案]
```

保存到 `./paper_matrix/frameworks/framework_{idea序号}.md`

### 与用户讨论
- 展示框架草案，逐步讨论每个部分
- 挑战式提问: "reviewer可能会从哪个角度攻击这个框架？"
- 根据用户反馈迭代修改

### 工具使用
- `Write`: 保存理论框架草案
- `Bash`(python/sympy): 符号推导验证
- `AskUserQuestion`: 与用户讨论框架

### Checkpoint 格式
```json
{"phase": 4, "status": "completed", "frameworks": [{"idea_id": 1, "type": "parallel", "file": "framework_1.md"}]}
```

---

## Phase 5: 代码骨架生成

### 行为流程

1. **分析代码集成方案**:
   - 检查 Paper A 和 Paper B 的 GitHub 仓库
   - 分析代码结构、编程语言、依赖库
   - 确定集成策略（fork+修改 / 从头实现 / 包装调用）

2. **生成代码骨架**:

```python
# base_framework.py - 统一框架基类
class UnifiedFramework:
    """统一框架: 将方法A和方法B统一在同一个框架下"""

    def __init__(self, alpha=0.5):
        self.alpha = alpha  # 组合系数

    def method_a(self, x):
        """方法A的实现（当alpha=1时的特例）"""
        raise NotImplementedError

    def method_b(self, x):
        """方法B的实现（当alpha=0时的特例）"""
        raise NotImplementedError

    def combine(self, x):
        """aA + (1-a)B 的组合"""
        return self.alpha * self.method_a(x) + (1 - self.alpha) * self.method_b(x)

    def find_optimal_alpha(self, data, metric):
        """网格搜索最优alpha"""
        # 实验脚本: 在[0, 0.1, 0.2, ..., 1.0]上搜索
        pass
```

3. **生成实验脚本**:
   - alpha 调参实验（网格搜索 + 可视化）
   - 与A和B的单独性能对比
   - 消融实验（验证每个组件的贡献）

4. **项目关联代码**（如果用户选择了关联项目）:
   - 生成数据加载和预处理代码
   - 适配用户现有数据格式
   - 生成端到端的实验 pipeline

### 输出文件结构
```
./paper_matrix/code/
+-- base_framework.py    # 统一框架基类
+-- method_a.py          # A的实现（或调用A的代码库）
+-- method_b.py          # B的实现（或调用B的代码库）
+-- combination.py       # aA+(1-a)B组合实现
+-- experiment.py        # 实验脚本（alpha调参、对比、消融）
+-- data_loader.py       # 数据加载（如关联项目）
+-- visualize.py         # 结果可视化
+-- requirements.txt     # 依赖列表
```

### 工具使用
- `WebFetch`: 获取 GitHub 仓库信息和代码结构
- `Write`: 生成代码文件
- `Bash`(python): 验证代码可运行性
- `AskUserQuestion`: 确认代码方案

### Checkpoint 格式
```json
{"phase": 5, "status": "completed", "code_files": ["base_framework.py", "method_a.py", "method_b.py", "combination.py", "experiment.py", "data_loader.py", "visualize.py", "requirements.txt"]}
```

---

## 跨阶段说明

### Checkpoint 系统
每个 Phase 完成后自动保存 `./paper_matrix/checkpoint.json`，包含:
- 当前阶段编号和状态
- 该阶段的核心输出数据
- 用户配置和偏好

断点恢复时，读取 checkpoint 并从上次中断处继续。

### 工具使用总览

| Phase | 主要工具 | 用途 |
|-------|---------|------|
| 0 | Bash, AskUserQuestion, Write | 初始化 |
| 1 | WebSearch, WebFetch, AskUserQuestion | 论文搜索与确认 |
| 2 | Task(subagent), Bash(python), Write | 矩阵评估与可视化 |
| 3 | WebFetch, Read, Write, Task(subagent) | 全文分析与Idea生成 |
| 4 | Write, Bash(python/sympy), AskUserQuestion | 理论框架构建 |
| 5 | WebFetch, Write, Bash(python) | 代码骨架生成 |

### 用户交互节点
- Phase 0: 收集配置
- Phase 1: 确认论文列表（分批，每次10篇）
- Phase 2: 讨论 top-30 组合，缩小到15-20个
- Phase 3: 讨论 Idea 卡片，选定3-5个
- Phase 4: 讨论理论框架，迭代修改
- Phase 5: 确认代码方案
