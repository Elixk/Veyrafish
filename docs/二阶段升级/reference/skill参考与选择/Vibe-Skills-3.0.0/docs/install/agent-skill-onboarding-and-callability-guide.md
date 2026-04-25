# AI / Agent 新增 Skill 接入与可调用保障指南

本指南是给 AI 或 Agent 的操作手册，不是面向普通用户的概念介绍。

目标只有一个：**把一个新 skill 正确接入到 Vibe-Skills，并证明它可以被正常调用。**

---

## 1. 先记住这三条

在这个项目里，真正的“已接入可调用”必须同时满足：

1. 有主入口：`SKILL.md`
2. 有准入：进入 canonical router 或 custom manifest
3. 有验证：至少完成结构验证、可执行验证、路由验证

任何只完成“复制目录”但没有完成准入和验证的 skill，都不算完成接入。

---

## 2. 这个项目的调用原理

Vibe-Skills 不是“扫描目录自动激活”的系统，而是**受治理路由系统**。

路由主要由这几层组成：

- `config/pack-manifest.json`
  - 定义 pack、优先级、可用任务类型、默认 skill、触发关键词
- `config/skill-keyword-index.json`
  - 为 skill 提供额外关键词召回信号
- `config/skill-routing-rules.json`
  - 为 skill 提供 `task_allow`、正向关键词、负向关键词、canonical task 偏好
- `config/skill-alias-map.json`
  - 处理常见别名
- `scripts/router/...` 与 `packages/runtime-core/...`
  - 实际执行路由打分、阈值比较、准入检查

这意味着：

- `bundled/skills/<name>/SKILL.md` 是**必要条件**
- 但它不是**充分条件**
- 必须再让 skill 进入 canonical 或 custom 准入面，路由器才会考虑它

---

## 3. 先判断你要走哪条接入路径

新增 skill 前，先做一次分流判断。

### 路径 A：走 canonical

适用于：

- 你希望这个 skill 成为仓库默认的一部分
- 这是一个可复用、稳定、面向多项目的能力
- 你愿意为它维护 pack、关键词、路由规则和长期兼容性

典型操作：

- 改 `bundled/skills/`
- 改 `config/pack-manifest.json`
- 改 `config/skill-keyword-index.json`
- 改 `config/skill-routing-rules.json`
- 必要时改 `config/skill-alias-map.json`

### 路径 B：走 custom

适用于：

- 这是实验性、项目私有、低频或高风险能力
- 你不希望它进入全局默认路由
- 你只想让它在某个宿主或项目里可被建议/调用

典型操作：

- 写 `config/custom-skills.json` 或 `config/custom-workflows.json`
- 不改 canonical pack

> 如果用户明确要求“正式纳入产品默认路由”，就走 canonical。  
> 如果用户只要“先能用”，优先走 custom。

---

## 4. 新 skill 的分类方式

不要把所有 skill 都当成同一种东西处理。先识别类型。

### 4.1 单入口 skill

结构通常只有：

```text
bundled/skills/<skill-id>/
└── SKILL.md
```

这类 skill 最容易接入，重点是路由和关键词。

### 4.2 脚本增强型 skill

结构通常为：

```text
bundled/skills/<skill-id>/
├── SKILL.md
├── scripts/
├── references/
└── requirements.txt
```

这类 skill 需要额外做脚本可执行验证。

### 4.3 复杂多表面 skill

结构通常为：

```text
bundled/skills/<skill-id>/
├── SKILL.md
├── skills/
├── commands/
├── hooks/
├── agents/
├── scripts/
└── references/
```

例如 `pua` 这种“多子技能 + commands/hooks/agents”的仓库。

这类 skill 的关键不是把所有文件都复制过来，而是先确定：

- 哪个是主入口 skill
- 哪些子技能只是内部模式
- 哪些 commands/hook 是宿主专属能力
- 哪些资源是必须镜像，哪些只是上游附属资产

---

## 5. 接入时的标准步骤

建议 AI / Agent 固定按下面顺序执行。

### 步骤 1：理解上游 skill 的真实形态

