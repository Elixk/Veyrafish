# Veyrafish Docker 部署与调试指南

**文档版本**：2026-04-24  
**适用范围**：Veyrafish 当前仓库 Dockerfile、docker-compose、PostgreSQL 容器和本地/服务器 Docker 调试  
**重要状态**：当前项目已有 Docker 配置，但 Docker 正式验收尚未完成。本文是部署与调试指南，不代表当前环境已实机通过。

## 1. 部署前置条件

### 1.1 必备软件

部署机器需要：

- Docker Engine
- Docker Compose v2
- 可访问镜像源或可本地构建镜像
- 至少 4GB 可用内存，建议更高
- 可用磁盘空间用于数据库、日志、报告和镜像层

检查命令：

```powershell
docker --version
docker compose version
```

Linux 服务器上通常还需要确认当前用户有 Docker 权限：

```bash
docker ps
```

### 1.2 端口要求

Veyrafish 默认暴露以下端口：

| 端口 | 服务 |
|---|---|
| `5000` | Flask 主应用 |
| `8501` | Insight Streamlit |
| `8502` | Media Streamlit |
| `8503` | Query Streamlit |
| `5444` | `docker-compose.yml` 中宿主机 PostgreSQL 端口 |
| `5544` | `docker-compose.local.yml` 中宿主机 PostgreSQL 端口 |

如果端口被占用，需要修改 compose 文件左侧宿主机端口，例如：

```yaml
ports:
  - "15000:5000"
```

容器内部端口不要随意改，`app.py` 和 Streamlit 管理逻辑默认使用 5000/8501/8502/8503。

## 2. Docker 相关文件

| 文件 | 用途 |
|---|---|
| `Dockerfile` | 构建 Veyrafish 应用镜像 |
| `docker-compose.yml` | 使用远程镜像 `ghcr.io/elixk/veyrafish:latest` 的部署方式 |
| `docker-compose.local.yml` | 本地源码构建/挂载的开发部署方式 |
| `.env.example` | 环境变量模板 |
| `.dockerignore` | Docker 构建上下文忽略规则 |

### 2.1 Dockerfile 设计说明

当前 Dockerfile 基于：

```dockerfile
python:3.11-slim-bookworm
```

它做了这些事：

- 设置 Python 不写 pyc、stdout/stderr 不缓冲。
- 设置 `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`。
- 安装 WeasyPrint、Playwright、科学计算和 Streamlit 常见系统依赖。
- 使用清华 Debian 镜像源提升 apt 稳定性。
- 安装 `uv`。
- 使用 `uv pip install --system -r requirements.txt` 安装 Python 依赖。
- 默认跳过 Playwright Chromium 浏览器下载。
- 复制 `.env.example` 为 `.env`。
- 复制项目源码。
- 创建运行目录。
- 暴露 5000、8501、8502、8503。
- 默认执行 `python app.py`。

### 2.2 Playwright 浏览器下载开关

Dockerfile 中：

```dockerfile
ARG INSTALL_PLAYWRIGHT_BROWSERS=0
```

默认不下载 Chromium，因为很多网络环境访问 Playwright 下载源会失败。

如部署需要容器内爬虫浏览器能力，可构建时启用：

```bash
docker build --build-arg INSTALL_PLAYWRIGHT_BROWSERS=1 -t veyrafish:local .
```

如果网络环境不稳定，建议先保持默认，待应用主流程跑通后再单独处理 Playwright 浏览器。

## 3. 环境变量

### 3.1 创建 `.env`

首次部署：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

### 3.2 Docker 下数据库配置

如果使用 compose 中的 `db` 服务，应用容器访问数据库时应配置：

```env
DB_DIALECT=postgresql
DB_HOST=db
DB_PORT=5432
DB_USER=veyrafish
DB_PASSWORD=veyrafish
DB_NAME=veyrafish
DB_CHARSET=utf8mb4
```

