# 安装说明

需要 Python 3.10 或以上版本。在项目根目录运行 `python3 scripts/install_skill.py`，Windows 可使用 `py -3`。默认安装到 `$CODEX_HOME/skills/brand-reputation-monitor`；未设置时使用 `~/.codex/skills/brand-reputation-monitor`。

安装器拒绝覆盖已有目标或符号链接。升级前先核对旧技能、自定义规则和备份，或通过 `--dest` 选择新的完整目标目录。安装不会启动浏览器、配置凭据、登录账号或启用自动化。

手动安装时，将整个 `skill/` 目录复制到宿主支持的技能位置，文件夹命名为 `brand-reputation-monitor`，保留相对目录结构。不支持技能发现的宿主可直接读取 `skill/SKILL.md`；不同宿主的发现方式和工具能力需分别验证。

离线工具可直接在仓库根运行 `python3 -m reputation_monitor --help`。如需命令行入口，在独立虚拟环境中执行 `python3 -m pip install .`，即可使用 `reputation-monitor`；本项目未声明已发布到 PyPI。

旧 shell/PowerShell 安装脚本与直接 Telegram 发送器已退役。未来通知接入由宿主承担，必须保留准确授权、发送意图、原始回执和未知结果核对。通用包中不存业务账号、凭据、真实投诉台账或生产运行记录。
