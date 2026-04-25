# Veyrafish Phase 1-L 运行架构升级需求冻结

日期：2026-04-22
运行模式：`/vibe`
主题：长任务抽离 + SQLite 持久化任务状态层

## 1. Goal

把当前 `/api/system/start` 的同步阻塞行为改为后台异步执行，同时引入轻量 SQLite
任务状态层，让引擎启动状态在进程重启后仍可查询，并为前端"最近任务"功能奠基。

## 2. Deliverables

- `task_store.py`：SQLite 任务状态层模块（增删查改 + schema 自动建表）
- `app.py` 局部改造：`/api/system/start` 改为立即返回 + 后台线程执行
- 新接口 `/api/system/task/<task_id>`：查询单次启动任务的进度与结果
- 新接口 `/api/system/tasks`：查询最近 N 次启动任务列表
- 更新 `PHASE_1_IMPLEMENTATION_CHECKLIST.md` + 写 Round 01 日志

## 3. Constraints

- 保留 Flask + Socket.IO，不切换 FastAPI
- 保留 `processes` 内存字典（运行期引擎状态），不替换，只补充持久化
- 保留全部现有路由接口，新接口只新增不修改旧签名
- SQLite 文件路径跟随 `LOG_DIR`，Docker 可通过 volume 挂载持久化
- 不引入 Redis、Celery 等新基础设施
- 测试基线（`pytest tests/`）改造后仍全部通过

## 4. Acceptance Criteria

- `/api/system/start` 在 1 秒内返回 `{"success": true, "task_id": "...", "status": "starting"}`
- 启动过程中 `/api/system/task/<task_id>` 能返回实时状态（starting / running / error）
- 系统重启后，`/api/system/tasks` 仍能返回历史任务记录
- 原有 `/api/status`、`/api/start/<app>`、Socket.IO 事件流全部不受影响
- `pytest tests/ -q` 36/36 通过

## 5. Manual Spot Checks

- 浏览器打开 `http://localhost:5000`，点「保存并启动系统」→ 弹窗不再卡住
- 启动期间访问 `/api/system/task/<id>` → 返回 `status: starting` 或 `running`
- 重启 `python app.py` 后访问 `/api/system/tasks` → 仍可看到上次记录

## 6. Non-goals

- 本轮不迁移 FastAPI
- 本轮不引入 Worker 池或 Celery
- 本轮不切换文件总线通信协议
- 本轮不实现任务取消接口（后续 Round 再做）

## 7. Task State Schema

```
tasks 表
  task_id     TEXT PRIMARY KEY   -- uuid4
  task_type   TEXT               -- "system_start"
  status      TEXT               -- starting | running | completed | error
  created_at  TEXT               -- ISO8601
  updated_at  TEXT               -- ISO8601
  payload     TEXT               -- JSON: 启动参数
  result      TEXT               -- JSON: 启动结果 / 错误信息
```
