# Vibe-Skills-3.0.0 项目全景概览

## 一、项目是什么

**Vibe-Skills-3.0.0** 是一个**跨 IDE/CLI 的 AI Agent 技能管理系统**，核心目标是为主流 AI 编码工具提供统一的技能包（Skill Pack）——让 AI 助手拥有领域专业知识、标准化工作流和可复用工具。

### 支持的 IDE / CLI 适配器


| 适配器                | 状态   | 安装目标目录                 |
| ------------------ | ---- | ---------------------- |
| **Codex** (OpenAI) | 正式支持 | `~/.codex/`            |
| **Claude Code**    | 正式支持 | `~/.claude/`           |
| **Cursor**         | 预览   | `~/.cursor/`           |
| **Windsurf**       | 预览   | `~/.codeium/windsurf/` |
| **OpenClaw**       | 预览   | `~/.openclaw/`         |
| **OpenCode**       | 预览   | `~/.config/opencode/`  |


---

## 二、项目结构

```
Vibe-Skills-3.0.0/
├── adapters/          # 各 IDE/CLI 的适配器配置
├── agents/            # Agent 模板（planner, debugger, reviewer 等）
├── apps/vgo-cli/      # VGO CLI 工具（Python）
├── bundled/skills/    # ★ 350+ 个捆绑技能（核心资产，含 Anthropic 官方技能）
│   ├── .system/       #   系统级元技能（skill-creator, skill-installer）
│   ├── document-skills/ # 文档处理技能组
│   └── <350+ 技能目录>/
├── commands/          # 命令定义（vibe, vibe-implement, vibe-review）
├── config/            # 路由配置、技能别名、能力目录
├── core/              # 主机中立的技能合同层（首批 8 个）
├── docs/              # 文档（安装、架构、治理、计划等）
├── packages/          # 核心包（runtime-core, installer-core, skill-catalog 等）
├── protocols/         # 6 大协议（runtime, think, do, review, retro, team）
├── schemas/           # JSON Schema（技能合同验证）
├── scripts/           # 脚本（路由、验证门、安装、构建）
└── tests/             # 测试套件
```

---

## 三、全部技能清单（按领域分类）

项目内含 **350+ 个捆绑技能**（含 Anthropic 官方技能与新增社区技能）+ 根目录 1 个 `vibe` 主技能。以下按领域分类：

### 1. 治理核心（Governed Core）


| 技能                     | 说明                    |
| ---------------------- | --------------------- |
| `vibe`                 | VCO 受治理运行时——整个系统的核心入口 |
| `brainstorming`        | 需求澄清与设计头脑风暴           |
| `writing-plans`        | 编写执行计划                |
| `systematic-debugging` | 系统化调试流程               |
| `tdd-guide`            | 测试驱动开发指南              |


### 2. 兼容性支持层（Compat Support）

`cancel-ralph`, `dialectic`, `local-vco-roles`, `ralph-loop`, `spec-kit-vibe-compat`, `subagent-driven-development`, `superclaude-framework-compat`, `think-harder`, `pua` *(Community)*

### 3. 系统元技能（.system）


| 技能                | 说明                    |
| ----------------- | --------------------- |
| `skill-creator`   | 创建新技能的完整指南（含脚手架、验证脚本） |
| `skill-installer` | 从精选列表或 GitHub 安装技能    |


### 4. 代码开发与审查

`code-review`, `code-review-excellence`, `code-reviewer`, `reviewing-code`, `receiving-code-review`, `requesting-code-review`, `coding-tutor`, `build-error-resolver`, `error-resolver`, `security-best-practices`, `security-reviewer`, `security-threat-model`, `security-ownership-map`, `verification-before-completion`, `verification-quality-assurance`, `commit-with-reflection`, `gh-address-comments`, `gh-fix-ci`, `langsmith-fetch` *(Community)*, `git-workflow` *(Community)*, `bug-detective` *(Community)*, `verification-loop` *(Community)*, `daily-coding` *(Community)*, `command-development` *(Community)*, `hook-development` *(Community)*

### 5. AI/ML 与数据科学

`senior-ml-engineer`, `senior-data-scientist`, `senior-computer-vision`, `senior-prompt-engineer`, `scikit-learn`, `pytorch-lightning`, `transformers`, `deepchem`, `sparse-autoencoder-training`, `transformer-lens-interpretability`, `training-machine-learning-models`, `evaluating-machine-learning-models`, `evaluating-llms-harness`, `explaining-machine-learning-models`, `ml-data-leakage-guard`, `ml-pipeline-workflow`, `gradient-methods`, `embedding-strategies`, `feature-importance-analyzer`, `hypothesis-testing`, `hypothesis-generation`, `running-clustering-algorithms`, `performing-regression-analysis`, `performing-causal-analysis`, `stable-baselines3`, `pufferlib`, `weights-and-biases`, `tensorboard`, `unsloth`, `timesfm-forecasting`, `algorithm-engineer-dualstack` *(Community)*, `architecture-design` *(Community)*, `kaggle-learner` *(Community)*

