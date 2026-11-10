# 浏览器与登录

[English](BROWSER.md) · [安装说明](INSTALL.zh-CN.md) · [项目首页](../README.zh-CN.md)

技能自带 Playwright 浏览器通道，优先使用电脑已安装的 Google Chrome 程序，没有 Chrome 时再下载 Chromium。两种方式都使用独立、持久化的监控配置目录。一次登录后，后续扫描可以继续使用该监控环境的登录态，无需读取个人日常浏览器的资料。

## 第一次使用会发生什么

1. **准备浏览器。** 默认安装器会配置 Playwright，并选择 Chrome 或 Chromium 建立监控专用环境；通过其他工具只复制了技能时，助手会在首次使用时运行技能内的配置脚本。
2. **选择来源。** 告诉助手品牌和希望检查的平台。只研究公开网页时，可以不登录平台账号。
3. **按需登录。** 助手为 X 或 Reddit 打开可见的监控浏览器窗口。你在其中填写账号密码、完成平台验证，结束后关闭窗口。
4. **核验访问。** 助手重新使用同一配置目录打开页面，检查页面上可见的已登录账号控件。无法确认时会说明状态，不以“已经存了 Cookie”代替登录核验。
5. **开始研究。** 搜索和页面阅读复用该监控环境。每次命令完成后退出浏览器进程，配置与登录资料保留供下一次使用。

登录窗口有等待时限。如果没有来得及完成，可以关闭窗口，再让助手重新打开登录。登录过期或平台要求额外验证时，也可能需要你再次手动操作。

## 常用命令

以下命令在**安装后的技能目录**中运行。Windows 可将 `python3` 换成 `py -3`；`browser.py` 会自动进入技能自己的运行环境。

```sh
python3 scripts/browser.py doctor
python3 scripts/browser.py status
```

`doctor` 检查运行环境，不打开浏览器；`status` 显示本地配置和已记录的检查。需要核验当前账号访问状态时，运行 `verify`。

### 浏览器选择

`doctor` 会显示选中的浏览器通道。配置脚本保存浏览器通道、监控数据目录和配置名称，日常命令沿用它们，无需每次重复参数。需要长期更换时，运行 `python3 scripts/setup.py --browser-channel auto`，也可将 `auto` 换成 `chrome` 或 `chromium`。

只针对当前命令时，可以使用全局参数 `--browser-channel chrome|chromium`，不会改变已保存的选择：

```sh
python3 scripts/browser.py --browser-channel chrome doctor
```

此参数不会安装缺失的浏览器。Chrome 和 Chromium 使用监控配置中的不同子目录，切换程序后需要在新选择的程序中登录，不会互相复制登录态。选择 Chrome 不会接入你已经打开的个人 Chrome 窗口。

### 连接 X 或 Reddit

```sh
python3 scripts/browser.py login --platform x
python3 scripts/browser.py verify --platform x
python3 scripts/browser.py login --platform reddit
python3 scripts/browser.py verify --platform reddit
```

在可见窗口里直接登录平台，完成后关闭窗口。助手应等登录命令结束后，再执行 `verify`。密码和验证码都不需要填进命令或聊天。

`verify` 根据当时页面返回结果：页面可能显示已登录、要求登录、无法访问，或没有足够信息确认登录。登录成功也不代表每个搜索结果和讨论页面都能访问。

### 搜索与阅读

```sh
python3 scripts/browser.py search --platform web --query 'Fable Labs reviews'
python3 scripts/browser.py search --platform x --query '"Fable Labs"'
python3 scripts/browser.py search --platform reddit --query 'Fable Labs'
python3 scripts/browser.py read https://example.com/
```

返回的 JSON 包含来源 URL、观察时间、页面渲染后的正文、链接和可取得的页面时间元素。助手从搜索结果中选择原始页面进一步阅读，再进行分析。上述品牌和网址只是示例占位。

长页面的 `read` 和 `search` 可通过 `--scrolls` 取得有限次数的滚动样本，读取随滚动加载的内容；这不等于展开所有回复或取得整段讨论的完整归档。

需要看到阅读窗口时，将全局参数放在子命令前：

```sh
python3 scripts/browser.py --headed read https://example.com/
```

需要分别使用不同账号或环境时，可以选择独立的配置名称，并在登录、核验和采集中始终使用该名称：

```sh
python3 scripts/browser.py --profile research-team login --platform x
python3 scripts/browser.py --profile research-team verify --platform x
```

同一个配置目录一次只运行一条浏览器命令。完成或关闭登录窗口后，再使用它开始扫描。

## 数据存放位置

| 数据 | 默认位置 |
| --- | --- |
| Python 运行环境 | `<安装后的技能目录>/.runtime/venv/` |
| 选择 Chromium 时下载的浏览器文件 | `<安装后的技能目录>/.runtime/browsers/` |
| macOS 监控数据 | `~/Library/Application Support/brand-reputation-monitor/` |
| Windows 监控数据 | `%LOCALAPPDATA%/brand-reputation-monitor/` |
| Linux 监控数据 | `${XDG_STATE_HOME:-~/.local/state}/brand-reputation-monitor/` |
| 默认配置数据 | 监控数据目录下的 `profiles/default/` |
| 浏览器用户资料 | 按所选通道存入 `profiles/default/chrome/` 或 `profiles/default/chromium/` |

可通过全局参数 `--state-dir` 指定其他监控数据目录。配置文件包含账号登录态，应保持私有。替换技能不会删除这个独立目录；技能不会导入个人浏览器资料，也不会把 Cookie 导出到报告中。

## 遇到无法访问的来源

专用浏览器提供独立的登录环境，平台自身的访问限制仍然适用。网站可能要求人工验证、限制自动访问，或调整页面结构。助手会记录受到影响的来源，并继续处理可取得的材料。

此通道用于搜索与阅读，不提供发帖、回复或消息发送命令。
