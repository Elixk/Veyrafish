# Veyrafish UI 重构（系统控制层收纳）需求冻结

日期：2026-04-22  
运行模式：`/vibe`  
主题：将首页右上角“系统控制层操作”从显性按钮区收纳为系统菜单，降低干扰并提升可用性（不破坏既有功能链路）

## 1. Goal

- 将首页右上角的 **刷新/系统配置/关闭系统** 从一排按钮重构为“系统菜单（popover/抽屉）”入口
- 保持现有前端业务逻辑（按钮 `id`、事件绑定、API 调用）不变，避免功能回归
- 补齐可用性：点击外部关闭、`Esc` 关闭、ARIA 标注

## 2. Deliverables

- `templates/index.html`：系统菜单 UI（HTML/CSS/JS）重构完成
- `docs/plans/2026-04-22-veyrafish-ui-refactor-execution-plan.md`：本轮执行计划
- `outputs/runtime/vibe-sessions/20260422-veyrafish-ui-refactor-system-menu/*`：治理收据与阶段记录

## 3. Constraints

- 不改后端接口，不调整 API 路径与参数
- 不改动既有关键按钮的 `id`（如 `pageRefreshButton`、`openConfigButton`、`shutdownButton`）
- 不引入前端打包工具与新依赖（保持单文件模板体系）
- 仅进行“系统控制层 UI 收纳与交互补齐”，不做整站视觉大改

## 4. Acceptance Criteria

- 系统菜单默认收起，点击“系统”按钮可展开/收起
- 菜单展开后：
  - 点击页面其他区域会关闭菜单
  - 按 `Esc` 会关闭菜单且焦点回到触发按钮
  - 菜单内三个操作按钮均可正常触发既有逻辑（刷新、打开配置、关闭系统）
- 不影响现有 Socket、控制台、论坛、报告、iframe 等主工作区功能

## 5. Manual Spot Checks

- 打开首页：右上角只有“系统”入口，不再直接暴露“关闭系统”
- 展开菜单：点“系统配置”应正常打开配置弹窗
- 展开菜单：点“刷新界面”应走既有安全刷新逻辑
- 展开菜单：点“关闭系统”应弹出既有关机确认弹窗

## 6. Non-goals

- 不在本轮拆分为多页面路由
- 不在本轮抽离/重写巨量内联 CSS/JS
- 不在本轮实现高保真水墨动效或更换设计语言

