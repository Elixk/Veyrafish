# Veyrafish UI 重构（系统控制层收纳）执行计划

日期：2026-04-22  
运行模式：`/vibe`  
内部执行等级：`M`

## 1. Strategy

以“**不破坏既有功能链路**”为最高优先级：保留原按钮 `id` 与事件绑定，只做 UI 结构与交互壳层重构，把系统控制层从主视觉中收纳起来。

## 2. Steps

- **Step A：基线确认**
  - 阅读 `templates/index.html` 中 `utility-actions`、相关 CSS、以及 `DOMContentLoaded` 初始化逻辑
  - 明确受影响元素：`pageRefreshButton`、`openConfigButton`、`shutdownButton`

- **Step B：实现系统菜单**
  - 将三按钮收纳进 `utility-popover`
  - 新增触发按钮 `utilityMenuTrigger` 与关闭按钮 `utilityMenuClose`
  - 增加交互：点击外部关闭、`Esc` 关闭、ARIA 属性同步

- **Step C：回归验证（手工）**
  - 启动后端并访问首页，验证菜单交互与按钮功能不回归

## 3. Ownership Boundaries

- 仅修改 `templates/index.html`（HTML/CSS/JS 同文件内）
- 不修改后端 Python 代码，不改 API

## 4. Verification

- 运行：

```bash
python app.py
```

- 打开首页后按需求文档执行手工 spot checks

## 5. Rollback Rules

- 若出现按钮失效/菜单阻断点击：优先恢复旧的 `utility-actions` 结构（保持原按钮直接可见），再逐步引入菜单行为

## 6. Cleanup Expectations

- 写入本轮 `outputs/runtime/vibe-sessions/...` 的治理收据、阶段记录与 cleanup receipt

