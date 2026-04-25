# Veyrafish Phase 2 Agent Runtime 升级需求冻结

日期：2026-04-22
运行模式：`/vibe`
主题：InsightEngine 节点级进度事件 + 断点恢复

## 1. Goal

在不重写 InsightEngine 核心逻辑的前提下，让 Agent 执行流：

1. **可追踪**：执行过程中向 `task_store` 的 `task_events` 表写入节点级事件
   （当前处理第几段、第几轮反思、节点名称、状态），前端可实时轮询
2. **可恢复**：`research()` 执行中途失败后，重新调用时从最后一个已完成的段落续跑，
   而不是从头重来

## 2. Deliverables

- `task_store.py`：新增 `task_events` 表 + `add_event` / `list_events` 方法
- `InsightEngine/agent.py`：`research()` 接受可选 `task_id` 参数；
  节点执行前后写入进度事件；支持断点恢复
- `InsightEngine/agent.py`：新增 `research_with_resume(query, task_id)` 便捷方法
- 需求文档（本文）+ 执行计划

## 3. Constraints

- **不改变** InsightEngine 的 `State` / `Paragraph` / `Research` dataclass 结构
- **不改变** 任何 Node 的 `run()` / `mutate_state()` 签名
- **不改变** `app.py` 中已有的路由和接口
- `task_id` 参数可选：不传时行为与现在完全相同，零侵入
- `pytest tests/` 全部通过（无回归）

## 4. task_events 表结构

```
task_events
  event_id    TEXT PRIMARY KEY   -- uuid4
  task_id     TEXT               -- 关联 tasks.task_id（外键，无约束）
  event_type  TEXT               -- node_start | node_done | paragraph_start |
                                 --   paragraph_done | research_start | research_done |
                                 --   error
  node_name   TEXT               -- 节点/步骤名称，如 FirstSearchNode
  paragraph   INTEGER            -- 段落索引（0-based），NULL 表示全局事件
  iteration   INTEGER            -- 反思轮次（0-based），NULL 表示非反思事件
  detail      TEXT               -- JSON：可选额外信息（错误信息、耗时等）
  created_at  TEXT               -- ISO8601 UTC
```

## 5. Acceptance Criteria

- 调用 `agent.research(query, task_id=tid)` 后，`task_events` 表中有
  `research_start` / `paragraph_start` / `node_start` / `node_done` /
  `paragraph_done` / `research_done` 等记录
- 模拟第 2 段落失败：再次调用 `research_with_resume` 时，
  第 1 段落不重新执行（已有 `paragraph_done` 事件），从第 2 段落继续
- 不传 `task_id` 时行为与现有完全一致

## 6. Non-goals

- 本轮不实现 WebSocket 实时推送事件（前端轮询 `/api/system/task/<id>` 即可）
- 本轮不改造 MediaEngine / QueryEngine（InsightEngine 是试点）
- 本轮不实现任意节点级回退（只支持段落级恢复）
