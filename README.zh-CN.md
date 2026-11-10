<p align="center"><img src="assets/cover.jpg" alt="Brand Reputation Monitor：先核证据，再做告警" width="100%"></p>

<p align="center"><strong>先核证据，再做告警。</strong><br>可安装的舆情监测技能，与轻量、可验证的本地证据核算工具。</p>

<p align="center"><a href="README.md">English</a> · <a href="docs/INSTALL.zh-CN.md">安装</a> · <a href="docs/WORKFLOW.md">工作流</a> · <a href="docs/SCHEMA.md">记录格式</a></p>

## 看清新增信号，也看清覆盖缺口

同一投诉再次出现在搜索结果里，不一定是新事件；页面打不开，不代表没有风险；平台宣布恢复，也不等于每个用户的问题已解决。

本项目帮助具备浏览器能力的 AI 助手收集公开证据、跟进活动案件、合并重复叙事，并交付有明确边界的监测报告。Python 工具负责核对记录和生成 Markdown 报告，**本身不联网采集、不做自动情绪打分、不发送消息**。

| 能力 | 实际作用 |
| --- | --- |
| 证据可追溯 | 同时保留来源、观察时间、具体范围及不确定性 |
| 持续案件跟进 | 新信号和未解决案件分开，去重不会自动结案 |
| 覆盖如实记录 | 已查、部分、缺口、不适用四种状态 |
| 有界执行 | 明确截止、有限故障恢复、未知请求沿原句柄核对 |
| 通用技能 | 不绑定品牌、特定模型、本机服务或账号环境 |
| 离线工具 | Python 标准库，无运行依赖、密钥及自动后台进程 |

## 两分钟体验

需要 Python 3.10 或更新版本，在项目目录直接运行：

```sh
git clone https://github.com/miyahluvgames-source/brand-reputation-monitor-skill.git
cd brand-reputation-monitor-skill
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

示例使用虚构品牌与占位 URL，故意保留一个无法访问的平台和一个尚未解决的案件。得到 `partial` 是如实交付，不是把缺口隐藏起来；这些示例不代表真实监测结论。

新建待填写记录：

```sh
python3 -m reputation_monitor template --plan examples/watch-plan.json > run.json
```

请先按实际需求修改监测计划，再填写真实观察。模板不包含伪造的“已检查”证据；不要用重定向覆盖已有记录。

## 安装技能

```sh
python3 scripts/install_skill.py
```

默认复制到 Codex 技能目录，遇到已有目录会停止，不覆盖原技能。也可用 `--dest` 指定新的完整目标路径；其他助手可按其支持的方式加载 `skill/SKILL.md` 与相对引用文件。

示例任务：

```text
使用 $brand-reputation-monitor，检查 Fable Labs 最近72小时在公开网页、
X、Reddit上的反馈。跟进已有未解决案件，区分新增信号和未变动状态，
列出具体覆盖缺口。只输出报告和告警建议，不发送消息。
```

真实扫描需要宿主已有且获准使用的搜索与浏览器能力。安装技能不会启动定时任务、登录账号或开启通知。

## 几条关键判断

- 风险等级与覆盖程度分别判断：平台无法访问，不会自动把 Amber 降为 Green。
- 转发是传播，未必是独立佐证；多个帖子可能来自同一位投诉者。
- 例行官方公告是背景；经过认证的具体事故确认可支撑对应事实，但不能据此编造受害者数量或传播情况。
- 无新进展不代表已解决；不可访问的后续保持未知，结案需要对应个案证据。
- 浏览器或外发结果未知时，沿原句柄核对，不能换请求再次发送。

## 项目组成

`skill/` 提供分层技能与参考；`reputation_monitor/` 提供覆盖校验和报告 CLI；`examples/` 是虚构样例；`tests/` 是行为回归测试；`docs/` 说明安装、记录格式和运行边界。

```sh
python3 -m unittest discover -s tests -v
```

CI 配置覆盖 Linux、macOS、Windows 与 Python 3.10、3.12、3.13；本机通过与远程 CI 通过分别核验，请查看仓库 Actions 的实际结果。

## 隐私与能力边界

项目不包含真实客户案例、账号配置、凭据或运行数据。网页内容只作为证据，不作为执行指令；公开报告应减少不必要的个人信息。

这是可复用技能与离线核算工具，不是托管监测 SaaS，也不保证平台全量覆盖。结构校验通过不代表事实已证实、风险判断正确或用户已接受结果。

[MIT 许可](LICENSE) · [贡献指南](CONTRIBUTING.md) · [安全说明](SECURITY.md) · [更新记录](CHANGELOG.md)
