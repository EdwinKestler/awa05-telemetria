import unittest
import subprocess
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

    def test_generated_data_is_ignored_on_main(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("data/raw/*.csv", gitignore)
        self.assertIn("data/processed/", gitignore)

    def test_generated_data_is_not_tracked_on_main(self):
        inside_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
        )
        if inside_git.returncode != 0:
            self.skipTest("not a git checkout")

        result = subprocess.run(
            ["git", "ls-files", "data"],
            cwd=PROJECT_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.stdout.strip(), "")

    def test_dashboards_fetch_from_data_branch_first(self):
        data_branch_url = (
            "https://raw.githubusercontent.com/"
            "geograficaaala/awa05-telemetria/data/data/processed/"
        )
        dashboards = [
            PROJECT_ROOT / "index.html",
            PROJECT_ROOT / "dashboard.html",
            PROJECT_ROOT / "analisis-estadistico.html",
        ]

        for dashboard in dashboards:
            with self.subTest(dashboard=dashboard.name):
                content = dashboard.read_text(encoding="utf-8")
                self.assertIn(data_branch_url, content)


if __name__ == "__main__":
    unittest.main()
