import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("monitor_browser", ROOT / "skill/scripts/browser.py")
browser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser)


class FakeLocator:
    def __init__(self, visible):
        self.first = self
        self.value = visible

    def is_visible(self):
        return self.value


class FakePage:
    def __init__(self, url="https://example.com/news", payload=None, visible=()):
        self.url = url
        self.payload = payload or {"title": "News", "text": "A rendered public article", "links": [], "times": []}
        self.visible = visible

    def locator(self, selector):
        return FakeLocator(selector in self.visible)

    def evaluate(self, source):
        return self.payload


class BrowserContractTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)

    def test_init_creates_separate_named_profile_and_readback_marker(self):
        profile = browser.profile_dir(self.base, "review")
        self.assertEqual(profile, self.base / "profiles/review")
        browser.prepare_profile(profile)
        self.assertEqual(json.loads((profile / "monitor-profile.json").read_text())["schema"], browser.PROFILE_SCHEMA)
        self.assertEqual(browser.prepare_profile(profile), profile)

    def test_unowned_existing_directory_never_adopted(self):
        profile = browser.profile_dir(self.base, "review")
        profile.mkdir(parents=True)
        (profile / "Cookies").write_text("private")
        with self.assertRaisesRegex(browser.BrowserError, "not a monitoring profile"):
            browser.prepare_profile(profile)
        self.assertEqual((profile / "Cookies").read_text(), "private")
        self.assertFalse((profile / "monitor-profile.json").exists())

    def test_profile_traversal_rejected(self):
        for name in ("../Default", "/tmp/profile", "a/b", "a\\b", "", "x" * 49):
            with self.subTest(name=name), self.assertRaises(browser.BrowserError):
                browser.profile_dir(self.base, name)

    def test_symlinked_chromium_directory_rejected(self):
        profile = browser.prepare_profile(browser.profile_dir(self.base, "review"))
        target = self.base / "personal"
        target.mkdir()
        try:
            (profile / "chromium").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation is unavailable")
        with self.assertRaises(browser.BrowserError):
            browser.profile_dir(self.base, "review")

    def test_lock_refuses_overlap_and_releases_after_exception(self):
        profile = browser.prepare_profile(browser.profile_dir(self.base, "review"))
        with self.assertRaisesRegex(RuntimeError, "fixture"):
            with browser.profile_lock(profile):
                with self.assertRaisesRegex(browser.BrowserError, "in use"):
                    with browser.profile_lock(profile):
                        self.fail("A second owner acquired the profile")
                raise RuntimeError("fixture")
        with browser.profile_lock(profile):
            pass

    def test_urls_reject_non_web_and_credentials(self):
        for url in ("file:///etc/passwd", "javascript:alert(1)", "https://u:p@example.com", "https://e.test:bad", "https://e.test/\nfoo"):
            with self.subTest(url=url), self.assertRaises(browser.BrowserError):
                browser.safe_url(url)
        self.assertEqual(browser.safe_url("http://127.0.0.1:8000/fixture"), "http://127.0.0.1:8000/fixture")

    def test_search_encodes_query_and_selects_recent_sort(self):
        self.assertIn("q=brand+%26+product", browser.search_url("x", "brand & product"))
        self.assertIn("f=live", browser.search_url("x", "brand"))
        self.assertIn("sort=new", browser.search_url("reddit", "brand"))
        with self.assertRaises(browser.BrowserError):
            browser.search_url("web", "   ")

    def test_platform_host_matching_avoids_lookalike_domains(self):
        self.assertIsNone(browser.platform_for_url("https://x.com.attacker.test/"))
        self.assertIsNone(browser.platform_for_url("https://notreddit.com/"))
        self.assertEqual(browser.platform_for_url("https://old.reddit.com/"), "reddit")

    def test_visible_account_control_is_required_for_authentication(self):
        page = FakePage("https://x.com/home")
        self.assertEqual(browser.login_observation(page, "x")["state"], "unknown")
        page.visible = ['[data-testid="SideNav_AccountSwitcher_Button"]']
        self.assertEqual(browser.login_observation(page, "x")["state"], "authenticated")
        page.url = "https://example.com/"
        self.assertEqual(browser.login_observation(page, "x")["state"], "unknown")

    def test_access_restriction_is_not_usable_evidence(self):
        page = FakePage(payload={"title": "Verify you are human", "text": "security verification", "links": [{"url": "https://e.test", "text": "verify"}]})
        record = browser.extract(page, page.url)
        self.assertEqual(record["status"], "challenge")
        self.assertEqual(record["text"], "")
        self.assertEqual(record["links"], [])
        self.assertEqual(browser.classify_access("https://x.com/i/flow/login", "Log in", "Login"), "login_required")
        self.assertEqual(browser.classify_access("https://example.com", "Forbidden", "denied", 403), "access_restricted")

    def test_article_quoting_challenge_text_remains_readable(self):
        body = "An incident report discusses the phrase checking your browser and security verification. " * 40
        self.assertEqual(browser.classify_access("https://example.com", "Security verification explained", body), "readable")
        self.assertEqual(browser.classify_access("https://example.com", "News", "Customers reported seeing 'verify you are human' yesterday."), "readable")
        self.assertEqual(browser.classify_access("https://example.com", "Access", "Verify you are human before proceeding"), "challenge")

    def test_rendered_sample_has_bounds_and_filters_secret_links(self):
        payload = {"title": "Article", "text": "a" * (browser.MAX_TEXT + 1),
                   "links": [{"url": "https://example.com/?token=secret", "text": "auth"},
                             {"url": "https://u:p@example.com", "text": "secret"},
                             {"url": "javascript:evil()", "text": "bad"}] +
                            [{"url": "https://example.com/" + str(i), "text": "article"} for i in range(120)],
                   "times": [{"datetime": "2026-11-10", "text": "November 10"}]}
        record = browser.extract(FakePage(payload=payload), "https://example.com/news")
        self.assertTrue(record["text_truncated"])
        self.assertEqual(len(record["text"]), browser.MAX_TEXT)
        self.assertEqual(len(record["links"]), browser.MAX_LINKS)
        self.assertFalse(any("secret" in x["url"] for x in record["links"]))
        self.assertFalse(record["media_inspected"])

    def test_status_never_claims_current_login_from_saved_verification(self):
        path = browser.prepare_profile(browser.profile_dir(self.base, "review"))
        browser.atomic_json(path / "last-login-x-chromium.json", {"status": "authenticated", "checked_at": "2020-01-01"})
        result = browser.status(SimpleNamespace(), path)
        self.assertEqual(result["current_login"], "not_checked")
        self.assertFalse(result["browser_started"])
        self.assertEqual(result["previous_verifications"]["x"]["status"], "authenticated")
        self.assertEqual(browser.status(SimpleNamespace(browser_channel="chrome"), path)["previous_verifications"], {})

    def test_cli_reuses_saved_profile_and_explicit_override_is_temporary(self):
        skill = self.base / "installed-skill"
        (skill / "scripts").mkdir(parents=True)
        (skill / ".runtime").mkdir()
        (skill / "scripts/browser_config.py").write_text((ROOT / "skill/scripts/browser_config.py").read_text())
        chosen = self.base / "private-state"
        saved = {"state_dir": str(chosen), "profile": "chosen"}
        (skill / ".runtime/browser-config.json").write_text(json.dumps(saved))
        with patch.object(browser, "SKILL_ROOT", skill):
            for arguments, name in [(["init"], "chosen"), (["--profile", "temporary", "init"], "temporary"), (["status"], "chosen")]:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = browser.main(arguments)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out.getvalue())["profile"], str(chosen / "profiles" / name))
        self.assertEqual(json.loads((skill / ".runtime/browser-config.json").read_text()), saved)

    def test_diagnostic_url_omits_tokens_and_credentials(self):
        self.assertEqual(browser.public_url("https://user:secret@example.com/path?token=secret#fragment"), "https://example.com/path")

    def test_evidence_urls_redact_auth_query_but_preserve_search(self):
        page = FakePage("https://x.com/search?q=brand&code=private&access_token=secret&f=live#token")
        result = browser.extract(page, page.url)
        self.assertEqual(result["url"], "https://x.com/search?q=brand&f=live")
        self.assertEqual(result["requested_url"], result["url"])
        self.assertTrue(result["source_url_redacted"])

    def test_reddit_generic_menu_cannot_prove_authentication(self):
        page = FakePage("https://www.reddit.com/", visible=['#expand-user-drawer-button'])
        self.assertEqual(browser.login_observation(page, "reddit")["state"], "unknown")
        page.evaluate = lambda source: True
        self.assertEqual(browser.login_observation(page, "reddit")["state"], "authenticated")
        page.visible = ['#expand-user-drawer-button', 'input[autocomplete="username"]']
        self.assertEqual(browser.login_observation(page, "reddit")["state"], "unknown")

    def test_scroll_keeps_earlier_virtualized_content_and_stops_at_challenge(self):
        args = SimpleNamespace(timeout=30, scrolls=3)
        page = FakePage()
        wheel_calls = []
        page.mouse = SimpleNamespace(wheel=lambda *values: wheel_calls.append(values))
        page.wait_for_timeout = lambda milliseconds: None
        samples = [{"status": "readable", "text": "first item"},
                   {"status": "readable", "text": "second item"},
                   {"status": "challenge", "text": ""}]
        @contextlib.contextmanager
        def fixture_context(*args, **kwargs):
            yield SimpleNamespace()
        with patch.object(browser, "browser_context", fixture_context), patch.object(browser, "open_page", return_value=(page, None)), patch.object(browser, "extract", side_effect=samples):
            result = browser.read_page(args, self.base, "https://example.com")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["text"], "first item")
        self.assertEqual([s["text"] for s in result["samples"]], ["first item", "second item", ""])
        self.assertEqual(result["scrolls_completed"], 2)
        self.assertEqual(len(wheel_calls), 2)

    def test_context_closes_own_browser_when_collection_raises(self):
        path = browser.prepare_profile(browser.profile_dir(self.base, "review"))
        events = []

        class Context:
            def set_default_timeout(self, value):
                pass

            def set_default_navigation_timeout(self, value):
                pass

            def close(self):
                events.append("closed")

        class Chromium:
            def launch_persistent_context(self, user_data_dir, **kwargs):
                self.path = user_data_dir
                self.options = kwargs
                return Context()

        chromium = Chromium()
        @contextlib.contextmanager
        def factory():
            yield SimpleNamespace(chromium=chromium)

        args = SimpleNamespace(browser_cache=self.base / "cache", headed=False, timeout=20)
        with patch.object(browser, "load_playwright", return_value=factory):
            with self.assertRaisesRegex(RuntimeError, "read failed"):
                with browser.browser_context(args, path):
                    raise RuntimeError("read failed")
        self.assertEqual(events, ["closed"])
        self.assertEqual(chromium.path, str(path / "chromium"))
        self.assertFalse(chromium.options["accept_downloads"])
        with browser.profile_lock(path):
            pass
        args.browser_channel = "chrome"
        program = self.base / "Chrome-program"
        program.write_text("fixture")
        config = SimpleNamespace(chrome_executable=lambda: program)
        with patch.object(browser, "load_playwright", return_value=factory), patch.object(browser, "configuration_module", return_value=config):
            with browser.browser_context(args, path):
                pass
        self.assertEqual(chromium.path, str(path / "chrome"))
        self.assertEqual(chromium.options["channel"], "chrome")
        self.assertEqual(chromium.options["executable_path"], str(program))

    def test_cli_does_not_echo_playwright_exception_body(self):
        output = io.StringIO()
        with patch.object(browser, "read_page", side_effect=RuntimeError("secret-cookie-value")), contextlib.redirect_stdout(output):
            code = browser.main(["--state-dir", str(self.base), "read", "https://example.com"])
        self.assertEqual(code, 2)
        self.assertNotIn("secret-cookie", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["code"], "RuntimeError")


