# Wave 4：ForumEngine 事件驱动 + 三引擎并发

**所属**：Phase 2 二阶段架构升级  
**前置**：Wave 3（三引擎已图谱化）  
**产出**：ForumEngine 事件驱动重构 + 并发调度 + `tests/test_forum_events.py`

---

## 1. 目标

两个高价值改造：
1. **ForumEngine 从日志文件监听升级为事件驱动**：不再读 `.log` 文件，改为从 `task_events` 表订阅结构化事件
2. **三引擎研究任务并发执行**：从串行变为 `ThreadPoolExecutor` 并发，首轮耗时从 `T1+T2+T3` 降到 `max(T1,T2,T3)`

## 2. ForumEngine 事件驱动改造

### 2.1 当前架构

```
insight.log ─┐
media.log  ──┤──→ LogMonitor（文件 tail）──→ 解析 SummaryNode 输出 ──→ 触发主持人
query.log  ──┘
```

问题：
- 依赖文件 IO，容易丢事件（seek 位置不对、文件被清空）
- 解析靠正则匹配日志格式，脆弱
- 日志格式变化会导致 ForumEngine 失灵

### 2.2 目标架构

```
InsightEngine ──┐
MediaEngine  ───┤──→ task_events 表 ──→ ForumEngine.poll_events() ──→ 触发主持人
QueryEngine  ───┘
```

优点：
- 结构化事件（JSON），不依赖日志格式
- task_events 已经被 Wave 3 的 GraphRunner 自动写入
- 天然支持按 task_id 隔离（多个研究任务互不干扰）

### 2.3 具体改造

#### poll_events() 方法

```python
class LogMonitor:
    def poll_events(self, task_ids: list[str], since: str | None = None) -> list[dict]:
        """从 task_events 表查询指定任务的新事件。"""
        store = get_task_store()
        events = []
        for tid in task_ids:
            events.extend(store.list_events(tid, limit=50))
        if since:
            events = [e for e in events if e["created_at"] > since]
        return sorted(events, key=lambda e: e["created_at"])
```

#### 主持人触发条件

```python
# 旧：每 5 条日志行触发
self.host_speech_threshold = 5

# 新：每 N 个 paragraph_done 事件触发
def _should_trigger_host(self, events: list[dict]) -> bool:
    paragraph_dones = [e for e in events if e["event_type"] == "paragraph_done"]
    return len(paragraph_dones) >= self.host_speech_threshold
```

#### 保留 forum.log 兼容层

```python
def _write_to_forum_log_compat(self, content: str, source: str):
    """保留 forum.log 写入，供 Socket.IO → 前端推送使用。"""
    self.write_to_forum_log(content, source)
```

前端仍通过 Socket.IO 读 `forum.log` 推送消息，这部分不改。

### 2.4 双模式切换

```python
class LogMonitor:
    def __init__(self, log_dir="logs", use_event_bus=True):
        self.use_event_bus = use_event_bus
        # ...
    
    def _monitor_loop(self):
        if self.use_event_bus:
            self._event_driven_loop()
        else:
            self._legacy_file_monitor_loop()  # 旧逻辑保留
```

## 3. 三引擎并发调度

### 3.1 当前调度方式

`app.py` 中 `/api/search` 对三引擎是**串行转发**（逐个 `requests.post`）。

### 3.2 目标调度方式

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def dispatch_research_concurrent(query: str, task_ids: dict[str, str]):
    """并发调度三引擎研究任务。"""
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="engine") as pool:
        futures = {}
        for engine_name, task_id in task_ids.items():
            agent = _get_agent(engine_name)
            futures[pool.submit(agent.research, query, task_id=task_id)] = engine_name
        
        results = {}
        for future in as_completed(futures):
            engine = futures[future]
            try:
                results[engine] = future.result()
            except Exception as exc:
                logger.error(f"{engine} 研究任务失败: {exc}")
                results[engine] = None
    return results
```

### 3.3 ForumEngine 与并发的配合

ForumEngine 通过 `poll_events()` 同时监控三个 task_id 的事件流：

```python
# ForumEngine 在并发调度开始时绑定三个 task_id
forum_monitor.bind_tasks([tid_insight, tid_media, tid_query])

# poll_events 自动聚合三个任务的事件
events = forum_monitor.poll_events(
    task_ids=[tid_insight, tid_media, tid_query],
    since=last_poll_time
)
```

## 4. 任务分解

| 编号 | 任务 | 文件 |
|------|------|------|
| W4.1 | `LogMonitor.poll_events()` 方法 | `ForumEngine/monitor.py` |
| W4.2 | 主持人触发条件改为事件驱动 | `ForumEngine/monitor.py` |
| W4.3 | `_event_driven_loop()` 主循环 | `ForumEngine/monitor.py` |
| W4.4 | `use_event_bus` 双模式切换 | `ForumEngine/monitor.py` |
| W4.5 | 保留 `forum.log` 写入兼容层 | `ForumEngine/monitor.py` |
| W4.6 | `dispatch_research_concurrent()` 并发调度函数 | `app.py` 或新建 `veyrafish_core/dispatcher.py` |
| W4.7 | ForumEngine `bind_tasks()` 多任务绑定 | `ForumEngine/monitor.py` |
| W4.8 | 单元测试 | `tests/test_forum_events.py` |

预估改动量：**修改 ~200 行 + 新增 ~100 行 + ~120 行测试**

## 5. 测试计划

```python
# tests/test_forum_events.py

class TestForumEventDriven:
    def test_poll_events_returns_structured_events(self): ...
    def test_host_trigger_on_paragraph_done(self): ...
    def test_event_loop_ignores_old_events(self): ...
    def test_legacy_mode_still_works(self): ...
    def test_forum_log_compat_layer(self): ...

class TestConcurrentDispatch:
    def test_three_engines_concurrent(self): ...
    def test_one_engine_failure_others_continue(self): ...
    def test_task_ids_isolation(self): ...
```

## 6. 验证门禁

```bash
pytest tests/test_forum_events.py -v   # 全部通过
pytest tests/ -q                       # 全量无回归
```

## 7. 回滚方式

- ForumEngine：`use_event_bus=False` 回退到旧的日志文件监听
- 并发调度：改回串行调用（删除 `dispatch_research_concurrent` 相关代码）
