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

    def test_production_requires_the_planned_final_step(self):
        for last_step, expected in ((25, 1), (110, 0)):
            with self.subTest(last_step=last_step), TemporaryDirectory() as directory:
                run = Path(directory)
                (run / "provenance").mkdir()
                (run / "provenance/profile.txt").write_text("smoke\n")
                md = run / "md"
                md.mkdir()
                for filename in ("md.tpr", "md.cpt", "md.xtc", "md-processed.top"):
                    (md / filename).write_text("fixture\n")
                (md / "md-processed.mdp").write_text("nsteps = 100 ; increments\ninit-step = 10\n")
                (md / "md.log").write_text(f"  Step  Time\n  {last_step}  0.05000\nFinished mdrun\n")
                result = self.run_script("check_10.sh", directory)
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected:
                    self.assertIn("expected final step 110, found 25", result.stderr)

    def test_redocking_rejects_malformed_rmsd(self):
        for value, expected in (("unavailable", 1), ("", 1), ("-0.5", 1), ("0.350136", 0)):
            with self.subTest(value=value), TemporaryDirectory() as directory:
                run = Path(directory)
                for name in ("provenance", "logs", "dock"):
                    (run / name).mkdir()
                (run / "provenance/profile.txt").write_text("dock\n")
                (run / "logs/pose.log").write_text("identity and formal charge +1 match\n")
                (run / "dock/lig_pose.sdf").write_text("$$$$\n")
                (run / "dock/redocking.csv").write_bytes(f"rank,rmsd_A\r\n1,{value}\r\n".encode())
                result = self.run_script("check_05.sh", directory)
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_unrecognized_profile_fails(self):
        result = self.run_script("run_example.sh", "invalid")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
