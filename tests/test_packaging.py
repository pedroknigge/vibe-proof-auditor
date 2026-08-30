"""Version, fixture, and native AGY installation contracts."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.sh"
DEMO = ROOT / "evals" / "fixtures" / "skill-docs"


def run_installer(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    bindir = home / "bin"
    bindir.mkdir(exist_ok=True)
    agy = bindir / "agy"
    agy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    agy.chmod(0o755)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(INSTALL), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class VersionSyncTests(unittest.TestCase):
    def test_version_surfaces_agree(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "0.9.0")
        self.assertIn(
            f'version: "{version}"', (ROOT / "SKILL.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            f'VERSION = "{version}"',
            (ROOT / "vibe_proof_auditor" / "scorelib.py").read_text(encoding="utf-8"),
        )
        self.assertIn(
            f"## {version}", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            f"Pre-1.0 (`{version}`)", (ROOT / "README.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            f"**Skill version:** {version}",
            (ROOT / "references" / "example-report.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            f'version: "{version}"', (DEMO / "SKILL.md").read_text(encoding="utf-8")
        )
        self.assertEqual(
            (DEMO / "VERSION").read_text(encoding="utf-8").strip(), version
        )
        self.assertIn(
            f"# Demo skill (v{version})",
            (DEMO / "SKILL.md").read_text(encoding="utf-8"),
        )

    def test_demo_fixture_remains_runnable_and_testless(self) -> None:
        expected = json.loads(
            (ROOT / "evals" / "expected" / "skill-docs.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue((DEMO / "scripts" / "run.py").is_file())
        self.assertFalse((DEMO / "tests").exists())
        self.assertEqual(expected["must_fail_gates"], ["testing"])
        self.assertEqual(
            expected["must_find"],
            [{"id": "no-tests", "path_substr": "scripts/run.py", "mark": "Fail"}],
        )


class InstallScriptTests(unittest.TestCase):
    def test_global_install_and_uninstall_materialize_direct_agy_demo(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibe-proof-install-") as tmp:
            home = Path(tmp)
            proc = run_installer(home, "--global")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            auditor_dests = [
                home / ".agents" / "skills" / "vibe-proof-auditor",
                home / ".gemini" / "config" / "skills" / "vibe-proof-auditor",
                home / ".gemini" / "antigravity-cli" / "skills" / "vibe-proof-auditor",
            ]
            demo_dests = [
                home / ".gemini" / "config" / "skills" / "demo-skill",
                home / ".gemini" / "antigravity-cli" / "skills" / "demo-skill",
            ]
            for dest in auditor_dests:
                self.assertTrue((dest / "SKILL.md").is_file(), dest)
            for dest in demo_dests:
                self.assertEqual(
                    (dest / "SKILL.md").read_text(encoding="utf-8"),
                    (DEMO / "SKILL.md").read_text(encoding="utf-8"),
                )
                self.assertTrue((dest / "scripts" / "run.py").is_file(), dest)
                self.assertEqual(
                    (dest / "VERSION").read_text(encoding="utf-8").strip(), "0.9.0"
                )
                self.assertFalse((dest / "tests").exists(), dest)
            self.assertFalse((home / ".agents" / "skills" / "demo-skill").exists())
            self.assertFalse((home / ".agy").exists())

            proc = run_installer(home, "--global", "--uninstall")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for dest in [*auditor_dests, *demo_dests]:
                self.assertFalse(dest.exists(), dest)


if __name__ == "__main__":
    unittest.main()
