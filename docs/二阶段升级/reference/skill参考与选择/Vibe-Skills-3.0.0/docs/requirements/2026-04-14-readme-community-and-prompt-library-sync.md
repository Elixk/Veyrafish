# Requirement: README Community Sync 与 Prompt Library 首页补全

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-readme-community-and-prompt-library-sync |
| 状态 | frozen |
| 创建日期 | 2026-04-14 |
| 作者 | AI Agent (governed) |

## 1. 目标

将近期已完成接入的新能力同步到双语首页：

1. `README.md`
2. `README.zh.md`

让用户在仓库首页即可理解以下新增内容：

- 已接入的社区技能扩展能力，尤其是 `arxiv-translator`
- 本地 Prompt 资产能力 `prompt-library`
- `awesome-ai-research-writing` 已被结构化纳入 `prompt-library`
- fork 后继续扩展自己 Skill / Prompt 资产的入口文档

## 2. 交付物

- 更新后的 `README.md`
- 更新后的 `README.zh.md`
- 对应的 requirement / execution plan 留痕

## 3. 约束

- 不改动运行时逻辑、路由逻辑与技能实现
- 仅做首页级信息架构补强与可发现性增强
- 中英文 README 保持信息大体对齐，但允许语言表达自然本地化
- 新增说明需与 `skills管理和安装指南.md` 中的既有事实一致

## 4. 验收标准

- [x] `README.md` 明确体现 `prompt-library` 与新社区技能整合能力
- [x] `README.zh.md` 明确体现 `prompt-library` 与新社区技能整合能力
- [x] 双语 README 给出 fork 后继续扩展 Skill / Prompt 的入口
- [x] 文案不与现有路由、安装、治理说明冲突
- [x] 无新增文档结构性问题

## 5. 非目标

- 不在本轮重写整份 README
- 不新增新的技能或 prompt 资产
- 不调整安装脚本、check 脚本与 canonical router 行为

## 6. 人工抽查点

- 首页是否能一眼看出项目不仅管理 Skills，也管理本地 Prompt 资产
- 首页是否能一眼看出项目持续吸收社区上游能力
- fork 使用者是否能快速找到“如何继续新增 Skill / Prompt”的入口