至少回答这些问题：

- skill 主要解决什么问题
- 典型触发意图是什么
- 它更像 `planning` / `coding` / `review` / `debug` / `research` 中的哪几类
- 是否有可执行脚本
- 是否依赖 commands、hooks、agents
- 是否需要浏览器、SSH、Python 包等外部依赖

如果这些都没搞清楚，不要直接写 pack。

### 步骤 2：确定本仓库内的镜像结构

默认镜像到：

```text
bundled/skills/<skill-id>/
```

最低要求：

- `SKILL.md`

推荐保留：

- `scripts/`
- `references/`
- `examples/`
- `commands/`
- `hooks/`
- `agents/`
- `requirements.txt`
- `README.md`

### 步骤 3：确定“主入口”

复杂 skill 必须选一个主入口。

规则：

- 如果仓库只有一个核心 `SKILL.md`，它就是主入口
- 如果上游有多个子技能，通常仍要在顶层保留一个主 `SKILL.md`
- 主路由命中的永远应该是“主入口”
- 子技能通常作为内部模式，不应该默认都进入全局路由

### 步骤 4：决定是否进入 canonical

只有满足下面条件，才建议进入 canonical：

- 能力边界清晰
- 关键词空间可控
- 不会强烈冲撞现有 pack
- 有清晰默认任务类型
- 有可验证的调用方式

否则先走 custom。

---

## 6. canonical 接入的具体做法

如果决定走 canonical，至少要改 3 个配置文件。

### 6.1 更新 `config/pack-manifest.json`

这是 pack 级入口。

每个新 pack 至少包含：

- `id`
- `priority`
- `grade_allow`
- `task_allow`
- `trigger_keywords`
- `skill_candidates`
- `defaults_by_task`

示例：

```json
{
  "id": "community-uiux-design",
  "priority": 84,
  "grade_allow": ["M", "L", "XL"],
  "task_allow": ["planning", "coding", "review"],
  "trigger_keywords": ["ui ux", "design system", "landing page", "界面设计", "设计系统"],
  "skill_candidates": ["ui-ux-pro-max", "frontend-design", "figma-implement-design"],
  "defaults_by_task": {
    "planning": "ui-ux-pro-max",
    "coding": "ui-ux-pro-max",
    "review": "ux-researcher-designer"
  }
}
```

#### priority 怎么定

不要拍脑袋。

建议按当前仓库风格控制：

- `96-100`：官方核心编排/主链，不给社区新 skill
- `90-95`：官方高置信领域 pack
- `83-89`：稳定、共享、边界清晰的社区领域 pack
- `80-82`：支持型、行为型、实验型、容易冲突的 community pack
- `60-79`：很窄、很新、很不稳定或低默认性能力

经验规则：

- 如果 skill 是“主流程替代者”，priority 不要太高
- 如果 skill 是“强领域专长”，priority 可以略高
- 如果 skill 很容易误触发，就把 priority 压低，并增加负向关键词

### 6.2 更新 `config/skill-keyword-index.json`

这是 skill 级的关键词召回补充。

用途：

- 提高 skill 被召回的机会
- 增加同义词、中英文、用户常见表述

示例：

```json
"ssh-skill": {
  "keywords": [
    "ssh",
    "remote server",
    "jump host",
    "ssh tunnel",
    "远程服务器",
    "跳板机",
    "批量运维"
  ]
}
```

关键词写法建议：

- 同时写英文技术词与中文用户表达
- 写“任务目标词”，不要只写品牌名
- 避免写过宽的通用词，例如“系统”“工具”“处理”

### 6.3 更新 `config/skill-routing-rules.json`

这是 skill 级的精排规则。

每个新增 skill 至少应定义：

- `task_allow`
- `positive_keywords`
- `negative_keywords`
- `equivalent_group`
- `canonical_for_task`

示例：

