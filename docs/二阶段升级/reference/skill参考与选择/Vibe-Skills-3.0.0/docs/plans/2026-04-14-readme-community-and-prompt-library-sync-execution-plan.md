# Execution Plan: README Community Sync 与 Prompt Library 首页补全

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-readme-community-and-prompt-library-sync-execution-plan |
| 状态 | completed |
| 需求文档 | docs/requirements/2026-04-14-readme-community-and-prompt-library-sync.md |
| 内部等级 | M（single-agent） |
| 创建日期 | 2026-04-14 |

## Wave 1: 首页信息架构补强

### Step 1.1: README 能力地图补充
- 在双语 README 的科研/学术写作能力区补入 `arxiv-translator`
- 在合适位置突出 `prompt-library` 作为本地 Prompt 资产库的定位

### Step 1.2: README 扩展入口补充
- 在双语 README 的安装/自定义区域增加 fork 后扩展 Skill / Prompt 的入口说明
- 链接到现有管理与接入文档，避免重复维护两套大篇幅说明

## Wave 2: 开源叙事与社区整合说明

### Step 2.1: 社区整合说明补充
- 在双语 README 中新增“最近集成”可见区块，补入近期已整合来源的代表性示例
- 明确说明社区 Skill 镜像与 Prompt 资产整理是项目演进的一部分

## Wave 3: 验证与收尾

### Step 3.1: 一致性检查
- 检查 README 与 `skills管理和安装指南.md` 事实是否一致
- 检查双语文案是否对齐

### Step 3.2: 质量检查
- 使用 `ReadLints` 检查最近编辑文件的结构性问题
- 完成后将 requirement 与 plan 状态收尾

## 回滚规则

- 若新增段落与原有 README 风格冲突，优先缩短而不是扩大改动面
- 若中英文信息无法完全等长，则保留语义一致，不强求逐句对照
