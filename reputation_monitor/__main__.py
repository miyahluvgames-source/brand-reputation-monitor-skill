"""Command-line interface. Reads files; never collects sources or sends alerts."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .coverage import check, load_json, template
from .report import render_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("template", "check", "report"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        if name != "template":
            command.add_argument("--record", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        plan = load_json(args.plan)
        if args.command == "template":
            result = template(plan)
        else:
            record = load_json(args.record)
            result = check(plan, record)
            if args.command == "report" and not result["errors"]:
                print(render_report(plan, record, result))
                return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"status": "input_error", "errors": [str(exc)]},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
