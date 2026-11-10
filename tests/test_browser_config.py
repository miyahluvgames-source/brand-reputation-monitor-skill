import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("monitor_config_test", ROOT / "skill/scripts/browser_config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class BrowserConfigTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.skill = self.root / "skill"
        self.runtime = self.skill / ".runtime"
        self.runtime.mkdir(parents=True)

    def test_missing_config_uses_os_defaults_without_writes(self):
        result = config.resolve_defaults(self.skill)
        self.assertEqual(result["state_dir"], str(config.default_state_dir().absolute()))
        self.assertEqual(result["profile"], "default")
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_selected_state_and_profile_survive_new_invocations(self):
        selected = config.save_defaults(self.skill, self.root / "private", "brand-one")
        self.assertEqual(config.resolve_defaults(self.skill), selected)
        self.assertEqual(set(json.loads((self.runtime / "browser-config.json").read_text())), {"state_dir", "profile", "browser_channel"})

    def test_explicit_arguments_override_only_the_selected_fields_without_saving(self):
        saved = config.save_defaults(self.skill, self.root / "private", "brand-one")
        result = config.resolve_defaults(self.skill, profile="brand-two")
        self.assertEqual(result["state_dir"], saved["state_dir"])
        self.assertEqual(result["profile"], "brand-two")
        result = config.resolve_defaults(self.skill, state_dir=self.root / "alternate")
        self.assertEqual(result["state_dir"], str(self.root / "alternate"))
        self.assertEqual(result["profile"], "brand-one")
        self.assertEqual(config.load_defaults(self.skill), saved)

    def test_invalid_saved_configuration_never_silently_changes_profiles(self):
        path = self.runtime / "browser-config.json"
        values = ["[]", "{}", "not-json", '{"state_dir":"relative","profile":"default"}',
                  json.dumps({"state_dir": str(self.root), "profile": "../personal"}),
                  json.dumps({"state_dir": str(self.root), "profile": "default", "cookie": "no"}),
                  json.dumps({"state_dir": str(self.root), "profile": "default", "browser_channel": []})]
        for value in values:
            path.write_text(value, encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(ValueError):
                config.resolve_defaults(self.skill)

    def test_symlink_configuration_cannot_redirect_to_other_data(self):
        external = self.root / "other.json"
        external.write_text(json.dumps({"state_dir": str(self.root), "profile": "default"}), encoding="utf-8")
        try:
            (self.runtime / "browser-config.json").symlink_to(external)
        except OSError:
            self.skipTest("Host does not permit symlink creation")
        with self.assertRaises(ValueError):
            config.resolve_defaults(self.skill)
        with self.assertRaises(ValueError):
            config.save_defaults(self.skill, self.root / "new", "new")

    def test_legacy_configuration_keeps_its_chromium_selection(self):
        path = self.runtime / "browser-config.json"
        path.write_text(json.dumps({"state_dir": str(self.root / "private"), "profile": "legacy"}), encoding="utf-8")
        with patch.object(config, "chrome_executable", return_value=self.root / "chrome"):
            self.assertEqual(config.resolve_defaults(self.skill)["browser_channel"], "chromium")
            self.assertEqual(config.resolve_defaults(self.skill, browser_channel="auto")["browser_channel"], "chrome")
        self.assertNotIn("browser_channel", json.loads(path.read_text()))

    def test_auto_uses_only_executable_presence_and_explicit_channel_is_preserved(self):
        with patch.object(config, "chrome_executable", return_value=None):
            self.assertEqual(config.resolve_defaults(self.skill)["browser_channel"], "chromium")
            self.assertEqual(config.resolve_defaults(self.skill, browser_channel="chrome")["browser_channel"], "chrome")
        with patch.object(config, "chrome_executable", return_value=self.root / "chrome"):
            self.assertEqual(config.resolve_defaults(self.skill)["browser_channel"], "chrome")
            self.assertEqual(config.resolve_defaults(self.skill, browser_channel="chromium")["browser_channel"], "chromium")


if __name__ == "__main__":
    unittest.main()
