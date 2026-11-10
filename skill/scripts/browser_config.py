"""Persist the monitoring profile selection; never store account credentials."""

import json
import os
from pathlib import Path
import re
import stat
import sys


def default_state_dir():
    if sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    return base / "brand-reputation-monitor"


def chrome_executable():
    """Inspect installed program paths only; never inspect personal browser data."""
    if sys.platform == "darwin":
        candidates = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                      Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    elif os.name == "nt":
        candidates = [Path(base) / "Google/Chrome/Application/chrome.exe" for base in
                      (os.environ.get("PROGRAMFILES", "C:/Program Files"),
                       os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"),
                       os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))]
    else:
        candidates = [Path("/opt/google/chrome/chrome"), Path("/usr/bin/google-chrome"),
                      Path("/usr/bin/google-chrome-stable")]
    return next((path for path in candidates if path.is_file()), None)


def validate(value):
    if not isinstance(value, dict) or set(value) != {"state_dir", "profile", "browser_channel"}:
        raise ValueError("Browser configuration must contain only state_dir, profile and browser_channel")
    state, profile = value["state_dir"], value["profile"]
    if not isinstance(state, str) or not state or len(state) > 4096 or any(ord(c) < 32 for c in state):
        raise ValueError("The saved browser state directory is invalid")
    if not Path(state).is_absolute():
        raise ValueError("The saved browser state directory must be absolute")
    if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", profile):
        raise ValueError("The saved browser profile name is invalid")
    if not isinstance(value["browser_channel"], str) or value["browser_channel"] not in {"chrome", "chromium"}:
        raise ValueError("The saved browser channel is invalid")
    return {"state_dir": state, "profile": profile, "browser_channel": value["browser_channel"]}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate browser configuration field")
        result[key] = value
    return result


def config_path(skill):
    runtime = Path(skill) / ".runtime"
    path = runtime / "browser-config.json"
    if runtime.is_symlink() or path.is_symlink():
        raise ValueError("Browser configuration must not be redirected through a symlink")
    return path


def load_defaults(skill):
    path = config_path(skill)
    if not path.exists():
        return {}
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 16384:
            raise ValueError("Browser configuration must be a small regular JSON file")
        raw = stream.read(16385)
    if len(raw) > 16384:
        raise ValueError("Browser configuration is too large")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    if isinstance(value, dict) and set(value) == {"state_dir", "profile"}:
        # Earlier installations prepared Chromium. Preserve that engine selection.
        value["browser_channel"] = "chromium"
    return validate(value)


def resolve_defaults(skill, state_dir=None, profile=None, browser_channel=None):
    saved = load_defaults(skill)
    state = state_dir if state_dir is not None else saved.get("state_dir", default_state_dir())
    name = profile if profile is not None else saved.get("profile", "default")
    channel = browser_channel if browser_channel is not None else saved.get("browser_channel", "auto")
    if channel == "auto":
        channel = "chrome" if chrome_executable() is not None else "chromium"
    return validate({"state_dir": str(Path(state).expanduser().absolute()), "profile": name,
                     "browser_channel": channel})


def save_defaults(skill, state_dir, profile, browser_channel="chromium"):
    value = validate({"state_dir": str(Path(state_dir).expanduser().absolute()), "profile": profile,
                      "browser_channel": browser_channel})
    path = config_path(skill)
    if not path.parent.is_dir():
        raise ValueError("Prepare the skill runtime before saving its browser configuration")
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    if os.name != "nt":
        temporary.chmod(0o600)
    os.replace(temporary, path)
    return value
