# Phase 3 UI 二阶段执行计划：维舆视觉重构

**需求文档**：`docs/requirements/2026-04-24-veyrafish-ui-phase2-redesign.md`  
**功能矩阵**：`docs/plans/2026-04-24-veyrafish-ui-phase2-function-retention-matrix.md`  
**内部执行等级**：L  
**日期**：2026-04-24  
**当前进度**：Wave 1 全局底座与 Wave 2 总览页第一段已实施  
**运行模式**：`$vibe`

---

## 1. Strategy

本轮按“先稳定底座，再重构入口与出口，再处理协作页，最后统一引擎页”的方式推进。

执行顺序已确认：

1. 全局底座
2. 总览页
3. 报告页
4. 论坛页
5. 洞察 / 媒析 / 检索

核心原则：视觉升级可以大胆，但真实功能链路必须保守。

## 2. Wave 0：功能确认门

**目标**：由用户确认哪些功能保留、收纳、延后或移除。

| 编号 | 任务 | 文件 |
|---|---|---|
| W0.1 | 整理现有功能清单 | `docs/plans/2026-04-24-veyrafish-ui-phase2-function-retention-matrix.md` |
| W0.2 | 给出保留建议与风险 | 同上 |
| W0.3 | 用户确认后冻结需求文档状态 | `docs/requirements/...ui-phase2-redesign.md` |

**出口条件**：用户明确确认功能保留范围。

**结果**：已确认“按矩阵执行”。

## 3. Wave 1：全局底座

**目标**：先让所有页面拥有统一品牌与素材访问能力。

| 编号 | 任务 | 文件 |
|---|---|---|
| W1.1 | 新增 PNG 素材路由 `/assets/png/<filename>` | `app.py` |
| W1.2 | 新增或重构共享 CSS | `static/engine-shared.css` 或新增 `static/veyu-ui.css` |
| W1.3 | 统一品牌常量、Header、Footer、背景装饰 | `templates/*.html` |
| W1.4 | 保留系统菜单、配置弹窗、关机确认弹窗可用 | `templates/*.html`, `static/engine-shared.js` |

**建议**：优先新增 `static/veyu-ui.css` 覆盖视觉，减少对旧 CSS 的破坏。

## 4. Wave 2：总览页

**目标**：把 `/` 做成演示第一屏。

| 编号 | 任务 | 文件 |
|---|---|---|
| W2.1 | 重构总览页布局为双上卡 + 五引擎入口 | `templates/index.html` |
| W2.2 | 保留议题输入、模板上传、LLM 配置、启动系统 | `templates/index.html` |
| W2.3 | 增加演示 KPI/趋势/洞察概览区 | `templates/index.html` |
| W2.4 | 五引擎入口保留真实跳转与状态 | `templates/index.html` |

## 5. Wave 3：报告页

**目标**：把成果出口做成“宣纸报告预览 + 真实导出控制”。

| 编号 | 任务 | 文件 |
|---|---|---|
| W3.1 | 重构三栏布局与报告纸张视觉 | `templates/report.html` |
| W3.2 | 保留生成报告、SSE/轮询、进度、预览 | `templates/report.html` |
| W3.3 | 保留 HTML/PDF/MD 下载与模板上传 | `templates/report.html` |
| W3.4 | 导出与定稿区按参考图视觉重排 | `templates/report.html` |

## 6. Wave 4：论坛页

**目标**：保留真实消息流，同时增加论坛研判演示面板。

| 编号 | 任务 | 文件 |
|---|---|---|
| W4.1 | 重构论坛三栏布局 | `templates/forum.html` |
| W4.2 | 保留实时消息流、刷新、清空、消息统计 | `templates/forum.html` |
| W4.3 | 加入演示态热帖、阵营、温度、热词区域 | `templates/forum.html` |
| W4.4 | 控制台日志改为可折叠或低干扰区域 | `templates/forum.html` |

## 7. Wave 5：洞察 / 媒析 / 检索

**目标**：统一三个引擎页视觉，不强接复杂真实图表。

| 编号 | 任务 | 文件 |
|---|---|---|
| W5.1 | 洞察页增加 KPI、趋势、风险矩阵演示层 | `templates/insight.html` |
| W5.2 | 媒析页增加传播路径、排行、诊断演示层 | `templates/media.html` |
| W5.3 | 检索页保留真实 Query iframe 入口，增加聚类/结果列表演示层 | `templates/query.html` |
| W5.4 | 保留三页 iframe 工作区与未运行占位态 | `templates/*.html` |

## 8. Verification Commands

```powershell
python -m pytest
python -c "import app; print('app import ok')"
python app.py
```

手工验收：

- 浏览器打开 `/`
- 打开 `/insight`, `/media`, `/query`, `/forum`, `/report`
- 检查系统配置弹窗、启动系统、关闭确认、日志、Forum、Report 导出链路

## 9. Ownership Boundaries

- 前端模板：`templates/*.html`
- 新素材：`templates/assets/png/*`
- 共享样式：`static/engine-shared.css` 或 `static/veyu-ui.css`
- 后端仅允许小改静态素材路由：`app.py`
- 不改 Agent / Skill / ReportEngine 核心流程

## 10. Rollback Rules

- 若某页功能断裂，优先回退该页模板，不回退全局底座。
- 若共享 CSS 影响过大，优先禁用新增覆盖样式，而不是改旧 JS。
- 若素材路由异常，先回退为直接 `/static/` 资源路径。

## 11. Phase Cleanup Expectations

每个 wave 完成后记录：

- 修改文件列表
- 测试/手工验收结果
- 功能保留矩阵状态变化
- `$vibe` runtime receipt

