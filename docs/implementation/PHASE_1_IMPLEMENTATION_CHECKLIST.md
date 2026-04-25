# Phase 1 实施清单：运行架构升级

**状态**：完成（核心）（Round 01-02 完成任务状态层 + 长任务抽离 + zombie 清理；完整 API/Worker 架构仍为后续优化）

## 1. 阶段目标

把当前的 `Flask + Streamlit 子进程 + 文件总线` 升级为可维护的 `API + Worker + 任务状态层` 架构。
本阶段选择 P1-L（标准）级别：保留 Flask，引入 SQLite 任务状态层，不引入 FastAPI / Celery。

> 验收校准：Phase 1 的完成结论仅限“核心运行架构改良完成”，不是完整 API-first / Worker / 事件流架构完成。

## 2. 开始条件

- [x] Phase 0 已基本完成（依赖/测试/配置治理核心项完成，trace id 暂不阻塞）
- [x] 配置和测试基线已建立（36/36 pytest 通过）
- [ ] 关键数据模型初版定义（任务模型已在 task_store.py 定义，Agent 输出模型待 Phase 0 Round 02）

## 3. 本阶段必须完成的任务

### 3.1 API 层升级

- [ ] 设计新的 API 目录结构（P1-L 暂保留 app.py 单文件，后续 Round 可拆模块）
- [ ] 将主编排入口从 `app.py` 迁移为 API-first 结构（P1-L 保留 Flask，旧路由不动）
- [x] 定义统一请求与响应模型（`task_store.py` 的 dict 结构即为本阶段任务响应模型）
- [x] 保留旧接口的兼容策略（所有旧路由签名未变，向后兼容）
- [ ] 补 API 文档或 OpenAPI Schema（待后续 Round）

### 3.2 任务执行层抽离

- [x] 将长任务从请求线程中抽离（`/api/system/start` 改为后台 Thread 执行，2026-04-22 Round 01）
- [x] 设计 Worker 执行边界（`threading.Thread` 后台执行，与 Flask 请求线程隔离）
- [x] 定义任务创建、查询状态接口（`POST /api/system/start` + `GET /api/system/task/<id>` + `GET /api/system/tasks`）
- [ ] 设计开发模式与生产模式的差异（暂用同一模式）
- [ ] 验证任务超时与取消机制（待后续 Round）

### 3.3 状态层建设

- [x] 建立任务状态存储（`task_store.py` SQLite，`logs/tasks.db`，2026-04-22 Round 01）
- [ ] 建立事件流或事件表（暂用 Socket.IO 推送，结构化事件表待后续）
- [ ] 让 Forum 协作与 Report 输入优先读取状态层（依赖 Agent 输出模型，待后续）
- [ ] 降低对 `forum.log` 与 `*_streamlit_reports` 的核心依赖（文件总线保留为兼容层，待后续）
- [x] 验证状态层在进程重启后的持久性（SQLite 文件持久化，跨重启可查）

### 3.4 旧运行模式兼容

- [x] 明确旧模式保留范围（`processes` 内存字典保留，Socket.IO 事件流保留，所有旧路由保留）
- [x] 提供迁移路径（新旧并存：内存状态读写不变，新增 SQLite 持久化层）
- [ ] 逐步将"文件协议"降级为兼容层（待后续 Round）
- [x] 验证旧系统主流程仍能跑通（`pytest tests/ -q` → 36/36 通过）

## 4. 应交付的结果

- [x] 新任务状态层（`task_store.py`）
- [x] 长任务抽离（`/api/system/start` 改为非阻塞）
- [x] 任务查询接口（`/api/system/task/<id>`、`/api/system/tasks`）
- [ ] Worker 层完整实现（当前用 Thread，后续可升级为 ThreadPoolExecutor）
- [ ] 兼容旧系统的完整迁移方案文档

## 5. 完成后的理想结果

- [x] 发起任务不再直接绑死在 Web 请求上（`/api/system/start` 1 秒内返回）
- [x] 任务状态有明确查询入口（`/api/system/task/<id>`）
- [ ] ReportEngine 不再靠扫目录判断输入是否齐全（依赖 Agent 输出模型，待后续）
- [ ] Forum 协作和 Agent 结果可以通过结构化状态追踪（待后续）

## 6. 建议测试

### API 测试

- [x] 任务创建（`task_store.create_task()` 单元测试通过）
- [x] 查询任务状态（`task_store.get_task()` 单元测试通过）
- [ ] 取消任务（接口待实现）
- [ ] 获取任务事件流（SSE 通道待接入）

### Worker 测试

- [x] 单任务正常执行（后台 Thread 执行，pytest 回归通过）
- [ ] 任务失败重试（待后续）
- [ ] 任务取消（待后续）
- [ ] 并发任务隔离（`_prepare_system_start()` 锁已有，未覆盖并发测试）

### 状态层测试

- [x] 任务状态写入与更新（`task_store.py` 断言测试通过）
- [ ] 事件顺序性（待补充契约测试）
- [x] 状态恢复（SQLite 持久化，跨重启验证通过）
- [ ] 报告读取路径切换后是否稳定（待后续）

### 回归测试

- [x] 现有用户查询主流程是否仍能跑通（`pytest tests/ -q` → **36/36 passed**）
- [x] 旧路由签名未变（静态验证通过）

## 7. 本阶段重点 bug 检查

- [ ] Web 端与 Worker 的任务状态不一致（任务状态存 SQLite，进程内状态在内存，需注意双写一致性）
- [ ] 任务取消后仍然继续执行（当前无取消机制，后续实现时需注意）
- [x] 事件流丢失（Socket.IO 仍为主通道，未引入新通道，无丢失风险）
- [x] 旧文件协议与新状态层并存不冲突（只新增，旧逻辑不变）

## 8. 完成判定

- [x] 长任务已从请求线程中剥离（`/api/system/start` 改为后台执行）
- [x] 任务状态层已成为有效辅助层（SQLite 持久化 + 单元测试覆盖 + zombie 清理）
- [ ] 任务状态层完全成为主通路（主状态仍在内存 `processes`，文件总线降级待后续）
- [ ] 文件总线降为兼容或观察用途（待后续）
- [x] 关键 API 和状态层测试通过（pytest **61/61** 通过）
- [x] 本轮日志已归档（Round 01 + Round 02）

## 9. 已完成轮次日志

| 轮次 | 日期 | 范围 | 日志文件 |
|------|------|------|---------|
| Round 01 | 2026-04-22 | task_store.py + `/api/system/start` 抽离 + 2 条查询接口 | [round-01](./logs/phase-1/2026-04-22-round-01.md) |
| Round 02 | 2026-04-22 | zombie task 清理 + `tests/test_task_store.py`（25 个测试） | [round-02](./logs/phase-1/2026-04-22-round-02.md) |

## 10. 本阶段结束后必须写的日志

- API 迁移范围与结果
- 状态层切换结果
- 与旧模式兼容的风险点
- 已知 bug 与下一轮清理项