### 6. 数据处理与分析

`exploratory-data-analysis`, `data-quality-checker`, `data-quality-frameworks`, `data-normalization-tool`, `data-storytelling`, `data-artist`, `preprocessing-data-with-automated-pipelines`, `engineering-features-for-machine-learning`, `splitting-datasets`, `detecting-data-anomalies`, `anomaly-detector`, `correlation-analyzer`, `confusion-matrix-generator`, `regression-analysis-helper`, `statistical-analysis`, `statistics-math`, `excel-analysis`, `polars`, `dask`, `vaex`, `results-analysis` *(Community)*

### 7. 可视化

`matplotlib`, `plotly`, `seaborn`, `datavis`, `creating-data-visualizations`, `visualization-best-practices`, `g2-legend-expert`, `scientific-visualization`, `infographics`

### 8. 文档处理

`document-skills/`（含子技能 `docx`, `pdf`, `pptx`）, `doc`, `docx`, `docx-comment-reply`, `xlsx`, `spreadsheet`, `markitdown`, `pdf`, `anthropic-pptx` *(Anthropic)*, `doc-coauthoring` *(Anthropic)*

### 9. 科学研究 / 生物信息学

`biopython`, `scanpy`, `pydeseq2`, `alphafold-database`, `chembl-database`, `clinvar-database`, `cosmic-database`, `drugbank-database`, `ensembl-database`, `gene-database`, `geo-database`, `gwas-database`, `hmdb-database`, `kegg-database`, `openalex-database`, `opentargets-database`, `pdb-database`, `pubchem-database`, `pubmed-database`, `reactome-database`, `string-database`, `uniprot-database`, `zinc-database`, `rdkit`, `cobrapy`, `pymatgen`, `medchem`, `molfeat`, `datamol`, `rowan`, `gget`, `scikit-bio`, `scikit-survival`, `pyopenms`, `pysam`, `anndata`, `lamindb`, `cellxgene-census`, `scvi-tools`, `bioservices`, `clinpgx-database`, `metabolomics-workbench-database`, `arboreto`, `deeptools`, `esm`, `diffdock`, `flowio`, `histolab`, `matchms`, `neurokit2`, `neuropixels-analysis`, `pathml`, `pydicom`, `pyhealth`, `pytdc`, `torchdrug`, `umap-learn`

### 10. 科学写作与出版

`scientific-writing`, `scientific-reporting`, `scientific-schematics`, `scientific-slides`, `scientific-brainstorming`, `scientific-critical-thinking`, `scientific-data-preprocessing`, `scholarly-publishing`, `manuscript-as-code`, `latex-posters`, `latex-submission-pipeline`, `literature-review`, `literature-matrix`, `citation-management`, `peer-review`, `submission-checklist`, `venue-templates`, `arxiv-translator` *(Community)*, `ml-paper-writing` *(Community)*, `citation-verification` *(Community)*, `writing-anti-ai` *(Community)*, `paper-self-review` *(Community)*, `review-response` *(Community)*, `results-report` *(Community)*, `post-acceptance` *(Community)*, `publication-chart-skill` *(Community)*, `latex-conference-template-organizer` *(Community)*

### 11. AIOS 角色系列（AI 操作系统代理）

`aios-analyst`, `aios-architect`, `aios-data-engineer`, `aios-dev`, `aios-devops`, `aios-master`, `aios-pm`, `aios-po`, `aios-qa`, `aios-sm`, `aios-squad-creator`, `aios-ux-design-expert`

### 12. 数学与逻辑

`math`, `math-tools`, `math-model-selector`, `mathematical-logic-expert`, `propositional-logic`, `sympy`, `statsmodels`, `pymc`, `pymc-bayesian-modeling`

### 13. 研究与检索

`comprehensive-research-agent`, `webthinker-deep-research`, `research-lookup`, `research-grants`, `bgpt-paper-search`, `flashrag-evidence`, `perplexity-search`, `documentation-lookup`, `skill-lookup`, `prompt-lookup`, `prompt-library`, `openai-docs`, `openai-knowledge`, `ai-search-hub` *(Community)*, `research-ideation` *(Community)*, `daily-paper-generator` *(Community)*

### 14. 前端/设计/部署

`figma`, `figma-implement-design`, `playwright`, `netlify-deploy`, `vercel-deploy`, `ux-researcher-designer`, `theme-factory`, `frontend-design` *(Anthropic)*, `canvas-design` *(Anthropic)*, `web-artifacts-builder` *(Anthropic)*, `ui-ux-pro-max` *(Community)*, `web-design-reviewer` *(Community)*

### 15. 多媒体

`generate-image`, `imagegen`, `screenshot`, `speech`, `transcribe`, `video-studio`, `algorithmic-art` *(Anthropic，已存在)*

### 16. 量子计算

`qiskit`, `pennylane`, `cirq`, `qutip`

