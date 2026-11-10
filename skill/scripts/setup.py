#!/usr/bin/env python3
"""Prepare this skill's private Python runtime and dedicated monitoring browser."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys


PLAYWRIGHT_VERSION = "1.65.0"
OWNER = "brand-reputation-monitor/runtime-v1"


class SetupError(RuntimeError):
    pass


def python_path(runtime):
    return runtime / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.is_symlink() or path.is_symlink():
        raise SetupError("Refusing a symlink at a setup receipt path")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def owned_runtime(skill):
    runtime = skill / ".runtime"
    if runtime.is_symlink():
        raise SetupError("The skill runtime must not be a symlink")
    runtime.mkdir(mode=0o700, exist_ok=True)
    marker = runtime / "owner.json"
    if marker.is_symlink():
        raise SetupError("Runtime ownership marker must not be a symlink")
    if marker.exists():
        try:
            value = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SetupError("Runtime ownership marker is unreadable") from exc
        if value != {"owner": OWNER}:
            raise SetupError("This runtime directory belongs to another installation")
    elif any(runtime.iterdir()):
        raise SetupError("Existing unmarked runtime is protected; choose a fresh skill destination")
    else:
        write_json(marker, {"owner": OWNER})
    for name in ("venv", "browsers", "setup.lock"):
        if (runtime / name).is_symlink():
            raise SetupError("Refusing a symlink in the private runtime: " + name)
    return runtime


@contextmanager
def setup_lock(runtime):
    """OS lock releases on exit/crash; a stale lock file never implies a live lock."""
    with (runtime / "setup.lock").open("a+b") as handle:
        locked = False
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                if not handle.read(1):
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            yield
        except BlockingIOError as exc:
            raise SetupError("Another setup is active for this skill; wait for that setup to finish") from exc
        finally:
            if locked:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run(args, env, timeout=600):
    """One bounded child, with its output returned only to the setup controller."""
    try:
        return subprocess.run([str(arg) for arg in args], env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise SetupError("Setup step timed out; its original child was stopped and joined") from exc


def require_success(result, stage):
    if result.returncode:
        detail = (result.stderr or result.stdout or "command failed")[-3000:]
        detail = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[redacted]@", detail)
        raise SetupError(stage + ": " + detail.strip())


SMOKE = """from pathlib import Path
from playwright.sync_api import sync_playwright
import json, sys
with sync_playwright() as p:
    channel = sys.argv[1]
    executable = Path(sys.argv[2]) if channel == 'chrome' else Path(p.chromium.executable_path)
    if not executable.is_file():
        raise RuntimeError('Chromium executable is missing')
    options = {'headless': True, 'channel': channel, 'timeout': 30000}
    if channel == 'chrome':
        options['executable_path'] = str(executable)
    browser = p.chromium.launch(**options)
    try:
        page = browser.new_page()
        page.goto('about:blank')
        assert page.url == 'about:blank'
    finally:
        browser.close()
