# Phase 3 实施清单：产品化与平台化增强

**状态**：进行中（已完成 5 轮前端重构；当前完成度以静态实现为主，仍缺浏览器实机验收）

## 1. 阶段目标

在前两个阶段稳定后，补齐前端、插件化、评估、回放和平台管理能力。

> 因竞赛时间压力，本阶段前端部分已先行启动。Phase 0-2 的工程治理与架构升级后续再补。

## 2. 开始条件

- [ ] Phase 2 已完成（当前已豁免，先行启动前端）
- [x] 前端规划文档已冻结
- [x] 现有前端功能键已盘点
- [x] 页面信息架构已定义

## 3. 本阶段必须完成的任务

### 3.1 前端升级（主要工作线）

参考文档：

- [前端功能清单](./frontend/FRONTEND_FUNCTION_INVENTORY.md)
- [前端页面信息架构](./frontend/FRONTEND_PAGE_ARCHITECTURE.md)
- [前端重构总规划](./frontend/FRONTEND_RESTRUCTURE_PLAN.md)

#### Round A：功能收敛与页面拆分

- [x] 盘点现有前端所有功能键与功能分组
- [x] 冻结首页、五引擎页、系统控制层的职责边界
- [x] 把五个引擎从标签切换升级为页面级视图结构
- [x] 把系统控制按钮从首页主操作区拆走（系统菜单 popover）
- [x] 保留旧前端脚本兼容（关键 DOM id 与 `.app-switcher`）

具体已完成：

- [x] 首页重写为"总览页 + 五引擎入口 + 工作台 + 控制台"结构（Round 02）
- [x] 加入代码生成国风装饰元素（Round 03）
- [x] 五引擎图标 SVG Sprite 化（Round 04）
- [x] 系统操作按钮收纳为"系统菜单"popover（本轮）
- [x] 新增后端 SVG 资产路由 `/assets/svg/<filename>`（本轮）
- [x] 顶栏角饰替换为外部 SVG 资产 `header-bamboo-corner.svg`（本轮）
- [x] 品牌章替换为外部 SVG 资产 `logo-seal-red.svg`（本轮）
- [x] 五引擎图标替换为外部 SVG 资产（本轮）
- [x] 卷首引言区加入 `quote-seal-left.svg` / `quote-boat-landscape.svg`（本轮）
- [x] 搜索区加入 `input-ink-mountain.svg` 水墨背景（本轮）
- [x] 拆分 6 个独立页面：总览页 + Insight / Media / Query / Forum / Report 内页（Round 05）
- [x] 新增共享 `static/engine-shared.css` / `static/engine-shared.js`（Round 05）
- [x] 新增 5 条 Flask 页面路由：`/insight`、`/media`、`/query`、`/forum`、`/report`（Round 05）

待完成：

- [ ] 顶部导航 `.nav-chip` 加上实际路由/视图切换逻辑
- [x] 页脚加入 `footer-mountain-left.svg`、`footer-mountain-right-boat.svg`、`footer-seal.svg`
- [x] 云纹装饰 `cloud-flourish.svg` 接入
- [ ] 图表区装饰 `chart-ink-bamboo-mountain.svg` 接入
- [ ] 浏览器实机验证全部 SVG 资产显示正常
- [ ] 移动端适配检查

#### Round B：总览页重构

- [x] 首页主输入区保留（搜索 + 模板上传 + 调度参数入口）
- [x] 五引擎摘要卡片已重构
- [ ] 最近任务 / 最近报告区域
- [ ] 全局任务状态概览卡（依赖 Phase 1 状态层）

#### Round C：报告页优先重构

- [ ] 报告页独立布局（左：结构树，中：预览区，右：导出操作）
- [ ] 报告生成进度流式展示
- [ ] 报告导出功能保留并优化（HTML / PDF / MD）
- [ ] 报告历史列表

#### Round D：洞察 / 媒析 / 检索 / 论坛逐个落地

- [ ] Insight 内页：维度切换 + 趋势图 + 洞察摘要
- [ ] Media 内页：媒体筛选 + 传播图 + 传播诊断
- [ ] Query 内页：强搜索区 + 结果列表 + 详情预览
- [ ] Forum 内页：回合筛选 + 讨论流 + 研判摘要

#### Round E：高保真视觉增强

- [ ] L1 视觉：黑白灰 + 朱砂点缀 + 纸纹背景（部分已完成）
- [ ] L2 视觉：国风边框、题签、印章、山水装饰
- [ ] L3 视觉：动态墨滴、远山视差、复杂动效

### 3.2 SVG 资产管理

- [x] 新建 `templates/assets/svg_assets/` 目录，16 个 SVG 文件
- [x] 后端新增 `/assets/svg/<filename>` 静态路由（`app.py`）
- [ ] 考虑将 SVG 迁移到 `static/` 目录（Flask 原生静态路径，无需自定义路由）
- [ ] SVG 资产清单文档化

已有资产清单：