同时 PostgreSQL 容器使用：

```env
POSTGRES_USER=veyrafish
POSTGRES_PASSWORD=veyrafish
POSTGRES_DB=veyrafish
POSTGRES_PORT=5444
```

注意：

- `DB_PORT` 是应用容器访问数据库容器的端口，应使用 `5432`。
- `POSTGRES_PORT` 是宿主机访问 PostgreSQL 的映射端口，生产 compose 默认 `5444`，local compose 默认 `5544`。
- `DB_HOST=localhost` 在容器内通常是错的，因为 localhost 指向应用容器自己，不是数据库容器。

### 3.3 LLM 和搜索配置

至少需要根据要跑的链路配置：

```env
INSIGHT_ENGINE_API_KEY=
INSIGHT_ENGINE_BASE_URL=
INSIGHT_ENGINE_MODEL_NAME=

MEDIA_ENGINE_API_KEY=
MEDIA_ENGINE_BASE_URL=
MEDIA_ENGINE_MODEL_NAME=

QUERY_ENGINE_API_KEY=
QUERY_ENGINE_BASE_URL=
QUERY_ENGINE_MODEL_NAME=

REPORT_ENGINE_API_KEY=
REPORT_ENGINE_BASE_URL=
REPORT_ENGINE_MODEL_NAME=

FORUM_HOST_API_KEY=
FORUM_HOST_BASE_URL=
FORUM_HOST_MODEL_NAME=

TAVILY_API_KEY=
SEARCH_TOOL_TYPE=AnspireAPI
ANSPIRE_API_KEY=
BOCHA_WEB_SEARCH_API_KEY=
```

最小启动不一定需要所有 Key，但真实端到端演示需要三引擎、Forum 和 Report 相关 Key 都可用。

### 3.4 不要提交真实 `.env`

`.env` 应仅存在于部署环境中，不应提交到代码仓库或写入文档。

## 4. 服务拓扑

Docker Compose 中有两个服务：

```text
veyrafish
  - Flask 主应用
  - 子进程启动三个 Streamlit Agent
  - ForumEngine
  - ReportEngine Blueprint

db
  - PostgreSQL 15
  - 持久化到 ./db_data
```

运行后拓扑：

```mermaid
flowchart TD
    Browser[Browser] --> V[veyrafish container]
    V --> Flask[Flask :5000]
    Flask --> I[Insight Streamlit :8501]
    Flask --> M[Media Streamlit :8502]
    Flask --> Q[Query Streamlit :8503]
    V --> Logs[/app/logs]
    V --> Reports[/app/final_reports]
    V --> DB[(db:5432)]
    DB --> Data[./db_data]
```

## 5. 端口与数据卷

### 5.1 生产 compose 数据卷

`docker-compose.yml` 中应用服务挂载：

| 宿主机 | 容器 | 用途 |
|---|---|---|
| `./logs` | `/app/logs` | 日志、`tasks.db` |
| `./final_reports` | `/app/final_reports` | 最终报告 |
| `./.env` | `/app/.env` | 运行配置 |
| `./insight_engine_streamlit_reports` | `/app/insight_engine_streamlit_reports` | Insight 中间报告 |
| `./media_engine_streamlit_reports` | `/app/media_engine_streamlit_reports` | Media 中间报告 |
| `./query_engine_streamlit_reports` | `/app/query_engine_streamlit_reports` | Query 中间报告 |

数据库服务挂载：

| 宿主机 | 容器 | 用途 |
|---|---|---|
| `./db_data` | `/var/lib/postgresql/data` | PostgreSQL 数据 |

### 5.2 本地 compose 数据卷

`docker-compose.local.yml` 会额外挂载整个源码：

```yaml
- ./:/app
```

这适合开发调试，但也意味着：

- 容器内 `/app` 会被本地源码覆盖。
- 改代码后可以 `restart` 容器生效。
- 改依赖后必须重新 build。

## 6. 启动方式

