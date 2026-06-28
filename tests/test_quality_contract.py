import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class QualityContractTests(unittest.TestCase):
    def test_ci_workflow_runs_required_phase5_checks(self):
        workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

        content = workflow.read_text(encoding="utf-8")

        self.assertIn("python -m pip install -e .", content)
        self.assertIn("python -m awa05.config", content)
        self.assertIn("python -m unittest discover -s tests -v", content)
        self.assertIn("python -m compileall -q awa05 scripts tests", content)
        self.assertIn("AWA05_DRY_RUN=true python -m awa05.upload.github", content)
        self.assertIn("git diff --check", content)

    def test_makefile_exposes_repeatable_local_commands(self):
        makefile = PROJECT_ROOT / "Makefile"

        content = makefile.read_text(encoding="utf-8")

        self.assertIn("check: config test compile upload-dry-run diff-check", content)
        self.assertIn("lint: compile diff-check", content)
        self.assertIn("run-simulation:", content)


if __name__ == "__main__":
    unittest.main()
