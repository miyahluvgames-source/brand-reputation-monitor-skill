#!/usr/bin/env python3
"""Install the repository's skill without replacing an existing installation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("skill source must be a real directory")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in skill source: " + str(path.relative_to(root)))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "SKILL.md" not in result:
        raise ValueError("source is missing SKILL.md")
    return result


def install(source, destination):
    expected = inventory(source)
    # Do not resolve the destination before this check: even a dangling symlink
    # is an existing object and must not be followed or replaced.
    if os.path.lexists(destination):
        raise FileExistsError("destination already exists; review or back it up before installing")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=False)
    actual = inventory(destination)
    if actual != expected:
        raise ValueError("installed files failed SHA256 readback; retain the directory for inspection")
    return {"status": "installed", "destination": str(destination.absolute()),
            "files_verified": len(actual), "sha256_verified": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    parser.add_argument("--dest", type=Path, default=home / "skills/brand-reputation-monitor",
                        help="exact destination directory (must not exist)")
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parents[1] / "skill"
    try:
        result = install(source, args.dest.expanduser())
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