```json
"ai-search-hub": {
  "task_allow": ["research", "planning", "review"],
  "positive_keywords": [
    "ai search hub",
    "multi platform search",
    "搜索聚合",
    "多平台搜索",
    "趋势简报"
  ],
  "negative_keywords": [
    "ssh",
    "ui implementation",
    "unit test"
  ],
  "equivalent_group": "search-aggregation",
  "canonical_for_task": ["research", "planning"]
}
```

#### `positive_keywords` 怎么写

写三类：

- 产品名 / skill 名
- 用户会说的任务短语
- 该能力特有的领域词

#### `negative_keywords` 怎么写

专门用来防止误路由。

优先写：

- 与相邻 pack 冲突的词
- 该 skill 明显不该处理的任务
- 近邻强 skill 的高频特征词

#### `canonical_for_task` 怎么用

只有当这个 skill 在某任务类型下明显是更优默认解时才写。

不要为了“多命中”滥用。

### 6.4 必要时更新 `config/skill-alias-map.json`

只有在用户常用别名明显固定时才加。

例如：

- 中文俗称
- 品牌缩写
- 固定翻译名

不要把所有同义词都塞进 alias；大多数应该放进 keyword index。

---

## 7. 复杂 skill 的特殊处理规则

复杂 skill 不是把目录原样复制就结束了。

### 7.1 `skills/` 子技能

- 子技能通常是内部模式，不默认都挂到 canonical
- 路由器通常只命中主入口
- 需要把子技能暴露为独立路由对象时，必须单独评估是否真的值得进入全局候选池

### 7.2 `commands/`

- `commands/` 通常是显式触发入口，不代表主路由自动会用
- 如果 skill 的价值主要依赖命令（例如 `/pua:p9`），文档中必须写清楚“自动触发”和“命令触发”的边界

### 7.3 `hooks/`

- Hook 通常强依赖宿主
- 不能默认假设 Codex、Claude Code、Cursor 都会等价执行
- 接入时必须注明：这是“主路由能力”还是“宿主增强能力”

### 7.4 `agents/`

- `agents/` 是协同执行资产，不是主路由入口
- 只有当主 skill 命中后，才会在其工作流中再使用对应 agent

### 7.5 `scripts/`

- `scripts/` 必须至少有一条可验证执行路径
- 最低标准通常是 `--help`
- 更高标准是 smoke test

---

## 8. 如何证明“它真的能被调用”

至少做下面 4 类验证。

### 8.1 结构验证

检查：

- `bundled/skills/<skill-id>/SKILL.md` 存在
- 编码可读（UTF-8）
- 复杂 skill 的关键目录存在

### 8.2 可执行验证

脚本型 skill：

```powershell
python "bundled/skills/<skill-id>/scripts/<entry>.py" --help
```

复杂命令型 skill：

- 校验关键文件存在
- 必要时跑最小脚本或最小结构自检

### 8.3 路由验证

用真实路由命令测试：

```powershell
python -m vgo_cli.main route `
  --repo-root "D:\user\landx\Desktop\AI\tools\skills\Vibe-Skills-3.0.0" `
  --prompt "请根据提示词选择 skill" `
  --task-type coding `
  --grade M
```

要重点看输出里的这些字段：

- `selected.pack_id`
- `selected.skill`
- `selection_reason`
- 候选列表里是否包含你新增的 skill

### 8.4 健康检查

```powershell
powershell -ExecutionPolicy Bypass -File ".\\check.ps1" -Deep
```

要注意区分两类结果：

#### A. skill 接入健康

这类失败说明你的新增 skill 本身没接好：

- 路由没命中
- 关键词没召回
- canonical pack 没生效
- custom manifest 无效

#### B. 宿主运行时健康

这类失败可能和新增 skill 无关，例如：

- `runtime-freshness-receipt` 缺失
- 宿主 target root 的 ready 状态不完整

结论要如实写：

- “skill 已进入 canonical 并能命中”
- “但宿主 runtime 仍有独立健康问题”

不要把这两类问题混为一谈。

---

## 9. 一个 Agent 应该怎样估算“路由权重”

不要直接改全局权重；优先通过 pack/rule 设计影响结果。

### 9.1 先理解当前真实信号

当前路由的核心信号来自 `config/router-thresholds.json`：