### 17. 模拟与工程

`simpy`, `fluidsim`, `pymatgen`, `astropy`, `geomaster`, `geopandas`

### 18. 实验室/平台集成

`benchling-integration`, `ginkgo-cloud-lab`, `latchbio-integration`, `labarchive-integration`, `dnanexus-integration`, `omero-integration`, `opentrons-integration`, `protocolsio-integration`

### 19. 金融与经济

`alpha-vantage`, `fred-economic-data`, `usfiscaldata`, `hedgefundmonitor`, `denario`, `edgartools`, `market-research-reports`

### 20. 规划与知识管理

`create-plan`, `planning-with-files`, `writing-plans`, `knowledge-steward`, `digital-brain`, `structured-content-storage`, `deepagent-memory-fold`, `deepagent-toolchain-plan`, `context-fundamentals`, `context-hunter`, `tailored-resume-generator` *(Community)*, `obsidian-project-memory` *(Community)*, `obsidian-project-bootstrap` *(Community)*, `obsidian-project-lifecycle` *(Community)*, `obsidian-research-log` *(Community)*, `obsidian-experiment-log` *(Community)*, `obsidian-literature-workflow` *(Community)*, `obsidian-synthesis-map` *(Community)*, `obsidian-link-graph` *(Community)*, `obsidian-bases` *(Community)*, `obsidian-cli` *(Community)*, `obsidian-markdown` *(Community)*, `zotero-obsidian-bridge` *(Community)*, `json-canvas` *(Community)*, `skill-development` *(Community)*, `skill-improver` *(Community)*, `skill-quality-reviewer` *(Community)*, `agent-identifier` *(Community)*, `defuddle` *(Community)*

### 21. 其他工具与实用技能

`file-organizer`, `smart-file-writer`, `mcp-integration`, `markdown-mermaid-writing`, `sentry`, `modal`, `modal-labs`, `skypilot-multi-cloud-orchestration`, `scrapling`, `zarr-python`, `networkx`, `torch-geometric`, `xan`, `deslop`, `hive-mind-advanced`, `windows-hook-debugging`, `node-zombie-guardian`, `clinical-decision-support`, `clinical-reports`, `treatment-plans`, `iso-13485-certification`, `claude-api` *(Anthropic)*, `mcp-builder` *(Anthropic)*, `slack-gif-creator` *(Anthropic)*, `webapp-testing` *(Anthropic)*, `brand-guidelines` *(Anthropic)*, `internal-comms` *(Anthropic)*, `ssh-skill` *(Community)*, `invoice-organizer` *(Community)*, `meeting-insights-analyzer` *(Community)*, `uv-package-manager` *(Community)*, `plugin-structure` *(Community)*

---

## 四、如何添加自己的技能

有 **三种途径** 可以添加自定义技能：

### 途径 A：使用 `skill-creator` 脚手架工具（推荐）

**步骤 1：初始化技能目录**

```bash
# 进入项目根目录的脚手架脚本
python bundled/skills/.system/skill-creator/scripts/init_skill.py <你的技能名> \
  --path <输出目录> \
  --resources scripts,references,assets \
  --interface display_name="我的技能" short_description="一句话说明"
```

示例：

```bash
python bundled/skills/.system/skill-creator/scripts/init_skill.py my-custom-skill \
  --path bundled/skills \
  --resources scripts,references
```

这会自动生成：

```
my-custom-skill/
├── SKILL.md          # 带有 YAML frontmatter 的模板
├── agents/
│   └── openai.yaml   # UI 元数据
├── scripts/          # 可执行脚本（如果指定了 --resources scripts）
└── references/       # 参考文档（如果指定了 --resources references）
```

**步骤 2：编写 SKILL.md**

SKILL.md 是技能的核心文件，包含两个关键部分：

```yaml
---
name: my-custom-skill
description: |
  你的技能描述。这是触发机制——AI 通过这段描述判断何时使用该技能。
  包含：(1) 做什么 (2) 何时触发 (3) 触发上下文
---
```

正文部分用 Markdown 写具体的指令和工作流：

```markdown
# My Custom Skill

## 核心流程

1. 步骤一...
2. 步骤二...

## 脚本

- `scripts/my-tool.py` - 用于 xxx 的确定性脚本

## 参考

- 详细 API 说明见 [references/api.md](references/api.md)
```

**步骤 3：添加资源文件（可选）**

- `scripts/`：需要确定性执行的 Python/Bash 脚本
- `references/`：领域知识、API 文档、模式说明等
- `assets/`：模板文件、图标、字体等输出资源

**步骤 4：验证技能**

```bash
python bundled/skills/.system/skill-creator/scripts/quick_validate.py <你的技能目录路径>
```

**步骤 5：迭代改进**

在实际使用中测试技能效果，根据 AI 的表现调整 SKILL.md 和资源文件。

### 途径 B：手动创建（最小结构）

只需一个文件夹和一个 `SKILL.md`：