| 文件名 | 用途 | 接入状态 |
|--------|------|---------|
| `header-bamboo-corner.svg` | 顶栏左右角饰 | 已接入 |
| `logo-seal-red.svg` | 品牌红印 | 已接入 |
| `title-seal-red.svg` | Hero 区印章 | 已接入 |
| `quote-seal-left.svg` | 引言区左侧印章 | 已接入 |
| `quote-boat-landscape.svg` | 引言区右下角小舟山水 | 已接入 |
| `input-ink-mountain.svg` | 搜索区水墨山水背景 | 已接入 |
| `icon-insight-eye.svg` | 洞察引擎图标 | 已接入 |
| `icon-media-brush.svg` | 媒析引擎图标 | 已接入 |
| `icon-query-search.svg` | 检索引擎图标 | 已接入 |
| `icon-forum-chat.svg` | 论坛引擎图标 | 已接入 |
| `icon-report-scroll.svg` | 报告引擎图标 | 已接入 |
| `footer-mountain-left.svg` | 页脚左侧山水 | 已接入 |
| `footer-mountain-right-boat.svg` | 页脚右侧山水小舟 | 已接入 |
| `footer-seal.svg` | 页脚印章 | 已接入 |
| `cloud-flourish.svg` | 云纹装饰 | 已接入 |
| `chart-ink-bamboo-mountain.svg` | 图表区竹山装饰 | 待接入 |

### 3.3 插件化边界

- [ ] 定义模板插件边界
- [ ] 定义工具插件边界
- [ ] 定义 Agent 扩展边界
- [ ] 定义加载、注册、禁用机制

### 3.4 评估与回放

- [ ] 固定样例任务集
- [ ] 结果评分机制
- [ ] 执行轨迹回放
- [ ] Prompt / tool / model 对比评估

### 3.5 管理能力

- [ ] 模板管理
- [ ] 配置管理（当前已有在线 LLM 配置弹窗，可继续增强）
- [ ] 任务审计
- [ ] 运行统计与告警

## 4. 应交付的结果

- [ ] 更完整的产品前端（进行中）
- [ ] 插件机制
- [ ] 评估系统
- [ ] 回放与审计能力

## 5. 完成后的理想结果

- 项目不再只是一个工程样例，而是具备持续运营能力的产品底盘
- 新模板、新工具、新 Agent 的引入成本下降
- 任何一次能力退化都能通过评估与回放定位

## 6. 建议测试

### 前端集成测试

- [ ] 创建任务到查看报告全链路
- [ ] 历史任务列表与详情
- [ ] 任务日志查看
- [ ] 五引擎切换是否正常
- [ ] 系统菜单展开/收起/关闭
- [ ] SVG 资产全部 200 正常返回
- [ ] 移动端基本可用性

### 插件测试

- [ ] 模板插件加载
- [ ] 工具插件加载
- [ ] Agent 扩展装载
- [ ] 插件异常隔离

### 评估测试

- [ ] 固定任务集回放
- [ ] 评分逻辑稳定
- [ ] 不同模型或 prompt 结果可对比

## 7. 本阶段重点 bug 检查

- [ ] 前端展示状态与后端真实状态不一致
- [ ] SVG 资产路由返回 404 或 MIME 类型错误
- [ ] 系统菜单点击穿透或无法关闭
- [ ] 旧脚本与新 DOM 结构不兼容导致功能失效
- [ ] 插件加载顺序导致系统行为异常
- [ ] 评估结果不可复现
- [ ] 回放数据与真实执行轨迹不一致

## 8. 完成判定

- [ ] 核心产品管理能力上线
- [ ] 前端首页与五引擎入口稳定可用
- [ ] 插件和评估机制可运行
- [ ] 关键集成测试通过
- [ ] 本轮日志已归档

## 9. 已完成轮次日志

| 轮次 | 日期 | 范围 | 日志文件 |
|------|------|------|---------|
| Round 01 | 2026-04-22 | 前端规划、功能清单、页面架构冻结 | [round-01](./logs/phase-3/2026-04-22-round-01.md) |
| Round 02 | 2026-04-22 | 首页第一版视觉重构与旧脚本兼容 | [round-02](./logs/phase-3/2026-04-22-round-02.md) |
| Round 03 | 2026-04-22 | 首页第二版视觉重构，代码生成 SVG 装饰 | [round-03](./logs/phase-3/2026-04-22-round-03.md) |
| Round 04 | 2026-04-22 | 首页第三版图标重构，内联 SVG Sprite 化 | [round-04](./logs/phase-3/2026-04-22-round-04.md) |
| Round 05 | 2026-04-22 | 前端多页重构，拆分 6 个独立 HTML 页面 + 5 条 Flask 路由 | [round-05](./logs/phase-3/2026-04-22-round-05.md) |

## 10. 本阶段结束后必须写的日志

- 前端改造范围与实际进度
- SVG 资产接入情况
- 插件机制启用情况
- 评估结果摘要
- 剩余产品化风险
