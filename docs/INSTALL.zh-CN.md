# 开始使用

[English](INSTALL.md) · [项目首页](../README.zh-CN.md) · [浏览器与登录](BROWSER.zh-CN.md)

## 准备条件

- Python 3.10 或更新版本，并支持创建虚拟环境。
- 能够加载 Skill、执行本地命令的 AI 助手。
- 安装 Playwright 所需的网络连接；找不到 Google Chrome 或明确选择 Chromium 时，还需要下载浏览器。
- 需要登录平台时，能够打开可见浏览器窗口的桌面环境。

分析使用当前助手的模型，无需为本项目另外注册模型账号或填写 API Key。

## 安装完整技能

下载仓库 ZIP，或克隆仓库后运行：

```sh
git clone https://github.com/miyahluvgames-source/brand-reputation-monitor-skill.git
cd brand-reputation-monitor-skill
python3 scripts/install_skill.py
```

Windows 的安装命令为：

```powershell
py -3 scripts/install_skill.py
```

默认目标是 `$CODEX_HOME/skills/brand-reputation-monitor`；未设置 `CODEX_HOME` 时，使用用户目录下的 `.codex/skills/brand-reputation-monitor`。

安装器会复制技能、创建专用 Python 虚拟环境并安装 Playwright。默认优先使用已经安装的 Google Chrome 程序，为其建立独立的监控配置；没有 Chrome 时，将 Chromium 下载到技能的运行目录。随后检查选定的浏览器能否启动。配置成功后，浏览器通道即可使用；平台账号登录由助手在下一步引导你完成。

也可以指定新的安装位置：

```sh
python3 scripts/install_skill.py --dest /path/to/skills/brand-reputation-monitor
```

目标目录必须尚不存在，安装器不会覆盖已有技能及自定义内容。

## 选择浏览器程序

新安装默认使用 `auto`：

| 选项 | 行为 |
| --- | --- |
| `--browser-channel auto` | 在标准安装位置找到 Google Chrome 时使用它，否则下载 Chromium |
| `--browser-channel chrome` | 使用已安装的 Google Chrome，找不到时报告错误 |
| `--browser-channel chromium` | 下载并使用技能自己的 Chromium |

例如，`python3 scripts/install_skill.py --browser-channel chrome` 会使用已有 Chrome 程序，同时建立独立的监控配置，不会接管日常 Chrome 的账号或标签页。

浏览器通道、监控数据目录和配置名称会保存下来，后续配置与浏览器命令沿用它们。需要更换时，在安装后的技能目录运行 `python3 scripts/setup.py --browser-channel chromium`。Chrome 和 Chromium 的登录资料分别保存，切换后需要在新选中的程序中登录。已经找到 Chrome 但启动失败时，配置会报告具体问题，不会静默切换浏览器。

## 开始第一次监测

新开一个助手对话，让宿主发现已安装的技能，然后输入：

```text
使用 $brand-reputation-monitor，关注 Fable Labs 最近 72 小时
在网页、X 和 Reddit 上的反馈。先帮我连接需要的来源，
然后整理一份包含原始链接和后续建议的报告。
```

助手会检查浏览器运行环境。如果所选来源需要账号，它会打开监控专用窗口，说明当前需要登录的平台，并等待你操作。你在平台页面完成登录后关闭窗口，助手再用保存下来的监控配置目录核验访问状态，继续采集。

密码、验证码和二步验证均在浏览器的平台页面里填写，不需要发给助手。暂时不想登录时，可以先要求只检查公开网页。[浏览器与登录](BROWSER.zh-CN.md)包含具体命令和登录态行为。

## 通过其他工具安装 Skill

也可以通过宿主的技能管理器安装完整 `skill/` 文件夹，或手动复制到其技能目录。请保留 `SKILL.md` 旁边的 `scripts/`、`references/` 和 `agents/`；安装后的浏览器通道不依赖原仓库仍留在下载位置。

首次使用时，如果缺少浏览器环境，助手会按技能说明运行自带的配置脚本。你也可以在安装后的技能目录执行：

```sh
python3 scripts/setup.py
```

仅审阅已有资料，或宿主已经提供适用的浏览器集成时，可以只复制技能，暂不配置它的浏览器运行环境：

```sh
python3 scripts/install_skill.py --skill-only
```

以后需要内置浏览器时，再运行 `scripts/setup.py`。助手会分别检查技能文件和浏览器是否已准备好。

## 安装中断后继续

进入安装后的技能目录，再运行 `python3 scripts/setup.py`。配置脚本复用自身运行目录，报告仍未完成的步骤，保留监控配置与登录资料。配置成功后，可检查：

```sh
python3 scripts/browser.py doctor
```

精简 Linux 系统可能缺少 Chromium 所需的共享库。配置脚本会报告具体依赖问题，不会自动执行需要管理员权限的系统安装。按提示补充系统依赖后，再运行配置脚本即可。

## 更新与卸载

更新前，保存自定义技能内容，将旧技能文件夹移到宿主技能目录以外，再运行安装器；最后合入仍需保留的自定义内容。监控资料存放在操作系统的应用数据目录中，替换技能不会清除其登录态。

卸载时，先关闭监控浏览器，再移除已安装的技能文件夹。只有同时希望清除监控账号登录资料时，才删除独立的监控数据目录。具体位置见[浏览器与登录](BROWSER.zh-CN.md)。

## 可选的记录工具

仓库还提供 JSON 覆盖记录校验和 Markdown 报告工具，可直接在仓库目录体验：

```sh
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

如需固定命令行入口，可在虚拟环境中运行 `python3 -m pip install .`，然后使用 `reputation-monitor`。这些工具负责记录格式与报告整理，语义分析由 Skill 和助手完成。[查看记录格式 →](SCHEMA.md)
