import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install_skill.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text("---\nname: demo\ndescription: Fixture\n---\n")
        (self.source / "references").mkdir()
        (self.source / "references/policy.md").write_text("Never invent evidence.")

    def test_install_readback_and_no_overwrite(self):
        destination = self.root / "nested/destination"
        result = installer.install(self.source, destination)
        self.assertEqual(result["status"], "installed")
        self.assertEqual(result["files_verified"], 2)
        self.assertTrue(result["sha256_verified"])
        (destination / "SKILL.md").write_text("User customization")
        with self.assertRaises(FileExistsError):
            installer.install(self.source, destination)
        self.assertEqual((destination / "SKILL.md").read_text(), "User customization")

    def test_existing_file_is_never_replaced(self):
        destination = self.root / "destination"
        destination.write_text("Keep this")
        with self.assertRaises(FileExistsError):
            installer.install(self.source, destination)
        self.assertEqual(destination.read_text(), "Keep this")

    def test_missing_skill_fails_before_destination_creation(self):
        (self.source / "SKILL.md").unlink()
        destination = self.root / "missing"
        with self.assertRaises(ValueError):
            installer.install(self.source, destination)
        self.assertFalse(destination.exists())

    def make_symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError:
            self.skipTest("Host does not permit symlink creation")

    def test_dangling_destination_symlink_rejected(self):
        destination = self.root / "link"
        self.make_symlink(destination, self.root / "absent", directory=True)
        with self.assertRaises(FileExistsError):
            installer.install(self.source, destination)
        self.assertTrue(destination.is_symlink())

    def test_source_symlink_rejected(self):
        self.make_symlink(self.source / "secret", self.root / "absent")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.root / "destination")
        self.assertFalse((self.root / "destination").exists())

    def add_setup(self):
        (self.source / "scripts").mkdir()
        (self.source / "scripts/setup.py").write_text("# fixture\n")

    def test_default_install_prepares_browser_and_keeps_resume_command(self):
        self.add_setup()
        destination = self.root / "destination"
        response = subprocess.CompletedProcess([], 0, json.dumps({"status": "ready", "login_status": "not_checked"}))
        with patch.object(installer.subprocess, "run", return_value=response) as run:
            result = installer.install_and_setup(self.source, destination)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["login_status"], "not_checked")
        self.assertEqual(run.call_args.args[0][1], str(destination / "scripts/setup.py"))

    def test_skill_only_never_downloads_or_starts_browser(self):
        self.add_setup()
        with patch.object(installer.subprocess, "run") as run:
            result = installer.install_and_setup(self.source, self.root / "destination", skill_only=True)
        run.assert_not_called()
        self.assertEqual(result["status"], "skill_installed")
        self.assertEqual(result["browser_status"], "setup_required")
        self.assertTrue(Path(result["setup_argv"][1]).is_file())

    def test_failed_or_unreadable_setup_never_claims_ready(self):
        self.add_setup()
        for index, response in enumerate((subprocess.CompletedProcess([], 1, '{"status":"setup_failed"}'),
                                          subprocess.CompletedProcess([], 0, 'not-json'),
                                          subprocess.CompletedProcess([], 1, '{"status":"ready"}'))):
            with self.subTest(index=index), patch.object(installer.subprocess, "run", return_value=response):
                destination = self.root / ("destination-" + str(index))
                result = installer.install_and_setup(self.source, destination)
                self.assertEqual(result["status"], "setup_failed")
                self.assertTrue((destination / "SKILL.md").exists())
                self.assertTrue(result["setup_argv"])

    def test_reinstall_from_used_skill_excludes_runtime_and_bytecode(self):
        (self.source / ".runtime").mkdir()
        (self.source / ".runtime/private-data").write_text("never copy")
        (self.source / "__pycache__").mkdir()
        (self.source / "__pycache__/old.pyc").write_bytes(b"generated")
        destination = self.root / "destination"
        result = installer.install(self.source, destination)
        self.assertEqual(result["files_verified"], 2)
        self.assertFalse((destination / ".runtime").exists())
        self.assertFalse((destination / "__pycache__").exists())

    def test_setup_launch_error_keeps_original_install_and_resume(self):
        self.add_setup()
        destination = self.root / "destination"
        with patch.object(installer.subprocess, "run", side_effect=OSError("fixture launch failure")):
            result = installer.install_and_setup(self.source, destination)
        self.assertEqual(result["status"], "setup_failed")
        self.assertEqual(result["browser_status"], "setup_required")
        self.assertTrue(Path(result["setup_argv"][1]).is_file())

    def test_destination_inside_source_fails_before_creating_destination(self):
        destination = self.source / "nested/install"
        with self.assertRaises(ValueError):
            installer.install(self.source, destination)
        self.assertFalse((self.source / "nested").exists())

    def test_symlink_parent_into_source_cannot_hide_recursive_destination(self):
        alias = self.root / "alias"
        self.make_symlink(alias, self.source, directory=True)
        with self.assertRaises(ValueError):
            installer.install(self.source, alias / "destination")
        self.assertFalse((self.source / "destination").exists())

    def test_omitted_install_profile_stays_omitted_for_saved_configuration(self):
        self.add_setup()
        result = installer.install_and_setup(self.source, self.root / "destination", skill_only=True)
        self.assertNotIn("--profile", result["setup_argv"])
        self.assertNotIn("--state-dir", result["setup_argv"])


if __name__ == "__main__":
    unittest.main()
