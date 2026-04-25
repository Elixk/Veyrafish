# Execution Plan: arxiv-translator Skill 与 awesome-ai-research-writing Prompts 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-09-arxiv-translator-and-research-writing-prompts-execution-plan |
| 状态 | completed |
| 需求文档 | docs/requirements/2026-04-09-arxiv-translator-and-research-writing-prompts.md |
| 内部等级 | L（serial native execution） |
| 创建日期 | 2026-04-09 |

## Wave 1: arxiv-translator Skill 镜像与接入

### Step 1.1: 创建 skill 目录结构
- 创建 `bundled/skills/arxiv-translator/`
- 创建子目录 `scripts/`, `references/`

### Step 1.2: 镜像核心文件
- `SKILL.md`（主入口）
- `scripts/download.py`
- `scripts/inspect_tex.py`
- `scripts/compile.py`
- `scripts/cleanup.py`
- `references/compile-errors.md`
- `requirements.txt`

### Step 1.3: Canonical 路由接入
- 更新 `config/pack-manifest.json`（新建 pack `community-arxiv-translation`）
- 更新 `config/skill-keyword-index.json`
- 更新 `config/skill-routing-rules.json`

### Step 1.4: 脚本级验证
- 运行 `python bundled/skills/arxiv-translator/scripts/download.py --help`

### Step 1.5: 路由验证
- 运行 `vgo_cli route` 测试

## Wave 2: awesome-ai-research-writing Prompts 接入

### Step 2.1: 创建 17 个 prompt 文件

按分类创建：

**translation/ (2个)**
- cn-to-en.md
- en-to-cn.md

**writing/ (10个)**
- cn-to-cn.md
- compress.md
- expand.md
- polish-en.md
- polish-cn.md
- de-ai-latex-en.md
- de-ai-word-cn.md
- paper-architecture-diagram.md
- experiment-chart-recommend.md
- figure-caption.md
- table-caption.md
- experiment-analysis.md

**review/ (2个)**
- logic-check.md
- reviewer-perspective.md

**research/ (1个)**
- model-selection.md

### Step 2.2: 更新 index.json
- 注册全部 17 个 prompt

## Wave 3: 文档与验证

### Step 3.1: 更新 skills管理和安装指南.md
- 第 10 章"科学写作与出版"补入 `arxiv-translator`
- 第 6 章社区集成记录补入两个来源的信息
- Prompt 资产说明补入 awesome-ai-research-writing 来源

### Step 3.2: 最终验证
- 检查 prompt 文件完整性
- 运行 `check.ps1 -Deep`（区分新增问题与既有问题）

## 回滚规则

- 如 skill 路由测试失败，回退 config/ 改动
- 如 prompt 格式有误，按 template 重新生成

## 完成判定

- 全部验收标准通过
- `skills管理和安装指南.md` 已更新
- 无新增 linter 错误