### 6.1 方式 A：使用远程镜像

适合：快速部署、服务器试跑、不需要本地改源码。

```bash
docker compose up -d
```

查看日志：

```bash
docker compose logs -f veyrafish
docker compose logs -f db
```

停止：

```bash
docker compose down
```

停止并删除数据库数据卷目录要非常谨慎。当前数据库挂载到 `./db_data`，删除该目录会清空数据库。

### 6.2 方式 B：本地源码构建

适合：本地开发、修改代码后在容器中验证。

```bash
docker compose -f docker-compose.local.yml up --build
```

后台启动：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

改源码后重启应用容器：

```bash
docker compose -f docker-compose.local.yml restart veyrafish
```

改依赖后重新构建：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

停止：

```bash
docker compose -f docker-compose.local.yml down
```

### 6.3 方式 C：手动 build 镜像

```bash
docker build -t veyrafish:local .
```

如需 Playwright Chromium：

```bash
docker build --build-arg INSTALL_PLAYWRIGHT_BROWSERS=1 -t veyrafish:local .
```

## 7. 启动后验证

### 7.1 容器状态

```bash
docker compose ps
```

期望：

- `veyrafish` running
- `veyrafish-db` running

### 7.2 访问页面

浏览器打开：

```text
http://localhost:5000
```

如果部署在服务器：

```text
http://<server-ip>:5000
```

检查页面：

- `/`
- `/insight`
- `/media`
- `/query`
- `/forum`
- `/report`

### 7.3 检查 API

```bash
curl http://localhost:5000/api/status
curl http://localhost:5000/api/system/status
curl http://localhost:5000/api/forum/log
curl http://localhost:5000/api/report/status
```

### 7.4 检查系统启动任务

前端点击“启动系统”，或调用：

```bash
curl -X POST http://localhost:5000/api/system/start
```

返回中应包含：

```json
{
  "success": true,
  "task_id": "...",
  "status": "starting"
}
```

查询：

```bash
curl http://localhost:5000/api/system/task/<task_id>
```

### 7.5 检查端口

系统启动后，浏览器或 curl 检查：

```text
http://localhost:8501
http://localhost:8502
http://localhost:8503
```

如果这些端口不可访问，先看 `docker compose logs -f veyrafish`。

## 8. 数据库初始化与检查

### 8.1 PostgreSQL 容器

进入数据库容器：

```bash
docker exec -it veyrafish-db psql -U veyrafish -d veyrafish
```

列出表：

```sql
\dt
```

### 8.2 应用容器访问数据库

进入应用容器：

```bash
docker exec -it veyrafish bash
```

检查环境变量：

```bash
python - <<'PY'
from config import settings
print(settings.DB_DIALECT, settings.DB_HOST, settings.DB_PORT, settings.DB_NAME)
PY
```

期望：

```text
postgresql db 5432 veyrafish
```

### 8.3 MindSpider 建表

如需初始化爬虫业务表：

```bash
docker exec -it veyrafish bash
cd /app/MindSpider
python main.py --setup
```

注意：

- `mindspider_tables.sql` 包含 MySQL 风格 DDL；PostgreSQL 环境建议使用 Python 初始化脚本路径。
- 初始化前确认 `.env` 中数据库配置正确。

## 9. 日志和产物

### 9.1 容器日志

```bash
docker compose logs -f veyrafish
docker compose logs -f db
```

### 9.2 应用日志目录

宿主机：

```text
./logs/
```

常见文件：

| 文件 | 说明 |
|---|---|
| `logs/insight.log` | InsightEngine |
| `logs/media.log` | MediaEngine |
| `logs/query.log` | QueryEngine |
| `logs/forum.log` | ForumEngine |
| `logs/report.log` | ReportEngine |
| `logs/tasks.db` | 任务、事件、证据 |

### 9.3 报告产物

宿主机：

```text
./final_reports/
```

中间报告：

