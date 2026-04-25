# Veyrafish Docker 部署文档需求冻结

**状态**：已冻结  
**日期**：2026-04-24  
**运行模式**：`$vibe` interactive_governed  
**主题**：编写 Docker 部署与调试文档。

## 1. Goal

基于当前项目真实 Docker 配置，编写一份 Docker 部署文档，覆盖镜像方式、本地构建方式、环境变量、端口、数据卷、启动、验证、日志、常见问题和正式验收清单。

## 2. Deliverable

- `docs/deployment/2026-04-24-veyrafish-docker-deployment-guide.md`

## 3. Constraints

- 当前 Docker 正式验收尚未完成，文档必须明确这是部署/调试指南，不声明“已验收通过”。
- 不修改 Dockerfile、compose 或业务代码。
- 必须基于当前 `Dockerfile`、`docker-compose.yml`、`docker-compose.local.yml`、`.env.example`。
- 必须说明生产镜像方式和本地源码构建方式的区别。

## 4. Acceptance Criteria

- 包含部署前置条件。
- 包含 `.env` 配置建议，特别是 Docker 下 `DB_HOST=db`、`DB_PORT=5432`。
- 包含端口、数据卷、服务拓扑。
- 包含两种启动方式：远程镜像 compose、本地构建 compose。
- 包含 Playwright、WeasyPrint、PostgreSQL、日志和报告目录说明。
- 包含启动后验证命令和浏览器检查项。
- 包含常见故障排查。
- 包含正式验收清单。

## 5. Non-goals

- 不执行 Docker 构建或启动。
- 不修复 Docker 环境问题。
- 不写云厂商生产运维手册。
- 不写 Kubernetes 部署文档。

## 6. Delivery Truth Contract

事实来源：

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.local.yml`
- `.env.example`
- `.dockerignore`
- `README.md`
- `DEVELOPMENT.md`
- `docs/design/2026-04-24-veyrafish-overall-project-design.md`
- `docs/development/2026-04-24-veyrafish-overall-development-guide.md`

