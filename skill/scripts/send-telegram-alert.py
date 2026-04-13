#!/usr/bin/env python
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a Telegram Bot API message.")
    parser.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"))
    parser.add_argument("--chat-id", default=os.environ.get("TELEGRAM_CHAT_ID"))
    parser.add_argument("--message", required=True)
    parser.add_argument("--parse-mode", default="Markdown")
    parser.add_argument("--disable-link-preview", action="store_true")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Missing Telegram bot token. Provide --token or TELEGRAM_BOT_TOKEN.")
    if not args.chat_id:
        raise SystemExit("Missing Telegram chat id. Provide --chat-id or TELEGRAM_CHAT_ID.")

    url = f"https://api.telegram.org/bot{args.token}/sendMessage"
    payload = {
        "chat_id": args.chat_id,
        "text": args.message,
        "parse_mode": args.parse_mode,
        "disable_web_page_preview": args.disable_link_preview,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Telegram API request failed: {exc}") from exc

    parsed = json.loads(body)
    if not parsed.get("ok"):
        raise SystemExit(f"Telegram API returned failure: {body}")
    print(json.dumps({"ok": True, "chat_id": args.chat_id, "message_id": parsed["result"]["message_id"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