@unittest.skipUnless(os.environ.get("BRM_BROWSER_INTEGRATION") == "1", "Opt-in real Chromium fixture test")
class RealBrowserTests(unittest.TestCase):
    def test_rendered_collection_and_persistent_session(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading

        class Fixture(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                if self.path == "/seed":
                    self.send_header("Set-Cookie", "monitor_fixture=retained; Max-Age=3600; Path=/; SameSite=Lax")
                self.end_headers()
                if self.path == "/seed":
                    body = '<html><body><script>localStorage.setItem("fixture", "retained");document.body.append("rendered fixture ready")</script></body></html>'
                else:
                    cookie = "cookie retained" if "monitor_fixture=retained" in self.headers.get("Cookie", "") else "cookie missing"
                    body = '<html><body>' + cookie + '<script>document.body.append(" / localStorage " + localStorage.getItem("fixture"))</script></body></html>'
                self.wfile.write(body.encode())

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        thread = threading.Thread(target=server.serve_forever, daemon=False)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = browser.prepare_profile(browser.profile_dir(directory, "integration"))
                args = SimpleNamespace(browser_cache=os.environ.get("BRM_BROWSER_CACHE"),
                                       browser_channel=os.environ.get("BRM_BROWSER_CHANNEL", "chromium"),
                                       headed=False, timeout=30)
                base = "http://127.0.0.1:" + str(server.server_port)
                seed = browser.read_page(args, path, base + "/seed")
                self.assertEqual(seed["status"], "readable")
                self.assertIn("rendered fixture ready", seed["text"])
                check = browser.read_page(args, path, base + "/check")
                self.assertIn("cookie retained", check["text"])
                self.assertIn("localStorage retained", check["text"])
                self.assertTrue(seed["browser_closed"] and check["browser_closed"])
                with browser.profile_lock(path):
                    with self.assertRaises(browser.BrowserError):
                        browser.read_page(args, path, base + "/check")
                with browser.profile_lock(path):
                    pass
                # Exercise login's window-close path on the same local fixture.
                # Headless substitutes only the display in CI; no real account is used.
                original_context = browser.browser_context
                original_open = browser.open_page
                @contextlib.contextmanager
                def headless_login(args, path, login=False):
                    with original_context(args, path, login=False) as context:
                        yield context
                def open_then_close(context, url, timeout):
                    result = original_open(context, base + "/check", timeout, wait_ms=0)
                    context.close()
                    return result
                login_args = SimpleNamespace(browser_cache=args.browser_cache, browser_channel=args.browser_channel,
                                             headed=False, timeout=10, platform="x")
                with patch.object(browser, "browser_context", headless_login), patch.object(browser, "open_page", open_then_close), contextlib.redirect_stderr(io.StringIO()):
                    result = browser.login(login_args, path)
                self.assertEqual(result["ended_by"], "window_closed")
                self.assertEqual(result["status"], "verification_required")
                self.assertTrue(result["browser_closed"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