```
my-skill/
└── SKILL.md
```

`SKILL.md` 最低要求：

```yaml
---
name: my-skill
description: 技能描述和触发条件
---

# My Skill

具体指令内容...
```

### 途径 C：从 GitHub 安装已有技能

```bash
# 列出可安装的精选技能
python bundled/skills/.system/skill-installer/scripts/list-skills.py

# 从 GitHub 安装
python bundled/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo owner/repo --path path/to/skill

# 通过 URL 安装
python bundled/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/owner/repo/tree/main/skills/my-skill
```

### 技能编写的关键原则

1. **精简至上**：上下文窗口是公共资源，只写 AI 本身不知道的信息
2. **渐进式披露**：SKILL.md 保持 500 行以内，详细内容拆分到 `references/` 目录
3. **frontmatter 的 `description` 是触发关键**：AI 通过它判断是否激活该技能
4. **不要写多余文档**：不需要 README.md、CHANGELOG.md 等辅助文件
5. **命名规范**：使用 kebab-case（如 `my-custom-skill`），小写字母 + 数字 + 连字符

### 在 Vibe 治理体系中注册自定义技能

如果要将技能接入 Vibe 的路由系统，还需要参考 `docs/install/custom-workflow-onboarding.md`，包括：

- 在 `config/custom-skills.json` 或 `config/custom-workflows.json` 中注册
- 配置 `trigger_mode` 和 `priority`
- 遵守单一运行时/单一路由器治理规则

### 延伸阅读

如果你希望 AI / Agent 不只是"把 skill 放进来"，而是按仓库当前的 canonical 路由机制把 skill 真正接入为"可调用状态"，建议继续阅读：

- `docs/install/agent-skill-onboarding-and-callability-guide.md`：面向 AI / Agent 的新增 skill 接入与可调用保障手册，包含 canonical / custom 接入、复杂 skill 建模、权重判断、路由验证与 `check --deep` 验收
- `skill智能调用与复杂Skill接入指南.md`：补充说明 Vibe 如何智能调用 skill，以及多子技能、命令、Hook、Agent 体系的接入理解

---

## 五、Anthropic 官方技能集成记录