- `intent_match = 0.4`
- `trigger_keyword_match = 0.25`
- `workspace_signal_match = 0.2`
- `skill_keyword_signal = 0.25`
- `recent_success_prior = 0.1`
- `conflict_penalty_inverse = 0.05`

候选精排还有这些附加调节项：

- `rule_positive_keyword_bonus = 0.2`
- `rule_negative_keyword_penalty = 0.25`
- `canonical_for_task_bonus = 0.12`

阈值上，当前主要分三档：

- `auto_route = 0.7`
- `confirm_required = 0.45`
- `fallback_to_legacy_below = 0.45`

这意味着：

- **最重要的是意图匹配**，不是 skill 名字好不好听
- `trigger_keywords` 和 `skill_keyword_index` 都很重要，但它们本质上是在给意图召回提供证据
- `negative_keywords` 的作用很大，因为精排阶段会做显式惩罚
- `canonical_for_task` 只在“这个任务上它真的更像默认解”时才值得用

### 9.2 新 skill 的判断框架

新增一个 skill 时，Agent 应该先做下面 5 个判断，再决定 pack priority 和关键词设计。

| 维度 | 问题 | 结论影响 |
|---|---|---|
| 任务适配度 | 它主要服务 `planning/coding/review/debug/research` 哪些任务？ | 决定 `task_allow` 和 `defaults_by_task` |
| 意图独特性 | 用户会不会用一组比较稳定、可识别的话来表达这个需求？ | 决定 `trigger_keywords` 和 `positive_keywords` 的有效性 |
| 近邻冲突度 | 它与现有 pack / skill 有多重叠？ | 决定是否需要强负向关键词，以及是否应该压低 `priority` |
| 默认性 | 它是“默认推荐解”还是“特殊场景增强解”？ | 决定是否进入 canonical，以及是否设置 `canonical_for_task` |
| 可执行性 | 它有没有脚本、命令或稳定的可验证调用面？ | 决定是否值得纳入 canonical 主路径 |

### 9.3 priority 的判断规则

新增 skill 时，不要把 `priority` 当成“强行抢路由”的按钮，而是当成“在同类 pack 中的默认可信度”。

建议按下面这套规则判断：

- `96-100`
  - 官方核心编排 / 主链 pack
  - 社区新增 skill 不应该进入这个区间
- `90-95`
  - 官方高置信领域能力
  - 新 community skill 一般不建议直接放这么高
- `83-89`
  - 稳定、边界清晰、可跨项目复用、且可验证的 community 能力
  - 这是大多数“值得 canonical 化”的新 skill 区间
- `80-82`
  - 行为增强型、支持型、容易和其他 pack 冲突的能力
  - 例如高能动性、流程督促、带强宿主依赖的能力
- `60-79`
  - 窄场景、实验性、强依赖命令/Hook 或误触发风险高的能力

简单判断法：

- 边界清晰 + 关键词稳定 + 调用收益高：`83-89`
- 有价值，但更像“行为增强”或“辅助层”：`80-82`
- 还不稳定，或者只在少数项目里成立：`60-79`

### 9.4 关键词怎么判断“写得够不够好”

`trigger_keywords`、`skill_keyword_index`、`positive_keywords` 都应该围绕“用户真实会怎么说”来写。

建议每个新增 skill 都覆盖这三层表达：

1. **产品/技能名**
   - 例如 `ai-search-hub`、`ssh-skill`
2. **用户任务短语**
   - 例如“多平台搜索”“批量运维”“设计系统”
3. **领域特有词**
   - 例如 `jump host`、`landing page`、`trend brief`

同时必须补一组 `negative_keywords`，专门处理近邻冲突。

写不好关键词最常见的两个坏结果：

- 召回不出来：说明正向词太少、太品牌化、太不贴近用户表达
- 误命中太多：说明负向词不够，或者 pack 边界没定义清楚

### 9.5 `canonical_for_task` 什么时候能开

只有当下面 3 条同时满足时才建议开：

