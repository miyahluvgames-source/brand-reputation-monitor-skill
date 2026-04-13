# 安装说明

这个仓库刻意保持轻量。核心交付物是可复用的 `skill/` 目录，以及配套的 prompt 模板和安装脚本。

## 基本要求

你只需要具备以下条件：

- 一个能运行浏览器型 agent 的宿主
- 如果希望 skill 自动补装浏览器能力，则宿主最好允许 shell 和配置修改
- 如果希望使用专门的 managed browser，最好安装 Chrome 或 Chromium

## 安装到 Codex

### 方案 1：脚本安装

PowerShell：

```powershell
pwsh ./scripts/install-codex-skill.ps1 -Force
```

Bash：

```bash
bash ./scripts/install-codex-skill.sh
```

默认安装位置：

- Windows：`%USERPROFILE%\.codex\skills\brand-reputation-monitor`
- 类 Unix 系统：`$HOME/.codex/skills/brand-reputation-monitor`

如果设置了 `CODEX_HOME`，脚本会优先使用它。

### 方案 2：手动安装

把下面这个目录：

```text
skill/
```

复制到：

```text
<CODEX_HOME>/skills/brand-reputation-monitor
```

典型默认路径：

- Windows：`C:\Users\<你自己>\.codex\skills\brand-reputation-monitor`
- macOS / Linux：`~/.codex/skills/brand-reputation-monitor`

## 安装到 Claude 或其他宿主

不同宿主没有统一的 skill 安装路径。

可以选择以下方式：

1. 如果宿主支持本地可复用 skill，就把 `skill/` 目录复制进去。
2. 如果宿主不支持本地 skill 目录，就直接使用这些 prompt 模板：
   - `skill/references/claude-minimal-entry.md`
   - `skill/references/portable-prompt-template.md`
   - `skill/references/automation-prompt-template.md`

## 浏览器环境预期

这套 skill 设计上会先检查：

- 浏览器原生控制能力
- 浏览器自动化能力
- 专门的 managed browser profile
- 目标平台的登录态

如果宿主允许本地安装和配置，它会尝试引导或补齐：

- Playwright 或等价浏览器自动化层
- Chrome DevTools MCP 或等价浏览器原生控制层

## 可选 Telegram 告警

如果你希望监测结果在风险超过阈值时自动通知你，需要提供：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

推荐默认阈值：

- `Amber`

内置 helper 路径：

- `skill/scripts/send-telegram-alert.py`

## Managed Browser 建议

如果可以创建专门的 profile，就不要直接使用你日常浏览器的 profile 跑监测自动化。

专门的 managed browser profile 会更稳定，因为它可以：

- 隔离登录态
- 减少无关标签页干扰
- 降低扩展污染
- 让定时监测更容易复现

## 登录态要求

如果你希望平台结果可信，就应当在专门的 managed browser 中提前登录需要覆盖的平台。

例如：

- X
- Reddit
- Facebook
- LinkedIn
- Instagram
- 小红书

如果没有登录，这套 skill 的正确行为应该是继续输出 partial coverage，而不是假装已经完整扫描。

## 推荐的第一次运行方式

可以先用这样一条请求试跑：

```text
Use $brand-reputation-monitor to run one reputation scan for [BRAND] across X, Reddit, LinkedIn, and open web within the last 72 hours.
```

## 故障排查

### Agent 没有浏览器工具

预期行为：

- skill 先识别缺口
- 如果允许安装，就补齐缺失能力
- 如果不允许安装，就明确报告缺失前置条件，并在能跑的范围内继续

### Agent 无法访问某个平台

预期行为：

- 把该平台标记为 partial coverage
- 公开网络信息仍然继续扫描
- 最终报告中明确给出 coverage gaps

### 宿主不允许安装本地包

这时就把本项目当成工作流包和 prompt 包使用。此时 setup 部分是操作清单，不是可执行安装步骤。
