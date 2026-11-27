import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class EntryPointTests(unittest.TestCase):
    def run_script(self, path, *args):
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / path), *args],
            cwd=ROOT, text=True, capture_output=True,
        )

    def test_dry_run_never_creates_run_directory(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "unused"
            result = self.run_script("run_example.sh", "--dry-run", "smoke", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_missing_output_cannot_pass_checkpoint(self):
        with TemporaryDirectory() as directory:
            result = self.run_script("check_05.sh", directory)
            self.assertNotEqual(result.returncode, 0)

    def test_unrecognized_profile_fails(self):
        result = self.run_script("run_example.sh", "invalid")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