以下技能从 [anthropics/skills](https://github.com/anthropics/skills) 仓库集成，来源于 Anthropic 官方的 Claude Agent Skills 公开项目。

### 新增技能（11 个）


| 技能                      | 说明                                   | 包含资源                                                                             |
| ----------------------- | ------------------------------------ | -------------------------------------------------------------------------------- |
| `brand-guidelines`      | 应用 Anthropic 官方品牌色彩和排版到各类产出物         | SKILL.md, LICENSE.txt                                                            |
| `canvas-design`         | 使用设计哲学创建精美的 .png 和 .pdf 视觉作品         | SKILL.md, canvas-fonts/ (30+ 字体文件)                                               |
| `claude-api`            | Claude API / Anthropic SDK 多语言快速上手指南 | SKILL.md, python/, typescript/, go/, java/, php/, ruby/, csharp/, curl/, shared/ |
| `doc-coauthoring`       | 引导用户通过结构化工作流协作撰写文档                   | SKILL.md                                                                         |
| `frontend-design`       | 创建高品质、可量产的前端界面设计                     | SKILL.md                                                                         |
| `internal-comms`        | 内部沟通写作助手（新闻稿、FAQ、公司通讯等）              | SKILL.md, examples/                                                              |
| `mcp-builder`           | MCP (Model Context Protocol) 服务器构建指南 | SKILL.md, reference/, scripts/                                                   |
| `anthropic-pptx`        | Anthropic 版本的 PowerPoint 演示文稿处理技能    | SKILL.md, scripts/, editing.md, pptxgenjs.md                                     |
| `slack-gif-creator`     | Slack 优化动画 GIF 创建工具                  | SKILL.md, core/, requirements.txt                                                |
| `web-artifacts-builder` | Claude.ai HTML artifacts 多组件构建工具套件   | SKILL.md, scripts/                                                               |
| `webapp-testing`        | 基于 Playwright 的 Web 应用自动化测试工具包       | SKILL.md, examples/, scripts/                                                    |


### 新增技能归属（对应第三章领域分类）


| 技能                      | 归属领域      | 分类位置   |
| ----------------------- | --------- | ------ |
| `anthropic-pptx`        | 文档处理      | 第 8 类  |
| `doc-coauthoring`       | 文档处理      | 第 8 类  |
| `frontend-design`       | 前端/设计/部署  | 第 14 类 |
| `canvas-design`         | 前端/设计/部署  | 第 14 类 |
| `web-artifacts-builder` | 前端/设计/部署  | 第 14 类 |
| `claude-api`            | 其他工具与实用技能 | 第 21 类 |
| `mcp-builder`           | 其他工具与实用技能 | 第 21 类 |
| `slack-gif-creator`     | 其他工具与实用技能 | 第 21 类 |
| `webapp-testing`        | 其他工具与实用技能 | 第 21 类 |
| `brand-guidelines`      | 其他工具与实用技能 | 第 21 类 |
| `internal-comms`        | 其他工具与实用技能 | 第 21 类 |


### 已存在的技能（6 个，未覆盖）

以下技能在 Vibe-Skills 中已有对应实现，本次未替换：


| Anthropic 技能      | Vibe-Skills 已有                                                            |
| ----------------- | ------------------------------------------------------------------------- |
| `algorithmic-art` | `bundled/skills/algorithmic-art/`                                         |
| `docx`            | `bundled/skills/docx/` + `document-skills/docx/`                          |
| `pdf`             | `bundled/skills/pdf/` + `document-skills/pdf/`                            |
| `skill-creator`   | `bundled/skills/.system/skill-creator/` + `bundled/skills/skill-creator/` |
| `theme-factory`   | `bundled/skills/theme-factory/`                                           |
| `xlsx`            | `bundled/skills/xlsx/`                                                    |


### 来源信息

- **仓库地址**：[https://github.com/anthropics/skills](https://github.com/anthropics/skills)
- **许可协议**：大部分为 Apache 2.0（文档技能 docx/pdf/pptx/xlsx 为 source-available）
- **集成日期**：2026-04-08

---

## 六、社区技能集成记录（更新至 2026-04-16）

以下技能来自社区开源仓库，已新增到 `bundled/skills/`：


| 技能                 | 来源仓库                                                                                                               | 归属领域              | 许可    | 目录                                 | 包含资源                                                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------------------------ | ----------------- | ----- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `ui-ux-pro-max`    | [https://github.com/nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 前端/设计/部署（第 14 类）  | MIT   | `bundled/skills/ui-ux-pro-max/`    | `SKILL.md`, `scripts/`, `data/`, `references/quick-reference.md`, `README.md`, `requirements.txt`                               |
| `ai-search-hub`    | [https://github.com/minsight-ai-info/AI-Search-Hub](https://github.com/minsight-ai-info/AI-Search-Hub)             | 研究与检索（第 13 类）     | MIT   | `bundled/skills/ai-search-hub/`    | `SKILL.md`, `scripts/`, `agents/openai.yaml`, `ROUTING.md`, `README.md`, `requirements.txt`                                     |
| `ssh-skill`        | [https://github.com/badseal/ssh-skill](https://github.com/badseal/ssh-skill)                                       | 其他工具与实用技能（第 21 类） | MIT   | `bundled/skills/ssh-skill/`        | `SKILL.md`, `scripts/`, `examples/`, `README.md`, `README_EN.md`, `requirements.txt`                                            |
| `pua`              | [https://github.com/tanweai/pua](https://github.com/tanweai/pua)                                                   | 兼容性支持层（第 2 类）     | MIT   | `bundled/skills/pua/`              | `SKILL.md`, `skills/`(多语言与子模式), `commands/`, `hooks/`, `agents/`, `scripts/setup-pua-loop.sh`, `README.md`, `README.zh-CN.md`   |
| `prompt-library`   | 本仓库内建（first-party local asset surface）                                                                             | 研究与检索（第 13 类）     | 项目内资产 | `bundled/skills/prompt-library/`   | `SKILL.md`, `index.json`, `prompts/`(多分类), `references/`, `README.md`                                                           |
| `arxiv-translator` | [https://github.com/Leey21/arxiv-translator](https://github.com/Leey21/arxiv-translator)                           | 科学写作与出版（第 10 类）   | MIT   | `bundled/skills/arxiv-translator/` | `SKILL.md`, `scripts/`(download.py, compile.py, inspect_tex.py, cleanup.py), `references/compile-errors.md`, `requirements.txt` |
| `algorithm-engineer-dualstack` | 用户提供的社区 Skill 文档（当前来源：`算法skill.md`） | AI/ML 与数据科学（第 5 类） | 待补充 | `bundled/skills/algorithm-engineer-dualstack/` | `SKILL.md`（单入口算法工程 Skill，覆盖调度/深度学习/图像/路径规划/Python-MATLAB 双栈） |
| `invoice-organizer` | [https://github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 其他工具与实用技能（第 21 类） | Apache-2.0 | `bundled/skills/invoice-organizer/` | `SKILL.md`（单入口；发票/收据读取、重命名、分类、CSV 汇总工作流） |
| `tailored-resume-generator` | [https://github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 规划与知识管理（第 20 类） | Apache-2.0 | `bundled/skills/tailored-resume-generator/` | `SKILL.md`（单入口；JD 分析、ATS 关键词、定制简历生成） |
| `meeting-insights-analyzer` | [https://github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 其他工具与实用技能（第 21 类） | Apache-2.0 | `bundled/skills/meeting-insights-analyzer/` | `SKILL.md`（单入口；会议转录分析、沟通模式识别、改进建议） |
| `langsmith-fetch` | [https://github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 代码开发与审查（第 4 类） | Apache-2.0 | `bundled/skills/langsmith-fetch/` | `SKILL.md`（单入口；LangSmith trace 调试流程，依赖外部 `langsmith-fetch` CLI） |
| `research-ideation` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 研究与检索（第 13 类） | MIT | `bundled/skills/research-ideation/` | `SKILL.md`, `references/`, `examples/` |
| `daily-paper-generator` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 研究与检索（第 13 类） | MIT | `bundled/skills/daily-paper-generator/` | `SKILL.md`, `scripts/`, `references/` |
| `results-analysis` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 数据处理与分析（第 6 类） | MIT | `bundled/skills/results-analysis/` | `SKILL.md`, `references/`, `examples/`, `USAGE.md` |
| `results-report` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/results-report/` | `SKILL.md`, `references/`, `examples/` |
| `publication-chart-skill` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/publication-chart-skill/` | `SKILL.md`, `scripts/`, `references/`, `examples/` |
| `ml-paper-writing` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/ml-paper-writing/` | `SKILL.md`, `references/` |
| `citation-verification` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/citation-verification/` | `SKILL.md`, `scripts/`, `references/` |
| `writing-anti-ai` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/writing-anti-ai/` | `SKILL.md`, `references/`, `examples/` |
| `paper-self-review` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/paper-self-review/` | `SKILL.md`, `references/`, `examples/` |
| `review-response` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/review-response/` | `SKILL.md`, `references/` |
| `post-acceptance` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/post-acceptance/` | `SKILL.md`, `references/`, `examples/` |
| `latex-conference-template-organizer` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 科学写作与出版（第 10 类） | MIT | `bundled/skills/latex-conference-template-organizer/` | `SKILL.md` |
| `obsidian-project-memory` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-project-memory/` | `SKILL.md`, `scripts/`, `references/` |
| `obsidian-project-bootstrap` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-project-bootstrap/` | `SKILL.md`, `references/` |
| `obsidian-project-lifecycle` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-project-lifecycle/` | `SKILL.md` |
| `obsidian-research-log` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-research-log/` | `SKILL.md` |
| `obsidian-experiment-log` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-experiment-log/` | `SKILL.md` |
| `obsidian-literature-workflow` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-literature-workflow/` | `SKILL.md`, `scripts/`, `references/` |
| `obsidian-synthesis-map` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-synthesis-map/` | `SKILL.md` |
| `obsidian-link-graph` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-link-graph/` | `SKILL.md` |
| `obsidian-bases` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-bases/` | `SKILL.md`, `references/` |
| `obsidian-cli` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-cli/` | `SKILL.md` |
| `obsidian-markdown` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/obsidian-markdown/` | `SKILL.md`, `references/` |
| `zotero-obsidian-bridge` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/zotero-obsidian-bridge/` | `SKILL.md`, `scripts/`, `references/`, `examples/` |
| `json-canvas` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/json-canvas/` | `SKILL.md`, `references/` |
| `skill-development` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/skill-development/` | `SKILL.md`, `references/` |
| `skill-improver` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/skill-improver/` | `SKILL.md`, `scripts/`, `references/`, `examples/` |
| `skill-quality-reviewer` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/skill-quality-reviewer/` | `SKILL.md`, `scripts/`, `references/` |
| `agent-identifier` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/agent-identifier/` | `SKILL.md`, `scripts/`, `references/`, `examples/` |
| `defuddle` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 规划与知识管理（第 20 类） | MIT | `bundled/skills/defuddle/` | `SKILL.md` |
| `daily-coding` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/daily-coding/` | `SKILL.md` |
| `git-workflow` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/git-workflow/` | `SKILL.md`, `references/`, `examples/` |
| `bug-detective` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/bug-detective/` | `SKILL.md`, `references/`, `examples/` |
| `verification-loop` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/verification-loop/` | `SKILL.md`, `references/`, `examples/` |
| `command-development` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/command-development/` | `SKILL.md`, `references/`, `examples/` |
| `hook-development` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 代码开发与审查（第 4 类） | MIT | `bundled/skills/hook-development/` | `SKILL.md`, `scripts/`, `references/`, `examples/` |
| `architecture-design` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | AI/ML 与数据科学（第 5 类） | MIT | `bundled/skills/architecture-design/` | `SKILL.md`, `references/`, `examples/` |
| `kaggle-learner` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | AI/ML 与数据科学（第 5 类） | MIT | `bundled/skills/kaggle-learner/` | `SKILL.md`, `references/` |
| `web-design-reviewer` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 前端/设计/部署（第 14 类） | MIT | `bundled/skills/web-design-reviewer/` | `SKILL.md`, `references/` |
| `uv-package-manager` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 其他工具与实用技能（第 21 类） | MIT | `bundled/skills/uv-package-manager/` | `SKILL.md` |
| `plugin-structure` | [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | 其他工具与实用技能（第 21 类） | MIT | `bundled/skills/plugin-structure/` | `SKILL.md`, `references/`, `examples/` |


### 调通检查（脚本级）

- `python bundled/skills/ui-ux-pro-max/scripts/search.py --help` ✅
- `python bundled/skills/ai-search-hub/scripts/run_web_chat.py --help` ✅
- `python bundled/skills/ssh-skill/scripts/ssh_execute.py --help` ✅
- `pua` 为命令/Hook 编排型技能，已完成 UTF-8 可读性与关键目录结构校验（`SKILL.md` + `commands/` + `hooks/` + `agents/`）✅
- `prompt-library` 已完成结构搭建、canonical 路由接入和 `skills-lock` 纳入 ✅
- `python bundled/skills/arxiv-translator/scripts/download.py --help` ✅（arXiv e-print 下载脚本）
- `algorithm-engineer-dualstack` 已完成主入口镜像与 canonical 路由接入；`vgo_cli route` 已对“调度算法工程 / 图像算法复现与消融实验”类请求命中验证 ✅
- `tailored-resume-generator` / `meeting-insights-analyzer` / `langsmith-fetch` 已完成主入口镜像、canonical 路由接入，并通过 `vgo_cli route` 代表性表达验证 ✅
- `invoice-organizer` 已完成主入口镜像与 canonical 路由接入；在包含“CSV 导出给会计”表达时会与现有 `spreadsheet` 语义重叠，后续如需更强命中可继续微调关键词/pack 边界
- `claude-scholar` 社区技能集（本轮新增 41 个）已完成主入口镜像与 canonical 路由接入：
  - `research-ideation`：`vgo_cli route` 对“5W1H + gap analysis”命中 `research-ideation`（0.7）✅
  - `results-analysis`：对“显著性检验 + figure catalog + stats appendix”命中 `results-analysis`（0.7）✅
  - `results-report`：对“决策导向复盘报告”命中 `results-report`（0.7）✅
  - `ml-paper-writing`：对“related work + 降 AI 味”命中 `ml-paper-writing`（0.45）✅
  - `review-response`：对“根据审稿意见写 rebuttal”命中 `review-response`（0.7）✅
  - `obsidian-project-memory`：对“同步到 Obsidian vault 并更新项目知识库”命中 `obsidian-project-memory`（0.7125）✅
  - `zotero-obsidian-bridge`：对“Zotero collection 生成 paper notes 并校验 schema”命中 `zotero-obsidian-bridge`（0.4625）✅
  - `skill-development`：对“新增 skill，设计结构和触发词”命中 `skill-development`（0.45）✅
  - `uv-package-manager`：对“uv sync 安装 pyproject 依赖”命中 `uv-package-manager`（0.7）✅
  - `git-workflow`：对“按 conventional commits 设计 git 工作流”命中 `git-workflow`（0.7）✅
- 脚本 smoke（claude-scholar 关键 scripts）：
  - `python bundled/skills/obsidian-project-memory/scripts/project_kb.py --help` ✅
  - `python bundled/skills/zotero-obsidian-bridge/scripts/verify_paper_notes.py --help` ✅
  - `python bundled/skills/publication-chart-skill/scripts/ensure_publication_tooling.py --help` ✅
  - `python bundled/skills/citation-verification/scripts/verify-citations.py --help` ✅（本轮已修复为支持在缺依赖场景下正常显示帮助）
- `pwsh ./check.ps1 -Deep -SkipRuntimeFreshnessGate`：49 passed, 0 failed, 5 warnings；warning 属于宿主目标根（`C:\Users\landx\.codex`）的运行时 freshness/closure 状态提示，不阻断本轮 skill 接入验收。
- 依赖已补充到各技能 `requirements.txt`，便于后续环境自动安装。

### Prompt 资产说明

如果你有很多不同类型的 prompt，推荐不要“一个 prompt 建一个 skill”，而是统一放入 `prompt-library`：

- 目录：`bundled/skills/prompt-library/`
- 分类：`coding`、`research`、`writing`、`review`、`translation`、`agent-control`、`business`
- 索引：`index.json`
- 已收录的 prompts：17 条学术写作 prompt（来自 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing)）

边界约定：

- `prompt-library`：管理和检索**本地 prompt 资产**
- `prompt-lookup`：处理 **external prompt retrieval / prompts.chat / prompt improvement**

### 添加 Prompt 操作入口（复制即用）

当你需要 AI / Agent 帮你往 `prompt-library` 里新增 prompt 时，直接复制下面的提示词块发送给 AI 即可。

#### 操作指南文件


| 文件                                                        | 用途                   |
| --------------------------------------------------------- | -------------------- |
| `bundled/skills/prompt-library/README.md`                 | 操作手册：目录结构、添加流程、边界说明  |
| `bundled/skills/prompt-library/references/taxonomy.md`    | 分类规范：7 个分类的定义和选择规则   |
| `bundled/skills/prompt-library/references/maintenance.md` | 维护规则：元数据要求、验证清单      |
| `bundled/skills/prompt-library/index.json`                | 索引文件：所有 prompt 的注册中心 |


#### 提示词块（复制即用）

```text
请按 Vibe-Skills 的 prompt-library 规范，帮我新增一个 prompt 到本地提示词库。

必须参照 bundled/skills/prompt-library/README.md 和 references/maintenance.md 执行。

具体要求：
1. 确认这个 prompt 属于哪个分类（coding / research / writing / review / translation / agent-control / business）；
2. 在 bundled/skills/prompt-library/prompts/<category>/ 下，复制 _template.md 并重命名；
3. 填写完整的元数据（id / title / category / tags / use_when / inputs / output_expectation）；
4. 写入 prompt 正文；
5. 在 bundled/skills/prompt-library/index.json 的 prompts 数组中注册该 prompt；
6. 确认文件位置和分类正确，元数据完整，index.json 已更新。

如果有多个 prompt 要添加，按分类批量处理，每个 prompt 独立一个文件。
```

---

## 七、新增技能统一同步规范（长期执行）

你后续每次新增 skill，统一按以下标准落地，确保"可用优先，文档次之"：

1. **完整镜像优先**：至少同步 `SKILL.md` + 核心 `scripts/` + 可运行示例（若上游有 `examples/`）。
2. **依赖显式化**：在技能目录落 `requirements.txt`（或等价依赖文件）。
3. **路由准入必做**：进入 canonical（更新 `pack-manifest` + `skill-keyword-index` + `skill-routing-rules`）或 custom manifest，不做这步就不算接入。
4. **脚本级调通**：至少完成一条可执行命令（通常 `--help` 或 smoke test）。
5. **路由验证必做**：用 `vgo_cli route` 确认 `selected.skill` 命中正确。
6. **健康检查**：运行 `check.ps1 -Deep`，确认无 `custom_manifest_invalid` / `custom_dependencies_missing`。
7. **分类即更新**：同步更新第三章领域分类（新增技能名 + 来源标记）。
8. **记录即索引**：在"社区技能集成记录"补 `来源/归属/许可/目录/包含资源/调通状态`。
9. **最小可运行承诺**：只做文档登记但未跑通脚本和路由验证的技能，不算"已接入完成"。

---

## 八、AI / Agent 新增 Skill 操作入口（复制即用）

当你需要 AI / Agent 帮你新增一个 skill 并确保它可被正常调用时，直接复制下面的提示词块发送给 AI 即可。

### 操作指南文件

AI / Agent 执行时必须参照以下文件（按优先级排序）：


| 文件                                                             | 用途                                       |
| -------------------------------------------------------------- | ---------------------------------------- |
| `docs/install/agent-skill-onboarding-and-callability-guide.md` | 主操作手册：接入路径选择、canonical 配置、权重判断、验证步骤、交付口径 |
| `skill智能调用与复杂Skill接入指南.md`                                     | 补充理解：Vibe 路由原理、复杂 skill 建模、常见失败排查        |
| `docs/install/custom-workflow-onboarding.md`                   | 走 custom 路径时的 manifest 声明规范              |
| `docs/install/custom-skill-governance-rules.md`                | 自定义 skill 的治理硬规则                         |


### 提示词块（复制即用）

```text
请按 Vibe-Skills 项目的标准流程新增一个 skill，并证明它可以被正常调用。

必须严格按照 docs/install/agent-skill-onboarding-and-callability-guide.md 执行。

具体要求：
1. 先分析上游 skill 的功能、意图、任务类型和复杂度；
2. 把 skill 镜像到 bundled/skills/<skill-id>/，保留主入口和关键资源；
3. 判断它属于单入口、脚本增强型还是复杂多表面 skill；
4. 走 canonical 接入：
   a. 更新 config/pack-manifest.json（新建 pack，设定 priority/task_allow/trigger_keywords/skill_candidates/defaults_by_task）
   b. 更新 config/skill-keyword-index.json（补充中英文关键词）
   c. 更新 config/skill-routing-rules.json（设定 task_allow/positive_keywords/negative_keywords/equivalent_group/canonical_for_task）
   d. 必要时更新 config/skill-alias-map.json
5. 解释为什么这样设定 priority、task_allow、positive_keywords、negative_keywords；
6. 运行至少一条可执行验证（脚本型跑 --help，命令型跑结构校验）；
7. 运行 route 测试（python -m vgo_cli.main route），证明 selected.skill 命中正确；
8. 运行 check.ps1 -Deep，区分 skill 接入问题与宿主健康问题；
9. 更新 skills管理和安装指南.md：
   a. 第三章领域分类补入新技能名
   b. 第六章社区集成记录补入来源/归属/许可/目录/包含资源/验证状态
10. 最终交付时必须说明：镜像位置、主入口、接入路径、config 改动、权重依据、验证结果。

绝对不要说"文件已复制所以可用"或"文档已记录所以接入完成"。
```

