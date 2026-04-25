# Veyrafish Phase 1-L 执行计划

日期：2026-04-22
运行模式：`/vibe`
内部执行等级：`L`

## 1. Strategy

渐进式改造，不做大爆炸重写：

1. 先建独立模块 `task_store.py`（可单独测试，不依赖 Flask）
2. 再改 `app.py` 中的 `/api/system/start`（局部替换，影响面最小）
3. 新增两个查询接口（只新增，不改旧路由）
4. 跑 pytest 验证无回归
5. 更新清单和日志

## 2. Waves

### Wave 1：task_store.py（独立模块）

改动范围：只新增文件，不改任何现有文件

- SQLite 连接管理（线程安全，WAL 模式）
- `create_task(task_type, payload) → task_id`
- `update_task(task_id, status, result=None)`
- `get_task(task_id) → dict`
- `list_tasks(limit=20) → list[dict]`
- 自动建表（`CREATE TABLE IF NOT EXISTS`）
- 数据库文件路径：`logs/tasks.db`（跟随 `LOG_DIR`）

### Wave 2：app.py 局部改造

改动范围：仅修改 `start_system()` 路由函数 + 新增 2 个路由

**改造 `/api/system/start`**：
```
旧：同线程 initialize_system_components() → 阻塞 30s → 返回结果
新：立即创建 task_id，写入 task_store，后台 thread 执行 → 1s 内返回
```

**新增 `/api/system/task/<task_id>`**：
- 从 task_store 读取单条记录返回

**新增 `/api/system/tasks`**：
- 从 task_store 读取最近 20 条返回

### Wave 3：验证

- `python -m pytest tests/ -q` → 36/36 通过
- 静态验证：`/api/system/start` 返回字段包含 `task_id`
- 静态验证：旧接口签名未变

## 3. Ownership Boundaries

- 只新增/修改 `task_store.py`、`app.py`
- 不改 `config.py`、`requirements.txt`、任何 Engine 模块、任何 HTML 模板

## 4. Verification

```bash
python -m pytest tests/ -q
python -c "from task_store import TaskStore; ts = TaskStore('logs/tasks.db'); print('OK')"
```

## 5. Rollback Rules

- `task_store.py` 是新文件，回滚只需删除
- `app.py` 中 `start_system()` 只有该函数被修改，可以 git diff 精确回滚

## 6. Cleanup Expectations

- 写 `outputs/runtime/vibe-sessions/20260422-veyrafish-phase1-task-layer/` 收据
- 写 `docs/implementation/logs/phase-1/2026-04-22-round-01.md`
- 更新 `PHASE_1_IMPLEMENTATION_CHECKLIST.md` 勾选项
- 更新 `MASTER_IMPLEMENTATION_CHECKLIST.md` Phase 1 状态
