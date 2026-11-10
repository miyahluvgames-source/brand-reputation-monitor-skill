import importlib.util
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