1. 这个 skill 在某个任务类型里明显更像默认解
2. 它不是靠命令/Hook 才能成立的弱主入口
3. 你已经通过 route 测试证明它在相应 prompt 下确实更合理

如果只是“它也能做这个任务”，不要开。

### 9.6 给 Agent 的解释模板

每次把新 skill 纳入 canonical 时，Agent 最终都应该能说明：

- 为什么这个 skill 的 `task_allow` 是这些，不是更多
- 为什么 pack 设为这个 `priority`
- 为什么 `defaults_by_task` 选它而不是近邻 skill
- 为什么这些关键词足以召回
- 为什么这些 `negative_keywords` 足以抑制误命中
- 为什么它应该或不应该设置 `canonical_for_task`

### 9.7 用最近新增的 4 个 skill 作为例子

| Skill | 路由判断 | priority 判断 | 说明 |
|---|---|---|---|
| `ui-ux-pro-max` | 主任务是 `planning/coding/review`，意图短语稳定，边界清晰 | `84` | 它是强领域能力，但不是官方主链，适合放在稳定 community canonical 区间 |
| `ai-search-hub` | 主任务是 `research/planning`，用户表达常见为“聚合搜索/趋势简报/多平台搜索” | `86` | 研究型召回价值高，且与普通深度研究 skill 有清晰区别，因此略高于普通 community pack |
| `ssh-skill` | 主任务是 `coding/debug/review`，运维词汇清晰，命令可验证 | `84` | 边界稳定，宿主依赖可控，适合默认进入远程运维相关场景 |
| `pua` | 更像行为增强与执行督促，不是纯领域技能 | `80` | 它有价值，但更容易与调试/验证类 skill 产生重叠，因此不宜给太高 priority |

### 9.8 一个简单经验

- 如果你需要靠非常高的 `priority` 才能命中，通常说明关键词设计有问题
- 如果 skill 经常误命中，优先加 `negative_keywords`，而不是一味降 `priority`
- 如果 skill 只有在显式命令下才真正成立，优先降级为支持型或走 custom，而不是硬塞进高优先级 canonical

---

## 10. 推荐的固定执行顺序（给 AI / Agent）

以后每次新增 skill，固定按下面 prompt 执行：

```text
请把一个新的 skill 按 Vibe-Skills 的 canonical 方式接入，并证明它可以被正常调用。

执行要求：
1. 先分析上游 skill 的功能、意图、任务类型和复杂度；
2. 把 skill 镜像到 bundled/skills/<skill-id>/，保留主入口和关键资源；
3. 判断它属于单入口、脚本增强型还是复杂多表面 skill；
4. 如果走 canonical：
   - 更新 config/pack-manifest.json
   - 更新 config/skill-keyword-index.json
   - 更新 config/skill-routing-rules.json
   - 必要时更新 config/skill-alias-map.json
5. 解释 priority、task_allow、positive_keywords、negative_keywords 的依据；
6. 运行至少一条可执行验证；
7. 运行 route 测试并证明 selected.skill 正确；
8. 运行 check.ps1 -Deep，并区分 skill 接入问题与宿主健康问题；
9. 最后更新文档，记录来源、归属、资源、验证状态。
```

---

## 11. 最终交付口径

一个 AI / Agent 完成新增 skill 后，最终应该用下面这套口径汇报：

### 必须说明

- skill 镜像到了哪里
- 主入口是什么
- 走的是 canonical 还是 custom
- 改了哪些 config 文件
- 为什么这样设计 priority 和关键词
- 哪些验证已通过
- `check --deep` 是否全绿
- 如果没全绿，哪些是 skill 问题，哪些是宿主环境问题

### 绝对不要说

- “文件已经复制，所以 skill 已可用”
- “文档已记录，所以接入完成”
- “check 有报错，但应该不影响”

---

## 12. 一句话总结

在这个项目里，新增 skill 的正确顺序永远是：

**理解能力 -> 镜像资源 -> 选择主入口 -> 进入准入面 -> 配路由信号 -> 做真实验证 -> 再宣布可调用。**

只做前两步，不算接入完成。
