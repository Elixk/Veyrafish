# Requirement: algorithm-engineer-dualstack 社区 Skill 接入

| 字段 | 值 |
|------|-----|
| ID | 2026-04-14-algorithm-engineer-dualstack-community-skill |
| 状态 | frozen |
| 创建日期 | 2026-04-14 |
| 作者 | AI Agent (governed) |

## 1. 背景

用户在根目录提供了 `算法skill.md`，其内容已经是一个完整的 Skill 主入口草案：

- `name: algorithm-engineer-dualstack`
- 中文描述完整
- 面向调度算法、深度学习、图像算法、避障算法、Python / MATLAB 双栈实现

用户要求按 `skills管理和安装指南.md` 的规范，把它作为一个新的社区 Skill 接入到当前项目中，并确保符合“已接入可调用”的标准。

## 2. 目标

将 `algorithm-engineer-dualstack` 以社区 Skill 的形式接入当前仓库，至少完成：

1. 在 `bundled/skills/algorithm-engineer-dualstack/` 下建立主入口
2. 走 canonical 路由接入
3. 更新 `skills管理和安装指南.md` 的分类与社区记录
4. 完成结构验证与路由验证

## 3. 类型判断

该 Skill 当前形态为：

- **单入口 Skill**
- 主入口为单个 `SKILL.md`
- 无独立脚本、无上游 `scripts/` / `references/` / `examples/`
- 主要价值在于方法论、工程化流程与评价协议，而不是确定性外部脚本

因此本轮按“单入口 canonical community skill”接入。

## 4. 分类判断

基于其触发意图和技能边界，主归类为：

- **第 5 类：AI/ML 与数据科学**

原因：

- 覆盖深度学习、图像算法、数值优化与实验评估
- 虽然也触及 MATLAB、调度、路径规划，但整体是“算法工程”横向技能，不适合放入更窄的单领域类目

## 5. 验收标准

- [x] `bundled/skills/algorithm-engineer-dualstack/SKILL.md` 存在
- [x] `config/pack-manifest.json` 已新增 canonical pack
- [x] `config/skill-keyword-index.json` 已新增技能关键词
- [x] `config/skill-routing-rules.json` 已新增路由规则
- [x] `skills管理和安装指南.md` 第 5 类已补入该 Skill
- [x] `skills管理和安装指南.md` 社区技能集成记录已补入该 Skill
- [x] `vgo_cli route` 已对代表性算法需求命中该 Skill（algorithm-engineer-dualstack）
- [x] 不引入新的文档或结构错误

## 6. 约束

- 不伪造不存在的 upstream 资源
- 不凭空添加 `scripts/`、`references/`、`requirements.txt`
- 路由权重需保守，避免误抢现有更窄的 ML / 视觉 / 数据技能

## 7. 人工抽查点

- “调度算法 / 深度学习 / 图像算法 / 路径规划 / MATLAB 双栈实现”这类请求能否自然命中
- “scikit-learn / PyTorch / 生信数据库 / 论文翻译”这类更窄领域请求不应被它轻易抢走
