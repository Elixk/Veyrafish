# Phase 3 执行计划：稳定、可演示、可复现

**需求文档**：`docs/requirements/2026-04-24-veyrafish-phase3-stabilize-demo-reproducible.md`  
**内部执行等级**：L（串行三轮推进，局部任务可并行检查）  
**日期**：2026-04-24  
**运行模式**：`$vibe`

---

## 1. 执行策略

Phase 3 不继续做大架构跃迁，而是按“能演示、能复现、能部署调试”的顺序推进。

建议拆成 5 个波次：

1. **Wave 1：前端界面重构轮**
2. **Wave 2：Skill 完善应用轮**
3. **Wave 3：系统稳定轮**
4. **Wave 4：Docker 部署调试准备与执行**
5. **Wave 5：操作文档、技术文档与演示材料**

前三波属于 Phase 3 主体；Wave 4 和 Wave 5 是 Phase 3 之后的交付收口阶段，但计划中提前定义接口，避免返工。

## 2. Wave 1：前端界面重构轮

**目标**：让界面从“控制台堆叠”变成“可演示的舆情分析工作台”。

### 任务

| 编号 | 任务 | 主要文件/目录 |
|------|------|---------------|
| W1.1 | 盘点 `templates/index.html` 当前按钮、API 调用和视图状态 | `templates/index.html`, `app.py` |
| W1.2 | 定义首页信息架构：系统状态、任务入口、实时进度、报告结果 | `docs/前端设计参考/`, `templates/` |
| W1.3 | 重构系统控制区，区分产品操作和运维操作 | `templates/index.html`, `static/` |
| W1.4 | 重构任务进度和 Forum 日志展示，让演示路径更顺 | `templates/index.html`, `app.py` |
| W1.5 | 重构报告入口和最近结果展示，减少寻找成本 | `templates/index.html` |
| W1.6 | 做桌面端和移动端手动检查，修复文本重叠、按钮溢出、状态不可读 | `templates/`, `static/` |

### 验证

```powershell
python -m pytest
python app.py
```

手动检查：

- 浏览器打开主页。
- 检查启动系统、配置状态、发起分析、进度查看、报告查看。
- 检查桌面和窄屏布局。

### 完成判定

- 原功能不退化。
- 演示主路径更清楚。
- 前端没有明显视觉崩坏或按钮不可用。

### 回滚规则

- 前端重构按区块提交，任何区块出问题可回退到旧区块结构。
- 不改后端 API 语义，除非已有测试覆盖。

## 3. Wave 2：Skill 完善应用轮

**目标**：让 Skill 从“有一组能力”变成“主链路中有可解释价值的能力层”。

### 当前 Skill 分层建议

| Skill | 当前定位 | Phase 3 建议 |
|------|----------|--------------|
| `query_rewrite` | 主链路已接入 | 增强前端可观测字段，展示改写理由、约束、工具选择 |
| `llm_summarize` | 主链路已接入 | 稳定结构化输出和降级摘要，作为报告质量基线输入 |
| `evidence_extract` | evidence sink 已接入 | 强化来源绑定，将证据摘要暴露给调试/报告上下文 |
| `gap_finder` | 反思阶段已接入 | 把 conflict/recency/coverage gap 用于演示和报告保守表达 |
| `quality_gate` | 摘要门禁已接入 | 输出 issue 与 score，作为前端或日志可展示诊断 |
| `web_search` | 能力存在，主链路未默认替换 | 暂不强行替换原搜索工具，先做调试入口或统一适配层评估 |
| `sentiment_analysis` | 备用 NLP 能力 | 优先接入报告/Forum 辅助统计，而不是主流程强依赖 |

### 任务

| 编号 | 任务 | 主要文件/目录 |
|------|------|---------------|
| W2.1 | 写当前 Skill 状态表，明确主链路、调试链路、备用能力 | `docs/SKILL_DEVELOPMENT_GUIDE.md` 或新文档 |
| W2.2 | 为 `query_rewrite` / `quality_gate` / `gap_finder` 增加可观测输出路径 | `veyrafish_core/`, `app.py`, `templates/` |
| W2.3 | 评估 `web_search` 是否适合作为统一搜索适配层，不直接替换成熟路径 | `veyrafish_core/skills/web_search.py` |
| W2.4 | 评估 `sentiment_analysis` 接入 Forum 或报告统计的最小路径 | `ForumEngine/`, `ReportEngine/` |
| W2.5 | 补充测试，确保 Skill 失败时回退稳定 | `tests/test_skill.py`, `tests/test_graph_integration.py` |

### 验证

```powershell
python -m pytest tests/test_skill.py -v
python -m pytest tests/test_graph_integration.py -v
python -m pytest
```

### 完成判定

- 不以新增 Skill 数量作为成果。
- 至少让 2-3 个 Skill 的输出能被主链路、日志、前端或报告真实消费。
- 失败降级不破坏端到端流程。

### 回滚规则

- Skill 增强必须是增强路径，任何失败都回退到原有主链路。
- 不在本轮强制替换搜索、报告生成等高风险核心路径。

## 4. Wave 3：系统稳定轮

**目标**：把本地运行从“开发者知道怎么跑”变成“别人按检查清单也能跑”。

### 任务

