# Veyrafish Phase 2 执行计划

日期：2026-04-22
运行模式：`/vibe`
内部执行等级：`L`

## 1. Strategy

最小侵入原则：所有改动通过**参数注入**和**外层包裹**完成，核心节点逻辑零修改。

## 2. Waves

### Wave 1：task_store.py 扩展

新增 `task_events` 表及其操作方法。不修改现有 `tasks` 表和方法。

- `_init_events_table()`：`CREATE TABLE IF NOT EXISTS task_events`
- `add_event(task_id, event_type, node_name, paragraph, iteration, detail) → event_id`
- `list_events(task_id, limit) → list[dict]`
- 在 `TaskStore.__init__` 中调用 `_init_events_table()`

### Wave 2：InsightEngine/agent.py 改造

**Step 2a：`research()` 接受 `task_id` 参数**

```python
def research(self, query: str, save_report: bool = True,
             task_id: Optional[str] = None) -> str
```

**Step 2b：在关键节点前后写入事件**

包裹位置：
- `research()` 入口 → `research_start`
- `_generate_report_structure()` 完成后 → 每个段落记录 `paragraph_start` 事件
- `_initial_search_and_summary()` 前后 → `node_start/node_done` (FirstSearchNode, FirstSummaryNode)
- `_reflection_loop()` 每轮前后 → `node_start/node_done` (ReflectionNode, ReflectionSummaryNode)
- `_process_paragraphs()` 每段完成 → `paragraph_done`
- `_generate_final_report()` 完成 → `research_done`
- 任何 Exception → `error` 事件

**Step 2c：断点恢复逻辑**

新增 `research_with_resume(query, task_id)`:
1. 从 `task_events` 查询已完成的段落集合（有 `paragraph_done` 事件的段落 index）
2. 若状态已有段落数据（从 State 文件或重新生成结构），跳过已完成的段落
3. 从第一个未完成段落继续执行

具体实现：改造 `_process_paragraphs()` 接受 `skip_indices: set[int]` 参数

### Wave 3：验证

- `python -m pytest tests/ -q` → 61+ 通过
- 静态验证：`InsightEngine/agent.py` 中 `research()` 签名向后兼容

## 3. Ownership Boundaries

- 修改：`task_store.py`、`InsightEngine/agent.py`
- 不修改：所有 Node 文件、`state/state.py`、`app.py`、任何 HTML 模板

## 4. Rollback Rules

- `task_store.py` 扩展是纯新增（新表新方法），回滚只需删除新增代码
- `InsightEngine/agent.py` 改造通过默认参数保持向后兼容，回滚删除新增逻辑即可

## 5. Cleanup Expectations

- 写 `outputs/runtime/vibe-sessions/20260422-veyrafish-phase2-agent-runtime/` 收据
- 写 `docs/implementation/logs/phase-2/2026-04-22-round-01.md`
- 更新 `PHASE_2_IMPLEMENTATION_CHECKLIST.md`
- 更新 `MASTER_IMPLEMENTATION_CHECKLIST.md`
