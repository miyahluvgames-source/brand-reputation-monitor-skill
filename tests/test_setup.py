import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_setup", ROOT / "skill/scripts/setup.py")
setup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_module)


class SetupTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.skill = Path(folder.name) / "skill"
        (self.skill / "scripts").mkdir(parents=True)
        (self.skill / "scripts/browser.py").write_text("# fixture", encoding="utf-8")
        (self.skill / "scripts/browser_config.py").write_text(
            (ROOT / "skill/scripts/browser_config.py").read_text(encoding="utf-8"), encoding="utf-8")
        self.calls = []
        self.installed = False
        self.fail_stage = None
        self.stages = []

    def fake_run(self, argv, env, timeout=600):
        args = list(map(str, argv))
        self.calls.append((args, dict(env), timeout))
        self.stages.append(json.loads((self.skill / ".runtime/setup.json").read_text())["stage"])
        stage, stdout = "other", ""
        if "venv" in args:
            executable = setup_module.python_path(self.skill / ".runtime")
            executable.parent.mkdir(parents=True)
            executable.touch()
        elif any("version('playwright')" in arg for arg in args):
            return subprocess.CompletedProcess(args, 0 if self.installed else 1,
                                               setup_module.PLAYWRIGHT_VERSION if self.installed else "", "")
        elif "pip" in args:
            stage = "pip"
            self.installed = True
        elif "playwright" in args and "install" in args:
            stage = "chromium"
        elif setup_module.SMOKE in args:
            stage = "smoke"
            stdout = '{"launched":true,"closed":true}'
        elif args[-1] == "init":
            stage = "init"
            stdout = '{"status":"initialized","profile":"default"}'
        elif args[-1] == "doctor":
            stage = "doctor"
            stdout = '{"status":"ready"}'
        if stage == self.fail_stage:
            return subprocess.CompletedProcess(args, 1, "", "fixture failure")
        return subprocess.CompletedProcess(args, 0, stdout, "")

    def setup(self):
        with patch.object(setup_module, "run", side_effect=self.fake_run):
            return setup_module.setup(self.skill, self.skill.parent / "private-state", browser_channel="chromium")

    def test_complete_setup_checks_browser_before_ready(self):
        result = self.setup()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["login_status"], "not_checked")
        self.assertEqual(result["browser_smoke"], {"launched": True, "closed": True})
        commands = [c[0] for c in self.calls]
        smoke = next(i for i, cmd in enumerate(commands) if setup_module.SMOKE in cmd)
        init = next(i for i, cmd in enumerate(commands) if cmd[-1] == "init")
        self.assertLess(smoke, init)
        self.assertFalse(any("login" in cmd for cmd in commands))
        self.assertTrue(all(c[1]["PLAYWRIGHT_BROWSERS_PATH"] == str(self.skill / ".runtime/browsers") for c in self.calls))
        self.assertEqual(json.loads((self.skill / ".runtime/setup.json").read_text())["status"], "ready")
        self.assertEqual(set(self.stages), {"create_runtime", "install_playwright", "install_chromium",
                                          "browser_smoke", "prepare_profile", "doctor"})

    def test_second_setup_keeps_existing_runtime_and_skips_driver_install(self):
        self.setup()
        sentinel = self.skill / ".runtime/venv/customization"
        sentinel.write_text("keep", encoding="utf-8")
        self.calls.clear()
        self.setup()
        self.assertFalse(any("pip" in cmd or "venv" in cmd for cmd, _, _ in self.calls))
        self.assertTrue(any(setup_module.SMOKE in cmd for cmd, _, _ in self.calls))
        self.assertEqual(sentinel.read_text(), "keep")

    def test_setup_reuses_saved_selection_and_explicit_override_preserves_old_data(self):
        first_state = self.skill.parent / "state-one"
        old_profile = first_state / "profiles/research"
        old_profile.mkdir(parents=True)
        sentinel = old_profile / "login-fixture"
        sentinel.write_text("preserve", encoding="utf-8")
        with patch.object(setup_module, "run", side_effect=self.fake_run):
            first = setup_module.setup(self.skill, first_state, "research", "chromium")
            self.calls.clear()
            second = setup_module.setup(self.skill)
            self.assertEqual(first["selection"], second["selection"])
            self.assertTrue(all(cmd[cmd.index("--profile") + 1] == "research" for cmd, _, _ in self.calls if "--profile" in cmd))
            third = setup_module.setup(self.skill, self.skill.parent / "state-two", "review")
        self.assertEqual(third["selection"]["profile"], "review")
        self.assertEqual(sentinel.read_text(), "preserve")
        saved = json.loads((self.skill / ".runtime/browser-config.json").read_text())
        self.assertEqual(saved, third["selection"])

    def test_download_failure_retains_recoverable_installation(self):
        self.fail_stage = "chromium"
        with self.assertRaises(setup_module.SetupError):
            self.setup()
        receipt = json.loads((self.skill / ".runtime/setup.json").read_text())
        self.assertEqual(receipt["status"], "setup_failed")
        self.assertEqual(receipt["stage"], "install_chromium")
        self.assertTrue(setup_module.python_path(self.skill / ".runtime").exists())
        self.fail_stage = None
        self.assertEqual(self.setup()["status"], "ready")

    def test_smoke_failure_does_not_claim_ready_or_initialize_profile(self):
        self.fail_stage = "smoke"
        with self.assertRaises(setup_module.SetupError):
            self.setup()
        self.assertFalse(any(cmd[-1] == "init" for cmd, _, _ in self.calls))
        receipt = json.loads((self.skill / ".runtime/setup.json").read_text())
        self.assertEqual(receipt["stage"], "browser_smoke")

    def test_zero_exit_without_positive_readiness_is_not_ready(self):
        def ambiguous(argv, env, timeout=600):
            result = self.fake_run(argv, env, timeout)
            if str(argv[-1]) == "doctor":
                return subprocess.CompletedProcess(argv, 0, '{"status":"browser_install_required"}', "")
            return result
        with patch.object(setup_module, "run", side_effect=ambiguous):
            with self.assertRaises(setup_module.SetupError):
                setup_module.setup(self.skill, browser_channel="chromium")
        receipt = json.loads((self.skill / ".runtime/setup.json").read_text())
        self.assertEqual(receipt["status"], "setup_failed")
        self.assertEqual(receipt["stage"], "doctor")

    def test_auto_reuses_chrome_program_without_browser_download(self):
        chrome = self.skill.parent / "Google Chrome"
        chrome.touch()
        configuration = setup_module.load_config_module(self.skill)
        with patch.object(setup_module, "load_config_module", return_value=configuration), \
             patch.object(configuration, "chrome_executable", return_value=chrome), \
             patch.object(setup_module, "run", side_effect=self.fake_run):
            result = setup_module.setup(self.skill)
        self.assertEqual(result["selection"]["browser_channel"], "chrome")
        self.assertFalse(any("playwright" in args and "install" in args for args, _, _ in self.calls))
        smoke = next(args for args, _, _ in self.calls if setup_module.SMOKE in args)
        self.assertEqual(smoke[-2:], ["chrome", str(chrome)])

    def test_missing_chrome_uses_chromium_only_for_auto(self):
        configuration = setup_module.load_config_module(self.skill)
        with patch.object(setup_module, "load_config_module", return_value=configuration), \
             patch.object(configuration, "chrome_executable", return_value=None), \
             patch.object(setup_module, "run", side_effect=self.fake_run):
            result = setup_module.setup(self.skill)
            self.assertEqual(result["selection"]["browser_channel"], "chromium")
            self.calls.clear()
            with self.assertRaises(setup_module.SetupError):
                setup_module.setup(self.skill, browser_channel="chrome")
        self.assertFalse(any("playwright" in args and "install" in args for args, _, _ in self.calls))

    def test_existing_chrome_launch_failure_never_changes_engine(self):
        chrome = self.skill.parent / "Google Chrome"
        chrome.touch()
        configuration = setup_module.load_config_module(self.skill)
        self.fail_stage = "smoke"
        with patch.object(setup_module, "load_config_module", return_value=configuration), \
             patch.object(configuration, "chrome_executable", return_value=chrome), \
             patch.object(setup_module, "run", side_effect=self.fake_run):
            with self.assertRaises(setup_module.SetupError):
                setup_module.setup(self.skill)
        self.assertFalse(any("playwright" in args and "install" in args for args, _, _ in self.calls))
        self.assertFalse((self.skill / ".runtime/browser-config.json").exists())

    def test_unmarked_existing_runtime_is_protected(self):
        runtime = self.skill / ".runtime"
        runtime.mkdir()
        (runtime / "user-data").write_text("keep", encoding="utf-8")
        with self.assertRaises(setup_module.SetupError):
            self.setup()
        self.assertEqual(self.calls, [])
        self.assertFalse((runtime / "owner.json").exists())

    def test_corrupt_or_foreign_marker_is_protected(self):
        runtime = self.skill / ".runtime"
        runtime.mkdir()
        for content in ("{}", "not-json", '{"owner":"other"}'):
            (runtime / "owner.json").write_text(content, encoding="utf-8")
            with self.subTest(content=content), self.assertRaises(setup_module.SetupError):
                self.setup()
        self.assertEqual(self.calls, [])

    def test_environment_does_not_inherit_foreign_python_or_browser_destination(self):
        with patch.dict(setup_module.os.environ, {"PYTHONPATH": "/foreign", "PYTHONHOME": "/foreign",
                                                 "PIP_TARGET": "/foreign", "PLAYWRIGHT_BROWSERS_PATH": "/foreign"}):
            self.setup()
        for _, env, _ in self.calls:
            self.assertNotIn("PYTHONHOME", env)
            self.assertNotIn("PYTHONPATH", env)
            self.assertNotIn("PIP_TARGET", env)
            self.assertEqual(env["PLAYWRIGHT_BROWSERS_PATH"], str(self.skill / ".runtime/browsers"))

    def test_incomplete_skill_fails_without_side_effects(self):
        (self.skill / "scripts/browser.py").unlink()
        with self.assertRaises(setup_module.SetupError):
            self.setup()
        self.assertFalse((self.skill / ".runtime").exists())

    def test_runtime_symlink_does_not_follow_other_data(self):
        target = self.skill.parent / "other"
        target.mkdir()
        try:
            (self.skill / ".runtime").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit symlink creation")
        with self.assertRaises(setup_module.SetupError):
            self.setup()
        self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
