# Brand Reputation Monitor Skill

[English README](README.md) · [安装说明](docs/INSTALL.zh-CN.md) · [Install Guide](docs/INSTALL.md)

![流程概览](assets/workflow-overview.svg)

把一个具备浏览器能力的 agent 变成跨平台的品牌舆论、PR 风险与危机信号监测工具。

这个项目打包了一套可复用、宿主无关的监测 skill，可用于 Codex、Claude 或其他具备浏览器控制能力的 agent 宿主。它适合做单轮巡检，也适合做定时监测。设计目标是让 agent 能够：

- 自动判断品牌所属行业与高风险投诉类型
- 默认先覆盖公开网络信息 / 搜索结果
- 扫描 X、Reddit、Facebook、LinkedIn、Instagram、小红书等指定社媒
- 优先识别安全、资金、诈骗、钓鱼、宕机、合规与信任风险
- 先检查浏览器自动化环境，再创建或复用专门的 managed browser
- 主动提醒用户在这个 managed browser 中完成目标社媒登录，再把对应平台结果视为可信覆盖

## 为什么要做这个项目

很多品牌监测 prompt 在真实环境里会失败，通常是因为：

1. 它们把社媒监测当成情绪收集，而不是风险识别。
2. 它们忽略浏览器自动化环境和登录态，却默认平台覆盖完整。
3. 它们绑定在某一个宿主或某一个项目里，无法跨 agent 复用。

这个项目就是为了解决这些问题。它提供的是一套：

- 风险优先
- 浏览器环境优先
- 登录态优先
- 宿主无关
- 适合自动化调度

的监测工作流。

## 这个 Skill 会做什么

它会响应类似下面的自然语言请求：

- 监测这个品牌的舆情
- 看看最近有没有 PR 风险
- 扫一下 X 和 Reddit 上有没有危机信号
- 看看这个公司有没有安全投诉
- 过去 72 小时跑一轮品牌舆情监测

在每一轮运行中，预期执行顺序是：

1. 先检查浏览器环境是否可用。
2. 如果宿主允许本地安装和配置，则自动补齐浏览器能力。
3. 创建或复用一个专门的 managed browser profile。
4. 提醒用户在该浏览器里登录目标平台。
5. 永远先扫描公开网络信息。
6. 再扫描指定社媒平台。
7. 合并跨平台重复叙事。
8. 输出一份精炼、可决策的风险报告。

## 默认监测逻辑

- 默认时效范围：最近 72 小时
- 默认必须覆盖：公开网络 / 搜索结果
- 默认高优先级主题：
  - 安全事件
  - 资产损失或提现失败
  - 诈骗、钓鱼、假冒
  - 隐私泄露或数据泄露
  - 影响信任的宕机事件
  - 重复出现的用户伤害型投诉
  - 媒体或 KOL 放大传播

## 输出结构

推荐输出结构如下：

1. 监测范围
2. 总体状态：`Green` / `Amber` / `Red`
3. 核心结论
4. 安全 / 信任 / 资金风险
5. 重点叙事或重点帖子
6. 建议动作
7. 覆盖缺口

如果某个平台没有登录或无法完整访问，这套 skill 的设计原则是继续扫描其他来源，并明确把该平台标记为 partial coverage，而不是伪造完整覆盖。

## 项目结构

```text
brand-reputation-monitor-skill/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── assets/
│   └── workflow-overview.svg
├── docs/
│   ├── INSTALL.md
│   └── INSTALL.zh-CN.md
├── scripts/
│   ├── install-codex-skill.ps1
│   └── install-codex-skill.sh
└── skill/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── scripts/
    └── references/
```

## 快速开始

### 在 Codex 中使用

1. 把 `skill/` 目录复制或安装到 Codex 的 skills 目录。
2. 确保宿主具备浏览器自动化和浏览器原生控制能力。
3. 直接发起请求，例如：

```text
Use $brand-reputation-monitor to run one reputation scan for BYDFi across X, Reddit, LinkedIn, and open web within the last 72 hours.
```

### 在 Claude 中使用

如果你的 Claude 宿主支持可复用 skills，就把 `skill/` 目录复制到对应的 skill 目录。

如果不支持，可以直接使用这些 prompt 模板：

- [Claude 极简入口](skill/references/claude-minimal-entry.md)
- [通用单轮 prompt](skill/references/portable-prompt-template.md)
- [自动化 prompt](skill/references/automation-prompt-template.md)

## 安装说明

手动安装和脚本安装都写在这里：

- [安装说明](docs/INSTALL.zh-CN.md)
- [Install Guide](docs/INSTALL.md)

## 可选 Telegram 告警

这套 skill 现在可以在最终风险达到设定阈值时，自动通过 Telegram 向用户发通知。

要开启这个功能，用户必须提供：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

推荐默认策略：

- `Amber` 和 `Red` 发送
- 如果命中高优先级安全 / 资金风险覆盖条件，则立即发送

在 Windows Codex 类宿主上，内置 helper 在这里：

- [send-telegram-alert.py](skill/scripts/send-telegram-alert.py)

## Managed Browser 与登录态要求

这个项目的一个核心前提是：只有当指定的 managed browser 已经具备目标社媒的登录态时，该平台的结果才应被视为可靠覆盖。

例如：

- 如果要监测 X，就应在 managed browser 中登录 X
- 如果要监测 LinkedIn，就应在 managed browser 中登录 LinkedIn
- 如果要监测小红书，就应在 managed browser 中登录小红书

如果没有登录，该 skill 不应该假装“已经完整覆盖该平台”。

## 浏览器工具预期

当宿主允许本地安装与配置时，这个 skill 预期会帮助补齐：

- Playwright 或等价的浏览器自动化能力
- Chrome DevTools MCP 或等价的浏览器原生控制能力
- 一个专门用于监测任务的 managed browser profile

具体包名和安装方式取决于宿主。在 Codex 类环境里，常见等价物是：

- `chrome-devtools-mcp`
- `@playwright/mcp`

## 当前限制

- 这是一个工作流型工具包，不是 SaaS 产品。
- 最终效果取决于宿主是否给浏览器访问、shell 权限和平台可见性。
- 私密内容或高门槛平台内容，即使登录后也可能仍然受限。
- 这套 skill 的目标是风险识别，不是历史数据看板或情绪统计报表。

## License

本仓库使用 [MIT License](LICENSE)。