| 编号 | 任务 | 主要文件/目录 |
|------|------|---------------|
| W3.1 | 新增启动自检：依赖、端口、目录、配置、API Key 缺失提示 | `scripts/`, `app.py`, `config.py` |
| W3.2 | 固化本地演示命令和固定样例输入 | `scripts/`, `docs/`, `outputs/` |
| W3.3 | 检查错误提示：缺依赖、缺 key、端口占用、子进程启动失败 | `app.py`, `config.py` |
| W3.4 | 增加最小端到端验收脚本或手动验收表 | `scripts/`, `docs/implementation/` |
| W3.5 | 清理临时输出和历史调试残留，只保留必要样例 | `.tmp_*`, `logs/`, `outputs/` |

### 验证

```powershell
python -m pytest
python scripts/<startup-check-script>.py
python app.py
```

手动验收：

- 新环境缺依赖时能快速定位。
- `.env` 缺关键字段时有明确提示。
- 本地能完成一次演示流程。

### 完成判定

- Phase 3 主体完成后，可以明确说：`本地演示链路通过`。
- 若真实 LLM 未验证，只能说：`mock/本地流程通过，真实 LLM 待验收`。

### 回滚规则

- 启动自检必须只提示或阻断明确不可运行的问题，不能误伤可降级运行场景。
- 清理动作必须先确认目标路径，避免删除用户数据或最终报告。

## 5. Wave 4：Docker 部署调试

**进入条件**：

- Wave 1-3 门禁通过。
- 本地端到端演示流程完成。
- 启动自检能说明当前环境状态。

### 任务

| 编号 | 任务 | 主要文件/目录 |
|------|------|---------------|
| W4.1 | 核查 Dockerfile、docker-compose.local.yml、requirements/pyproject 一致性 | `Dockerfile`, `docker-compose.local.yml`, `requirements.txt`, `pyproject.toml` |
| W4.2 | 明确容器环境变量和数据卷 | `.env.example`, Docker 配置 |
| W4.3 | 容器内运行启动自检和单元测试 | Docker 容器 |
| W4.4 | 容器内启动 Web，验证 `/api/system/start` 和主页 | Docker 容器 |
| W4.5 | 记录 Docker 调试问题清单和修复结果 | `docs/implementation/` |

### 验证

```powershell
docker compose -f docker-compose.local.yml up --build
```

检查：

- Web 服务可访问。
- 子进程或降级模式行为明确。
- 数据目录挂载正常。
- 日志能追踪启动失败原因。

## 6. Wave 5：文档与演示材料

**进入条件**：

- Docker 调试链路至少完成一轮。
- 操作步骤已经通过真实命令验证。

### 文档清单

| 文档 | 内容 |
|------|------|
| 操作文档 | 环境准备、配置 API Key、启动、发起任务、查看报告、常见问题 |
| 技术文档 | 架构图、模块职责、TaskStore、Graph、Skill、Evidence、ReportEngine |
| 部署文档 | Docker、本地运行、环境变量、端口、数据目录、日志位置 |
| 演示脚本 | 5 分钟演示流程、关键话术、异常预案 |
| 验收报告 | 测试结果、端到端结果、Docker 结果、残余风险 |

### 完成判定

- 文档命令和真实命令一致。
- 文档中的截图或输出来自当前版本。
- 能支持别人独立复现一次演示。

## 7. Verification Commands

常规门禁：

```powershell
python -m pytest
python -c "from veyrafish_core.skills import default_registry; print(default_registry.names())"
python -c "from veyrafish_core.llm_client import LLMClient; print('llm client import ok')"
```

前端/产品门禁：

```powershell
python app.py
```

Docker 门禁：

```powershell
docker compose -f docker-compose.local.yml up --build
```

## 8. Ownership Boundaries

- 前端轮主要触碰：`templates/`, `static/`, 必要时 `app.py` 的展示 API。
- Skill 轮主要触碰：`veyrafish_core/skills/`, `veyrafish_core/base_research_agent.py`, `tests/`。
- 稳定轮主要触碰：`scripts/`, `config.py`, `app.py`, `docs/implementation/`。
- Docker 轮主要触碰：`Dockerfile`, `docker-compose*.yml`, `.env.example`, 依赖文件。
- 文档轮主要触碰：`docs/`, `README*`, 演示材料目录。

## 9. Rollback Rules

- UI 改造按功能区回滚，不回滚后端稳定改动。
- Skill 接入必须保留 fallback；单个 Skill 出问题不影响主流程运行。
- 稳定性脚本必须非破坏性运行；清理类脚本必须显式限制路径。
- Docker 修改不反向污染本地运行路径。
- 文档更新不作为功能完成证据，必须绑定真实验收记录。

## 10. Phase Cleanup Expectations

每一波结束时必须留下：

- 本波改动摘要。
- 执行过的验证命令。
- 手动检查结果。
- 未完成项和残余风险。
- 临时文件清理结果。

Phase 3 主体结束时必须留下：

- 前端重构验收记录。
- Skill 应用状态表。
- 系统稳定验收记录。
- Docker 调试准备清单。
- 文档写作输入清单。

## 11. Recommended Sequence

最推荐的顺序：

1. 先做前端重构，因为它直接影响演示体验。
2. 再做 Skill 应用，因为它能增强演示时的技术含金量。
3. 最后做系统稳定，因为它要吸收前两轮改动后的真实风险。
4. 然后进 Docker，解决环境复现问题。
5. 最后写文档，确保文档来自真实步骤。

不要把 Docker 和文档提前做成主任务；它们应该吃到 Phase 3 的稳定成果。
