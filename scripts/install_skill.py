#!/usr/bin/env python3
"""Install the complete skill and prepare its dedicated monitoring browser."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def generated(path):
    return any(part in {".runtime", "__pycache__"} for part in path.parts) or path.suffix in {".pyc", ".pyo"}


def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("skill source must be a real directory")
    result = {}
    for path in sorted(root.rglob("*")):
        if generated(path.relative_to(root)):
            continue
        if path.is_symlink():
            raise ValueError("symlink in skill source: " + str(path.relative_to(root)))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "SKILL.md" not in result:
        raise ValueError("source is missing SKILL.md")
    return result


def install(source, destination):
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("destination must be outside the source skill directory")
    expected = inventory(source)
    # Do not resolve the destination before this check: even a dangling symlink
    # is an existing object and must not be followed or replaced.
    if os.path.lexists(destination):
        raise FileExistsError("destination already exists; review or back it up before installing")
    destination.parent.mkdir(parents=True, exist_ok=True)
    def ignore(directory, names):
        return [name for name in names if generated(Path(directory).relative_to(source) / name)]
    shutil.copytree(source, destination, symlinks=False, ignore=ignore)
    actual = inventory(destination)
    if actual != expected:
        raise ValueError("installed files failed SHA256 readback; retain the directory for inspection")
    return {"status": "installed", "destination": str(destination.absolute()),
            "files_verified": len(actual), "sha256_verified": True}


def install_and_setup(source, destination, skill_only=False, state_dir=None, profile=None, browser_channel=None):
    result = install(source, destination)
    setup_script = destination.absolute() / "scripts/setup.py"
    resume = [sys.executable, str(setup_script)]
    if state_dir is not None:
        resume.extend(["--state-dir", str(Path(state_dir).expanduser().absolute())])
    if profile is not None:
        resume.extend(["--profile", profile])
    if browser_channel is not None:
        resume.extend(["--browser-channel", browser_channel])
    result["setup_argv"] = resume
    result["login_status"] = "not_checked"
    if skill_only:
        result["status"] = "skill_installed"
        result["browser_status"] = "setup_required"
        return result
    if not setup_script.is_file():
        result.update(status="setup_failed", error="The skill is missing scripts/setup.py")
        return result
    # setup.py owns bounded dependency operations and closes its smoke-test browser.
    # Keep its stderr visible so the user sees progress during the download.
    try:
        child = subprocess.run(resume, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    except OSError as exc:
        result.update(status="setup_failed", browser_status="setup_required", error=str(exc))
        return result
    try:
        setup_result = json.loads(child.stdout)
        if not isinstance(setup_result, dict):
            raise ValueError("setup result must be an object")
    except ValueError:
        setup_result = {"status": "setup_failed", "error": "Setup did not return a readable result; rerun setup using setup_argv"}
    result["setup"] = setup_result
    ready = child.returncode == 0 and setup_result.get("status") == "ready"
    result["status"] = "ready" if ready else "setup_failed"
    result["browser_status"] = "ready" if ready else "setup_required"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    parser.add_argument("--dest", type=Path, default=home / "skills/brand-reputation-monitor",
                        help="exact destination directory (must not exist)")
    parser.add_argument("--skill-only", action="store_true", help="copy the self-contained skill; defer browser setup")
    parser.add_argument("--state-dir", type=Path, help="optional private monitoring state root")
    parser.add_argument("--profile", help="dedicated monitoring profile name; otherwise use the saved selection")
    parser.add_argument("--browser-channel", choices=["auto", "chrome", "chromium"],
                        help="reuse installed Chrome or prepare Chromium; new installations default to auto")
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parents[1] / "skill"
    try:
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10 or later is required")
        result = install_and_setup(source, args.dest.expanduser(), args.skill_only,
                                   args.state_dir, args.profile, args.browser_channel)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "setup_failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