```text
./insight_engine_streamlit_reports/
./media_engine_streamlit_reports/
./query_engine_streamlit_reports/
```

这些目录已在 compose 中挂载，容器重启后仍保留。

## 10. PDF 与 Playwright

### 10.1 WeasyPrint

Dockerfile 已安装常见 PDF 所需系统库：

- `libpango`
- `libpangocairo`
- `libgdk-pixbuf`
- `libffi`
- `libcairo2`
- GTK 相关库

PDF 导出失败时排查：

```bash
docker exec -it veyrafish bash
python - <<'PY'
import weasyprint
print("weasyprint ok", weasyprint.__version__)
PY
```

### 10.2 Playwright

Dockerfile 默认跳过浏览器下载：

```text
INSTALL_PLAYWRIGHT_BROWSERS=0
```

如果 MindSpider 或相关爬虫需要浏览器能力，有两种方式：

构建时下载：

```bash
docker build --build-arg INSTALL_PLAYWRIGHT_BROWSERS=1 -t veyrafish:local .
```

容器内手动下载：

```bash
docker exec -it veyrafish bash
python -m playwright install chromium
```

如果下载失败，多半是网络问题，需要配置代理或镜像策略。

## 11. 常见问题

### 11.1 应用容器无法连接数据库

症状：

- 日志提示数据库连接失败。
- Insight 查询失败。

检查：

```env
DB_HOST=db
DB_PORT=5432
DB_DIALECT=postgresql
```

不要在容器内使用：

```env
DB_HOST=localhost
```

除非数据库也在同一个应用容器内，这不是当前 compose 设计。

### 11.2 5000 页面打不开

检查：

```bash
docker compose ps
docker compose logs -f veyrafish
```

可能原因：

- 容器启动失败。
- 5000 被占用。
- `.env` 挂载不存在或格式错误。
- `app.py` import 阶段异常。

### 11.3 8501/8502/8503 打不开

说明：

- Flask 容器启动不等于三个 Streamlit 子应用已经启动。
- 当前设计是由 `app.py` 在系统启动流程中拉起 Streamlit 子进程。

处理：

- 先访问 `/`。
- 点击启动系统。
- 查 `/api/status`。
- 看 `logs/insight.log`、`logs/media.log`、`logs/query.log`。

### 11.4 远程镜像拉取慢

`docker-compose.yml` 中已有备用镜像注释：

```yaml
# image: ghcr.nju.edu.cn/elixk/veyrafish:latest
```

可按网络环境替换。

### 11.5 本地 compose 改代码不生效

`docker-compose.local.yml` 挂载源码，通常重启即可：

```bash
docker compose -f docker-compose.local.yml restart veyrafish
```

如果改了依赖或 Dockerfile：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

### 11.6 `.env` 修改后不生效

处理：

```bash
docker compose restart veyrafish
```

如果是前端配置弹窗写入的 `.env`，也建议重启容器确认所有子进程重新读取配置。

### 11.7 PostgreSQL 端口混淆

生产 compose：

```yaml
"${POSTGRES_PORT:-5444}:5432"
```

local compose：

```yaml
"${POSTGRES_PORT:-5544}:5432"
```

解释：

- 宿主机连接 PostgreSQL 用 `localhost:5444` 或 `localhost:5544`。
- 应用容器连接 PostgreSQL 用 `db:5432`。

## 12. 更新和回滚

### 12.1 更新远程镜像

```bash
docker compose pull
docker compose up -d
```

### 12.2 更新本地构建

```bash
docker compose -f docker-compose.local.yml up -d --build
```

### 12.3 回滚

远程镜像方式建议固定镜像 tag，而不是长期使用 `latest`。

例如：

```yaml
image: ghcr.io/elixk/veyrafish:<version>
```

当前 compose 使用 `latest`，适合快速试跑，不适合严格生产回滚。

### 12.4 数据备份

备份目录：

