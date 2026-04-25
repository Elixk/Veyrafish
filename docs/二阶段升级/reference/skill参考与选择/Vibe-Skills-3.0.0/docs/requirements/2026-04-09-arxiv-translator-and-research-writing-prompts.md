# Requirement: arxiv-translator Skill 与 awesome-ai-research-writing Prompts 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-09-arxiv-translator-and-research-writing-prompts |
| 状态 | frozen |
| 创建日期 | 2026-04-09 |
| 作者 | AI Agent (governed) |

## 1. 背景

用户提供了两个上游 GitHub 仓库：

1. **awesome-ai-research-writing** (https://github.com/Leey21/awesome-ai-research-writing)
   - 17.5k stars，专注于学术论文写作的 prompt 集合
   - 内容：17 个精心设计的 prompt 模板（中转英、英转中、润色、扩写、缩写、去 AI 味等）
   - 结构：仅 `README.md` + `images/`，**无 SKILL.md**
   - 判定：**Prompt 资产**，应纳入 `prompt-library`

2. **arxiv-translator** (https://github.com/Leey21/arxiv-translator)
   - 123 stars，arXiv 论文 LaTeX 源码翻译与编译工具
   - 结构：`arxiv-translator/SKILL.md` + `scripts/` + `references/`
   - 判定：**标准 Skill**，应完整镜像并接入 canonical 路由

## 2. 目标

### 2.1 Skill 接入（arxiv-translator）

- 完整镜像到 `bundled/skills/arxiv-translator/`
- 配置 canonical 路由（pack-manifest、skill-keyword-index、skill-routing-rules）
- 运行脚本级验证
- 通过 `vgo_cli route` 测试确认路由命中

### 2.2 Prompt 接入（awesome-ai-research-writing）

将以下 17 个 prompt 按分类纳入 `prompt-library`：

| Prompt | 分类 | 原标题 |
|--------|------|--------|
| cn-to-en | translation | 中转英 |
| en-to-cn | translation | 英转中 |
| cn-to-cn | writing | 中转中 |
| compress | writing | 缩写 |
| expand | writing | 扩写 |
| polish-en | writing | 表达润色（英文论文） |
| polish-cn | writing | 表达润色（中文论文） |
| logic-check | review | 逻辑检查 |
| de-ai-latex-en | writing | 去 AI 味（LaTeX 英文） |
| de-ai-word-cn | writing | 去 AI 味（Word 中文） |
| paper-architecture-diagram | writing | 论文架构图 |
| experiment-chart-recommend | writing | 实验绘图推荐 |
| figure-caption | writing | 生成图的标题 |
| table-caption | writing | 生成表的标题 |
| experiment-analysis | writing | 实验分析 |
| reviewer-perspective | review | 论文整体以 Reviewer 视角进行审视 |
| model-selection | research | 模型选择 |

## 3. 验收标准

### Skill 验收

- [x] `bundled/skills/arxiv-translator/SKILL.md` 存在且 UTF-8 编码
- [x] `scripts/` 目录完整（download.py, inspect_tex.py, compile.py, cleanup.py）
- [x] `references/compile-errors.md` 存在
- [x] `requirements.txt` 存在
- [x] `config/pack-manifest.json` 已更新
- [x] `config/skill-keyword-index.json` 已更新
- [x] `config/skill-routing-rules.json` 已更新
- [x] `python bundled/skills/arxiv-translator/scripts/download.py --help` 可执行
- [x] `vgo_cli route` 测试命中正确（confidence: 0.7）

### Prompt 验收

- [x] 17 个 prompt 文件存在于 `bundled/skills/prompt-library/prompts/` 对应分类目录
- [x] 每个 prompt 有完整元数据（id, title, category, tags, use_when）
- [x] `index.json` 已注册全部 17 个 prompt
- [x] 文档已更新说明来源

## 4. 约束

- Prompt 内容保持原样，仅做结构化搬运
- Skill 按照 Vibe-Skills 标准 canonical 路由接入
- 更新 `skills管理和安装指南.md` 做完整记录

## 5. 来源信息

- awesome-ai-research-writing: MIT License（推断）
- arxiv-translator: MIT License（推断）
- 集成日期：2026-04-09