print(json.dumps({'launched': True, 'closed': True}))
"""


def load_config_module(skill):
    path = Path(skill) / "scripts/browser_config.py"
    spec = importlib.util.spec_from_file_location("monitor_browser_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup(skill, state_dir=None, profile=None, browser_channel=None):
    skill = Path(skill).absolute()
    browser_script = skill / "scripts/browser.py"
    if not browser_script.is_file():
        raise SetupError("The installed skill is incomplete: scripts/browser.py is missing")
    runtime = owned_runtime(skill)
    configuration = load_config_module(skill)
    executable = python_path(runtime)
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PIP_TARGET", "PIP_PREFIX", "PIP_USER"):
        env.pop(name, None)
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(runtime / "browsers")
    with setup_lock(runtime):
        stage = "create_runtime"
        selected = configuration.resolve_defaults(skill, state_dir, profile, browser_channel)
        browser_args = [str(executable), str(browser_script), "--state-dir", selected["state_dir"],
                        "--profile", selected["profile"], "--browser-channel", selected["browser_channel"]]
        def progress(value):
            write_json(runtime / "setup.json", {"status": "preparing", "stage": value,
                       "selection": selected, "updated_at": datetime.now(timezone.utc).isoformat()})
        try:
            progress(stage)
            if not executable.is_file():
                print("Preparing an isolated Python environment…", file=sys.stderr)
                require_success(run([sys.executable, "-m", "venv", "--copies", runtime / "venv"], env), stage)
            stage = "install_playwright"
            progress(stage)
            probe = run([executable, "-c", "from importlib.metadata import version; print(version('playwright'))"], env, 30)
            if probe.returncode or probe.stdout.strip() != PLAYWRIGHT_VERSION:
                print("Installing the browser driver in the skill environment…", file=sys.stderr)
                require_success(run([executable, "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
                                     "--no-input", "--no-cache-dir", "playwright==" + PLAYWRIGHT_VERSION], env), stage)
            stage = "prepare_browser"
            progress(stage)
            chrome = configuration.chrome_executable() if selected["browser_channel"] == "chrome" else None
            if selected["browser_channel"] == "chrome":
                if chrome is None:
                    raise SetupError("Google Chrome was selected but its executable was not found. Install Chrome or explicitly choose --browser-channel chromium.")
                print("Using the installed Chrome program with a separate monitoring profile…", file=sys.stderr)
            else:
                stage = "install_chromium"
                progress(stage)
                # Playwright skips binaries already installed for this exact driver revision.
                print("Preparing the dedicated Chromium browser…", file=sys.stderr)
                require_success(run([executable, "-m", "playwright", "install", "chromium"], env, 900), stage)
            stage = "browser_smoke"
            progress(stage)
            print("Checking that the monitoring browser starts and closes correctly…", file=sys.stderr)
            require_success(run([executable, "-c", SMOKE, selected["browser_channel"], str(chrome or "")], env, 60), stage)
            stage = "prepare_profile"
            progress(stage)
            init = run(browser_args + ["init"], env, 30)
            require_success(init, stage)
            stage = "doctor"
            progress(stage)
            doctor = run(browser_args + ["doctor"], env, 30)
            require_success(doctor, stage)
            init_result, doctor_result = json.loads(init.stdout), json.loads(doctor.stdout)
            if not isinstance(init_result, dict) or init_result.get("status") != "initialized":
                raise SetupError("The dedicated profile was not confirmed initialized")
            if not isinstance(doctor_result, dict) or doctor_result.get("status") != "ready":
                raise SetupError("The browser readiness check did not confirm ready")
            configuration.save_defaults(skill, selected["state_dir"], selected["profile"], selected["browser_channel"])
            result = {"status": "ready", "playwright_version": PLAYWRIGHT_VERSION,
                      "runtime": str(runtime), "browser_smoke": {"launched": True, "closed": True},
                      "profile": init_result, "doctor": doctor_result, "selection": selected,
                      "login_status": "not_checked", "next_steps": [
                          browser_args + ["login", "--platform", "x"],
                          browser_args + ["verify", "--platform", "x"],
                          browser_args + ["login", "--platform", "reddit"],
                          browser_args + ["verify", "--platform", "reddit"]],
                      "completed_at": datetime.now(timezone.utc).isoformat()}
            write_json(runtime / "setup.json", result)
            return result
        except (OSError, ValueError, SetupError) as exc:
            write_json(runtime / "setup.json", {"status": "setup_failed", "stage": stage, "error": str(exc)})
            raise SetupError(str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, help="optional private state root (kept outside the skill)")
    parser.add_argument("--profile", help="dedicated monitoring profile name; otherwise use the saved selection")
    parser.add_argument("--browser-channel", choices=["auto", "chrome", "chromium"],
                        help="reuse installed Chrome or prepare Chromium; new installations default to auto")
    args = parser.parse_args(argv)
    skill = Path(__file__).resolve().parents[1]
    resume = [sys.executable, str(Path(__file__).resolve())]
    if args.state_dir is not None:
        resume.extend(["--state-dir", str(args.state_dir.expanduser().absolute())])
    if args.profile is not None:
        resume.extend(["--profile", args.profile])
    if args.browser_channel is not None:
        resume.extend(["--browser-channel", args.browser_channel])
    if sys.version_info < (3, 10):
        print(json.dumps({"status": "setup_failed", "error": "Python 3.10 or later is required"}))
        return 2
    try:
        result = setup(skill, args.state_dir, args.profile, args.browser_channel)
    except (OSError, ValueError, SetupError) as exc:
        print(json.dumps({"status": "setup_failed", "error": str(exc), "resume_argv": resume,
                          "hint": "Keep this installation and rerun setup after fixing the reported dependency or download issue. No account login was attempted."}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