```text
./db_data
./logs
./final_reports
./*_engine_streamlit_reports
.env
```

最关键：

- `db_data` 保存 PostgreSQL 数据。
- `logs/tasks.db` 保存任务、事件、证据。
- `final_reports` 保存最终报告。

## 13. 正式验收清单

Docker 正式验收至少要完成以下项目：

### 13.1 基础验收

- [ ] `docker compose up -d` 或 local compose 启动成功。
- [ ] `docker compose ps` 两个服务均 running。
- [ ] `http://localhost:5000` 可访问。
- [ ] `/api/status` 返回 JSON。
- [ ] `/api/system/status` 返回 JSON。

### 13.2 配置验收

- [ ] `.env` 已挂载到 `/app/.env`。
- [ ] 容器内 `config.settings` 读取到正确 DB 和 API 配置。
- [ ] `DB_HOST=db`。
- [ ] `DB_PORT=5432`。
- [ ] LLM 和搜索 API Key 配置完整。

### 13.3 数据库验收

- [ ] PostgreSQL 容器可进入。
- [ ] 应用容器可连接 `db:5432`。
- [ ] MindSpider schema 初始化成功。
- [ ] InsightEngine 查询不会因缺表直接失败。

### 13.4 应用验收

- [ ] 前端点击启动系统后返回 task_id。
- [ ] `/api/system/task/<task_id>` 可查询。
- [ ] 8501/8502/8503 子应用启动成功。
- [ ] `/forum` 可读取 Forum 日志。
- [ ] `/report` 可创建报告任务。

### 13.5 端到端验收

- [ ] 使用一个固定议题触发三引擎分析。
- [ ] 生成三份中间 Markdown 报告。
- [ ] Forum 有 Agent 或 HOST 消息。
- [ ] ReportEngine 生成 HTML 报告。
- [ ] 可导出 Markdown。
- [ ] 可导出 PDF，或明确记录 PDF 依赖问题。
- [ ] `final_reports/` 中产物落盘。
- [ ] 容器重启后日志和报告仍在宿主机目录。

### 13.6 失败记录

如果任一项失败，必须记录：

- 失败命令。
- 容器日志片段。
- `.env` 相关配置是否正确。
- 是否是网络、API Key、依赖、端口或代码问题。
- 是否阻塞比赛演示。

## 14. 生产部署建议

当前 compose 适合演示和单机部署。若要生产化，建议后续补：

- 固定镜像版本 tag。
- 使用反向代理和 HTTPS。
- 限制 8501/8502/8503 是否对外暴露。
- `.env` 使用安全密钥管理。
- 数据库定期备份。
- 日志轮转。
- 报告目录权限控制。
- 健康检查。
- 资源限制。
- 将长任务迁移到 Worker/队列。

## 15. 当前限制

当前 Docker 配置存在但还未完成正式验收。已知限制：

- Playwright 浏览器默认不下载。
- Docker 环境下真实 LLM、浏览器前端、三引擎完整分析仍需实测。
- 文件总线仍是兼容主路径，需确保挂载目录可写。
- `latest` 镜像不利于严格回滚。
- 生产化安全、HTTPS、鉴权、日志轮转尚未完成。

## 16. 推荐部署路径

如果目标是比赛演示，推荐顺序：

1. 先用 `docker-compose.local.yml` 本地构建跑通。
2. 修正 `.env`，确保 `DB_HOST=db`。
3. 访问首页并启动系统。
4. 验证三引擎端口。
5. 用固定议题跑一次最小链路。
6. 验证报告 HTML 生成。
7. 再尝试 PDF。
8. 将成功命令和失败点写入部署日志。

如果目标是服务器展示：

1. 先在本机完成 local compose 验收。
2. 服务器使用 `docker-compose.yml` 拉镜像或构建镜像。
3. 复制 `.env`。
4. 挂载持久化目录。
5. 配置防火墙只开放必要端口。
6. 通过公网地址访问 5000。

