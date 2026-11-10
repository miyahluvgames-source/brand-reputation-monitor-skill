#!/usr/bin/env python3
"""Dedicated, persistent monitoring browser. No daemon and no credential export."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = SKILL_ROOT / ".runtime"
PROFILE_SCHEMA = "brand-reputation-monitor/browser-profile/1"
MAX_TEXT = 40000
MAX_LINKS = 100
PLATFORMS = {
    "x": {"home": "https://x.com/home", "login": "https://x.com/i/flow/login",
          "authenticated": ['[data-testid="SideNav_AccountSwitcher_Button"]'],
          "signed_out": ['[data-testid="loginButton"]', 'input[autocomplete="username"]']},
    "reddit": {"home": "https://www.reddit.com/", "login": "https://www.reddit.com/login/",
               "authenticated": ['#expand-user-drawer-button',
                                 '[data-testid="user-menu-button"]'],
               "signed_out": ['a[href="https://www.reddit.com/login/"]',
                              'input[autocomplete="username"]']},
}
SECRET_QUERY = re.compile(r"(?:token|password|passwd|secret|session|authorization|auth|api.?key|signature|credential|^code$|^key$|^sig$|^jwt$)", re.I)


class BrowserError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def configuration_module():
    spec = importlib.util.spec_from_file_location("monitor_browser_config", SKILL_ROOT / "scripts/browser_config.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_configuration(state_dir=None, profile=None, browser_channel=None):
    try:
        return configuration_module().resolve_defaults(SKILL_ROOT, state_dir, profile, browser_channel)
    except (OSError, ValueError) as exc:
        raise BrowserError("invalid_configuration", str(exc)) from exc


def safe_url(value):
    if not isinstance(value, str) or len(value) > 8192 or any(ord(c) < 32 for c in value):
        raise BrowserError("invalid_url", "Use a valid HTTP(S) URL.")
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        raise BrowserError("invalid_url", "Use a valid HTTP(S) URL.") from None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise BrowserError("invalid_url", "Only credential-free HTTP(S) URLs are supported.")
    return value


def public_url(value):
    """Avoid echoing authentication query strings or credentials in diagnostics."""
    try:
        p = urlsplit(value)
        host = p.hostname or ""
        if ":" in host:
            host = "[" + host + "]"
        if p.port:
            host += ":" + str(p.port)
        return urlunsplit((p.scheme, host, p.path, "", ""))
    except ValueError:
        return ""


def evidence_url(value):
    """Keep search parameters while excluding common login/token URL parameters."""
    try:
        safe_url(value)
        p = urlsplit(value)
        query = [(key, val) for key, val in parse_qsl(p.query, keep_blank_values=True) if not SECRET_QUERY.search(key)]
        return urlunsplit((p.scheme, p.netloc, p.path, urlencode(query), ""))
    except BrowserError:
        return public_url(value)


def platform_for_url(url):
    host = (urlsplit(url).hostname or "").lower()
    if host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        return "x"
    if host == "reddit.com" or host.endswith(".reddit.com"):
        return "reddit"
    return None


def search_url(platform, query):
    if not query.strip() or len(query) > 1000 or any(ord(c) < 32 for c in query):
        raise BrowserError("invalid_query", "Search query must contain 1–1000 printable characters.")
    if platform == "x":
        return "https://x.com/search?" + urlencode({"q": query, "src": "typed_query", "f": "live"})
    if platform == "reddit":
        return "https://www.reddit.com/search/?" + urlencode({"q": query, "sort": "new"})
    return "https://www.bing.com/search?" + urlencode({"q": query})


def profile_dir(state_dir, name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", name):
        raise BrowserError("invalid_profile", "Profile name must be 1–48 letters, digits, underscores or hyphens.")
    base = Path(state_dir).expanduser().absolute()
    # Do not let an apparently dedicated profile redirect into a personal one.
    for p in [base, base / "profiles", base / "profiles" / name,
              base / "profiles" / name / "chromium", base / "profiles" / name / "chrome"]:
        if p.is_symlink():
            raise BrowserError("unsafe_profile", "Profile paths must not contain symbolic links.")
    return base / "profiles" / name


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    if os.name != "nt":
        temporary.chmod(0o600)
    os.replace(temporary, path)


def prepare_profile(path):
    marker = path / "monitor-profile.json"
    if path.exists():
        if not path.is_dir() or marker.is_symlink() or not marker.is_file():
            raise BrowserError("unowned_profile", "Existing directory is not a monitoring profile. Choose a new profile name.")
        try:
            value = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise BrowserError("invalid_profile_marker", "Profile ownership metadata is unreadable; preserve it for inspection.") from None
        if value.get("schema") != PROFILE_SCHEMA:
            raise BrowserError("unowned_profile", "Profile ownership marker does not match this tool.")
    else:
        path.mkdir(parents=True, mode=0o700)
        atomic_json(marker, {"schema": PROFILE_SCHEMA, "created_at": utc_now(), "purpose": "reputation monitoring"})
    if os.name != "nt":
        path.chmod(0o700)
    return path


def remaining(args, ceiling=30):
    seconds = getattr(args, "_deadline", time.monotonic() + args.timeout) - time.monotonic()
    if seconds <= 0:
        raise BrowserError("operation_timeout", "The command deadline expired. Preserve this profile and inspect before continuing.")
    return min(seconds, ceiling)


@contextmanager
def profile_lock(path):
    lock_path = path / "monitor.lock"
    if lock_path.is_symlink():
        raise BrowserError("unsafe_profile", "Refusing a symbolic-link lock file.")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    stream = os.fdopen(os.open(lock_path, flags, 0o600), "r+b")
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt
            if stream.seek(0, 2) == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise BrowserError("profile_busy", "This monitoring profile is in use. Finish or close its current command first.") from None
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise BrowserError("profile_busy", "This monitoring profile is in use. Finish or close its current command first.") from None
        acquired = True
        yield
    finally:
        if acquired:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        raise BrowserError("setup_required", "Run python3 " + str(SKILL_ROOT / "scripts/setup.py") + " to prepare the browser runtime.") from None


def configure_cache(cache):
    # A copied skill must not silently borrow another Playwright installation.
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(cache or RUNTIME / "browsers").expanduser().absolute())


def doctor(args):
    configure_cache(args.browser_cache)
    result = {"status": "setup_required", "profile": str(profile_dir(args.state_dir, args.profile)),
              "browser_started": False, "runtime_python": sys.executable,
              "browser_cache": os.environ["PLAYWRIGHT_BROWSERS_PATH"],
              "browser_channel": getattr(args, "browser_channel", "chromium")}
    result["browser_data_dir"] = str(Path(result["profile"]) / result["browser_channel"])
    try:
        factory = load_playwright()
        with factory() as playwright:
            if result["browser_channel"] == "chrome":
                executable = configuration_module().chrome_executable()
            else:
                executable = Path(playwright.chromium.executable_path)
            installed = executable is not None and Path(executable).is_file()
            result.update({"playwright_available": True, "browser_installed": installed})
            result["status"] = "ready" if installed else "browser_install_required"
    except BrowserError as exc:
        result.update({"playwright_available": False, "message": str(exc)})
    return result


@contextmanager
def browser_context(args, path, login=False):
    configure_cache(args.browser_cache)
    with profile_lock(path):
        with load_playwright()() as playwright:
            context = None
            try:
                channel = getattr(args, "browser_channel", "chromium")
                options = {}
                if channel == "chrome":
                    executable = configuration_module().chrome_executable()
                    if executable is None:
                        raise BrowserError("browser_install_required", "The selected Chrome program is unavailable. Run setup to select an installed browser.")
                    options["executable_path"] = str(executable)
                context = playwright.chromium.launch_persistent_context(
                    str(path / channel), headless=False if login else not args.headed,
                    channel=channel, timeout=remaining(args) * 1000, accept_downloads=False,
                    viewport={"width": 1280, "height": 900}, **options)
                context.set_default_timeout(min(args.timeout, 15) * 1000)
                context.set_default_navigation_timeout(min(args.timeout, 30) * 1000)
                yield context
            finally:
                if context is not None:
                    context.close()


def visible(page, selector):
    try:
        return page.locator(selector).first.is_visible()
    except Exception:
        return False


def login_observation(page, platform):
    if platform not in PLATFORMS or platform_for_url(page.url) != platform:
        return {"state": "unknown", "basis": "no_supported_platform_document"}
    signed_out = any(visible(page, selector) for selector in PLATFORMS[platform]["signed_out"])
    for selector in PLATFORMS[platform]["authenticated"]:
        if visible(page, selector):
            if signed_out:
                return {"state": "unknown", "basis": "conflicting_visible_account_controls"}
            if platform == "reddit":
                # Reddit can expose a generic user menu to signed-out visitors.
                # Require a separate, explicit logged-in app state as well.
                try:
                    explicit = page.evaluate("""() => ['shreddit-app', 'shreddit-header-buttons'].some(tag => {
                        const value = document.querySelector(tag)?.getAttribute('logged-in');
                        return value === '' || value === 'true';
                    })""")
                except Exception:
                    return {"state": "unknown", "basis": "document_transition"}
                if explicit is not True:
                    return {"state": "unknown", "basis": "generic_menu_without_authenticated_app_state"}
            return {"state": "authenticated", "basis": "visible_account_control", "selector": selector}
    if signed_out:
        return {"state": "signed_out", "basis": "visible_sign_in_control"}
    return {"state": "unknown", "basis": "no_recognized_account_control"}


def classify_access(url, title, body, http_status=None, challenge_control=False):
    text = body[:8000].strip().lower()
    if http_status in {401, 403, 429}:
        return "access_restricted"
    gate_title = re.fullmatch(r"(?:just a moment(?:\.\.\.)?|verify (?:you are|you're) human|security verification|checking your browser(?:\.\.\.)?|attention required!?)(?:\s*[|—-]\s*cloudflare)?", title.strip(), re.I)
    gate_prefixes = ("verify you are human", "checking your browser", "you've been blocked by network security",
                     "our systems have detected unusual traffic", "please complete the captcha", "prove you're not a robot")
    sparse_gate = len(body) < 1500 and any(text.startswith(phrase) for phrase in gate_prefixes)
    widget_gate = challenge_control and len(body) < 2000 and any(phrase in text for phrase in gate_prefixes)
    if gate_title or sparse_gate or widget_gate:
        return "challenge"
    parsed = urlsplit(url)
    if platform_for_url(url) and any(p in parsed.path.lower() for p in ("/login", "/i/flow/login", "/account/access")):
        return "login_required"
    if http_status and http_status >= 400:
        return "http_error"
    return "readable" if body.strip() else "empty"


def challenge_visible(page):
    return any(visible(page, selector) for selector in ("#challenge-running", "#cf-challenge-running", "form#challenge-form"))


def wait_for_account_document(page, platform, args):
    """Give client-rendered account controls a bounded chance to appear."""
    end = time.monotonic() + remaining(args, 8)
    while time.monotonic() < end:
        state = login_observation(page, platform)
        if state["state"] != "unknown" or challenge_visible(page):
            return state
        page.wait_for_timeout(min(400, max(1, (end - time.monotonic()) * 1000)))
    return login_observation(page, platform)


EXTRACT = """() => ({
  title: document.title,
  text: (document.body?.innerText || '').slice(0, 40001),
  links: Array.from(document.querySelectorAll('a[href]')).slice(0, 500)
    .map(a => ({text: (a.innerText || '').trim().slice(0, 240), url: a.href})),
  times: Array.from(document.querySelectorAll('time')).slice(0, 50)
    .map(t => ({datetime: t.getAttribute('datetime'), text: (t.innerText || '').slice(0, 200)}))
})"""


def extract(page, requested_url, response=None):
    payload = page.evaluate(EXTRACT)
    http_status = response.status if response else None
    body = payload.get("text", "")
    access = classify_access(page.url, payload.get("title", ""), body, http_status, challenge_visible(page))
    links = []
    seen = set()
    for link in payload.get("links", []):
        try:
            url = safe_url(link.get("url"))
        except BrowserError:
            continue
        if url in seen:
            continue
        seen.add(url)
        # Authentication links are not research leads and may contain one-time tokens.
        if any(SECRET_QUERY.search(key) for key, val in parse_qsl(urlsplit(url).query, keep_blank_values=True)):
            continue
        links.append({"text": link.get("text", ""), "url": evidence_url(url)})
        if len(links) == MAX_LINKS:
            break
    return {"status": access, "requested_url": evidence_url(requested_url), "url": evidence_url(page.url),
            "source_url_redacted": evidence_url(requested_url) != requested_url or evidence_url(page.url) != page.url,
            "observed_at": utc_now(), "http_status": http_status,
            "title": payload.get("title", ""),
            "text": body[:MAX_TEXT] if access == "readable" else "",
            "text_truncated": len(body) > MAX_TEXT,
            "links": links if access == "readable" else [],
            "source_times": payload.get("times", []) if access == "readable" else [],
            "login": login_observation(page, platform_for_url(page.url)),
            "coverage": "rendered_page_sample", "media_inspected": False}


def open_page(context, url, timeout, wait_ms=1500):
    page = context.pages[0] if context.pages else context.new_page()
    response = page.goto(url, wait_until="domcontentloaded", timeout=min(timeout, 30) * 1000)
    page.wait_for_timeout(min(wait_ms, max(0, timeout * 1000 - 1000)))
    return page, response


def read_page(args, path, url):
    safe_url(url)
    with browser_context(args, path) as context:
        page, response = open_page(context, url, remaining(args))
        result = extract(page, url, response)
        requested_scrolls = getattr(args, "scrolls", 0)
        result["scrolls_requested"] = requested_scrolls
        result["scrolls_completed"] = 0
        if requested_scrolls:
            samples = [{k: v for k, v in result.items() if not k.startswith("scrolls_")}]
            for index in range(requested_scrolls):
                if samples[-1]["status"] != "readable":
                    break
                remaining(args)
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(min(750, remaining(args) * 1000))
                samples.append(extract(page, url, response))
                result["scrolls_completed"] += 1
            result["samples"] = samples
            result["coverage"] = "rendered_page_samples"
            # Top-level text describes the first sample; later virtualized content
            # stays in ordered samples rather than replacing earlier evidence.
            if result["status"] == "readable" and samples[-1]["status"] != "readable":
                result["status"] = "partial"
    result["browser_closed"] = True
    return result


def verify_login(args, path):
    url = PLATFORMS[args.platform]["home"]
    with browser_context(args, path) as context:
        page, response = open_page(context, url, remaining(args))
        observation = wait_for_account_document(page, args.platform, args)
        body = page.locator("body").inner_text(timeout=3000)[:8000]
        access = classify_access(page.url, page.title(), body, response.status if response else None, challenge_visible(page))
        if access in {"challenge", "access_restricted", "http_error"}:
            observation = {"state": "unknown", "basis": access}
        result = {"status": observation["state"], "platform": args.platform,
                  "checked_at": utc_now(), "page": public_url(page.url),
                  "evidence": observation, "access": access, "browser_closed": True,
                  "browser_channel": getattr(args, "browser_channel", "chromium")}
    atomic_json(path / ("last-login-" + args.platform + "-" + result["browser_channel"] + ".json"), result)
    return result


def login(args, path):
    authenticated = None
    end = time.monotonic() + args.timeout
    reason = "timeout"
    print("A dedicated monitoring browser is opening. Sign in yourself, complete any MFA, then close its window. Credentials stay in that profile. Run verify afterwards.", file=sys.stderr, flush=True)
    with browser_context(args, path, login=True) as context:
        page, response = open_page(context, PLATFORMS[args.platform]["login"], remaining(args))
        while time.monotonic() < end:
            pages = [p for p in context.pages if not p.is_closed()]
            if not pages:
                reason = "window_closed"
                break
            page = pages[-1]
            current = login_observation(page, args.platform)
            try:
                body = page.locator("body").inner_text(timeout=1000)[:8000]
                access = classify_access(page.url, page.title(), body, challenge_control=challenge_visible(page))
                if access in {"challenge", "access_restricted", "http_error"}:
                    current = {"state": "unknown", "basis": access}
            except Exception:
                current = {"state": "unknown", "basis": "document_transition"}
            if current["state"] == "authenticated":
                authenticated = {"observed_at": utc_now(), "page": public_url(page.url), "evidence": current}
            try:
                page.wait_for_timeout(500)
            except Exception:
                if not [p for p in context.pages if not p.is_closed()]:
                    reason = "window_closed"
                    break
                raise
    return {"status": "verification_required", "platform": args.platform,
            "ended_by": reason, "browser_closed": True, "observed_authenticated": authenticated,
            "next_step": "Run verify --platform " + args.platform + " to check the persisted session."}


def status(args, path):
    records = {}
    channel = getattr(args, "browser_channel", "chromium")
    for platform in PLATFORMS:
        f = path / ("last-login-" + platform + "-" + channel + ".json")
        if f.is_file() and not f.is_symlink():
            try:
                records[platform] = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                records[platform] = {"status": "unreadable"}
    return {"status": "configured" if path.is_dir() else "not_initialized", "profile": str(path),
            "browser_channel": channel, "browser_data_dir": str(path / channel),
            "browser_started": False, "current_login": "not_checked",
            "previous_verifications": records, "note": "Stored results are historical. Run verify for current login state."}


def build_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir", type=Path, help="Override this installation's saved state directory")
    p.add_argument("--profile", help="Override this installation's saved profile name")
    p.add_argument("--browser-channel", choices=["chrome", "chromium"], help="Override the saved browser program for this command")
    p.add_argument("--browser-cache", type=Path, help="Explicit alternate Playwright browser cache for an existing approved installation")
    p.add_argument("--headed", action="store_true", help="Show a browser window during reads/verification")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("doctor", "status", "init"):
        sub.add_parser(command)
    for command in ("login", "verify", "read", "search"):
        c = sub.add_parser(command)
        c.add_argument("--timeout", type=int, default=900 if command == "login" else 45)
        if command in {"login", "verify"}:
            c.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
        elif command == "read":
            c.add_argument("url")
        else:
            c.add_argument("--platform", choices=["web", "x", "reddit"], default="web")
            c.add_argument("--query", required=True)
        if command in {"read", "search"}:
            c.add_argument("--scrolls", type=int, choices=range(4), default=0,
                           help="Read 0–3 additional scroll samples, preserving earlier rendered content")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        config = resolve_configuration(args.state_dir, args.profile, args.browser_channel)
        args.state_dir = Path(config["state_dir"])
        args.profile = config["profile"]
        args.browser_channel = config["browser_channel"]
        path = profile_dir(args.state_dir, args.profile)
        if hasattr(args, "timeout") and not (5 <= args.timeout <= (1800 if args.command == "login" else 120)):
            raise BrowserError("invalid_timeout", "Use 5–120 seconds for reads, or 5–1800 for manual login.")
        if hasattr(args, "timeout"):
            args._deadline = time.monotonic() + args.timeout
        if args.command == "doctor":
            result = doctor(args)
        elif args.command == "status":
            result = status(args, path)
        else:
            prepare_profile(path)
            if args.command == "init":
                result = {"status": "initialized", "profile": str(path), "browser_started": False}
            elif args.command == "read":
                result = read_page(args, path, args.url)
            elif args.command == "search":
                result = read_page(args, path, search_url(args.platform, args.query))
                result.update({"query": args.query, "platform": args.platform})
            elif args.command == "verify":
                result = verify_login(args, path)
            else:
                result = login(args, path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in {"ready", "initialized", "configured", "readable", "partial", "authenticated", "verification_required"} else 1
    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted", "message": "Command interrupted; preserve the monitoring profile and verify before continuing."}))
        return 130
    except BrowserError as exc:
        print(json.dumps({"status": "error", "code": exc.code, "message": str(exc)}))
        return 2
    except Exception as exc:
        # Playwright exceptions can contain full navigated URLs, tokens or page text.
        print(json.dumps({"status": "error", "code": type(exc).__name__,
                          "message": "Browser operation did not complete. Keep this profile; use doctor and a visible verification to diagnose. No automatic retry was made."}))
        return 2


def use_installed_runtime():
    venv = RUNTIME / "venv"
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if python.is_file() and Path(sys.prefix).resolve() != venv.resolve():
        os.execv(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]])


if __name__ == "__main__":
    use_installed_runtime()
    raise SystemExit(main())
