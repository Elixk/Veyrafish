# VibeSkills 安装到 Cursor 的完整指南

## 一、项目简介

VibeSkills 是一个 **个人 AI 操作系统**，包含 340+ 技能（Skills），覆盖编程、科研、数据分析、创作等领域。它通过 VCO（Vibe Code Orchestrator）运行时引擎统一管理和智能路由这些技能。

Cursor 在当前版本中处于 **preview-guidance（预览引导）** 支持状态。

---

## 二、安装方式（二选一）

### 方式 A：脚本安装（推荐）

在 **仓库根目录** 下用 PowerShell 执行：

**第 1 步：设置环境变量并安装**

```powershell
$env:CURSOR_HOME = "$env:USERPROFILE\.cursor"
pwsh -NoProfile -File .\install.ps1 -HostId cursor -Profile full
```

**第 2 步：运行健康检查**

```powershell
pwsh -NoProfile -File .\check.ps1 -HostId cursor -Profile full
```

安装结果会写入 `~/.cursor` 目录，包括：

- `~/.cursor/skills/vibe/` — 核心运行时入口及全部 bundled 技能
- `~/.cursor/commands/` — 命令文件
- `~/.cursor/.vibeskills/` — 安装状态 sidecar（host-settings、host-closure、install-ledger）

### 方式 B：手动复制安装（离线 / 无需脚本）

如果你不想跑脚本，可以手动将以下目录从仓库复制到 `%USERPROFILE%\.cursor\`：

1. 复制 `skills/` 目录 → `~/.cursor/skills/`
2. 复制 `commands/` 目录 → `~/.cursor/commands/`
3. 复制 `config/upstream-lock.json` → `~/.cursor/config/upstream-lock.json`

确保 `~/.cursor/skills/vibe/` 存在即可。

---

## 三、安装后仍需手动完成的部分

由于 Cursor 是 preview-guidance 路径，以下内容 **不会** 被自动接管：

1. **`~/.cursor/settings.json`** — 仍由你自己维护，安装脚本不会覆盖你的真实 Cursor 设置
2. **Provider 凭据** — 如 API Key 等需要在 Cursor 本地配置
3. **MCP 注册** — 需要在 Cursor 的 MCP 设置面中手动配置
4. **插件启用** — 需要在 Cursor 内手动操作

---

## 四、安装结果分析

### 正常通过项（46 项）

核心运行时和所有关键组件安装成功：

- 核心 skill（`vibe`、`tdd-guide`、`think-harder` 等）
- 路由脚本、治理配置、记忆治理、质量策略等全部就位
- 工作流 skill（`brainstorming`、`writing-plans`、`systematic-debugging` 等）
- host sidecar 状态（host-settings、host-closure）

### 可忽略的失败与警告

- **`[FAIL] vibe runtime freshness receipt`** — 因为仓库目录没有 `.git`（不是 git clone），freshness 校验无法执行，**不影响正常使用**。
- **3 个 `[WARN]`**（freshness gate / frontmatter gate / coherence gate）— 同样因为不在 git 仓库上下文中被跳过，属于正常情况。

### MCP 需要手动配置

| MCP | 状态 | 说明 |
|:---|:---|:---|
| `github` | host_native_unavailable | 需要在 Cursor MCP 设置中手动注册 |
| `context7` | host_native_unavailable | 需要在 Cursor MCP 设置中手动注册 |
| `serena` | host_native_unavailable | 需要在 Cursor MCP 设置中手动注册 |
| `scrapling` | not_attempted | 需要先启用 scripted install 支持 |
| `claude-flow` | not_attempted | 需要先启用 scripted install 支持 |

这些是 **增强功能**，不配置也不影响核心 `/vibe` 工作流的使用。

---

## 五、安装后如何使用

在 Cursor 的对话中通过 **Skills 入口** 调用，在消息末尾附上 `/vibe`：

```text
帮我重构这个模块的代码 /vibe
```

```text
帮我分析这个项目的架构 /vibe
```

系统会自动走 **澄清 → 规划 → 执行 → 验证** 的受管工作流。不加 `/vibe` 则按普通对话处理。

---

## 六、可选：补充 AI 治理在线配置

基础安装完成后即可使用。如果你还想启用 AI 治理 advice 能力，需要在本地环境变量中配置：

- **主路径（必需）**：`VCO_INTENT_ADVICE_API_KEY` + 可选 `VCO_INTENT_ADVICE_BASE_URL` + `VCO_INTENT_ADVICE_MODEL`
- **向量 diff（可选）**：`VCO_VECTOR_DIFF_API_KEY` + 可选 `VCO_VECTOR_DIFF_BASE_URL` + `VCO_VECTOR_DIFF_MODEL`

配置完成后，在仓库根目录运行以下命令验证：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify\vibe-router-ai-connectivity-gate.ps1 -TargetRoot "$env:USERPROFILE\.cursor" -WriteArtifacts
```

- 返回 `ok` 表示 AI 治理已连通
- 返回 `missing_credentials` / `missing_model` 表示配置未完成

---

## 七、版本选择

| 版本 | Profile 参数 | 说明 |
|:---|:---|:---|
| 全量版本 | `-Profile full` | 包含全部 340+ 技能，推荐大多数用户 |
| 仅核心框架 | `-Profile minimal` | 只包含核心运行时框架，精简安装 |

---

## 八、卸载

在仓库根目录运行：

```powershell
pwsh -NoProfile -File .\uninstall.ps1 -HostId cursor
```

只会清理 VibeSkills 自己安装的内容，不会影响你的 Cursor 原有配置。
