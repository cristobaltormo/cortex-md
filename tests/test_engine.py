import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Brain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.brain = self.tmp / "brain"
        shutil.copytree(ROOT, self.brain, ignore=shutil.ignore_patterns(".git", "__pycache__", "state"))
        self.env = {**os.environ, "BRAIN_STALE_DAYS": "100000", "BRAIN_DIR": str(self.brain), "CLAUDE_PROJECTS_DIR": str(self.tmp / "projects")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_script(self, name, stdin=None):
        return subprocess.run(
            [sys.executable, str(self.brain / "bin" / name), *([] if stdin is not None else [])],
            input=stdin, capture_output=True, text=True, env=self.env,
        )

    def health(self, *args):
        return subprocess.run(
            [sys.executable, str(self.brain / "bin" / "health.py"), *args],
            capture_output=True, text=True, env=self.env,
        ).stdout

    def test_example_brain_is_healthy(self):
        self.assertIn("Brain healthy", self.health())

    def test_orphan_note_is_reported(self):
        (self.brain / "memory" / "orphan.md").write_text(
            "---\nname: orphan\ndescription: x\nmetadata:\n  verified: 2099-01-01\n---\n\nSee [[preferences-communication]].\n"
        )
        self.assertIn("orphan.md is not reachable", self.health("--brief"))

    def test_broken_link_and_secret_are_reported(self):
        note = self.brain / "memory" / "preferences-communication.md"
        note.write_text(note.read_text() + "\nSee [[missing-note]]. password: hunter2hunter2\n")
        out = self.health("--brief")
        self.assertIn("missing-note", out)
        self.assertIn("password", out)

    def test_dead_entity_is_reported(self):
        note = self.brain / "memory" / "project-invoice-tool-storage-choice.md"
        note.write_text(note.read_text().replace("status: current\n", "status: current\n  entities: invoice-web\n", 1))
        (self.brain / "inventory" / "state.json").write_text(json.dumps({"containers": {"other": {}}}))
        self.assertIn("invoice-web", self.health("--brief"))
        (self.brain / "inventory" / "state.json").write_text(json.dumps({"containers": {"invoice-web": {}}}))
        self.assertNotIn("invoice-web", self.health("--brief"))

    def test_injection_suggests_matching_notes(self):
        prompt = json.dumps({"prompt": "why does the invoice tool use sqlite storage and spindown disks"})
        out = self.run_script("inject-memory.py", stdin=prompt).stdout
        self.assertIn("project-invoice-tool-storage-choice", out)

    def test_injection_is_silent_without_match(self):
        out = self.run_script("inject-memory.py", stdin=json.dumps({"prompt": "zzzzzzzz qqqqqqqq"})).stdout
        self.assertEqual(out.strip(), "")

    def test_context_runs_and_reports_pending(self):
        out = self.run_script("context.py").stdout
        self.assertIn("Open fronts", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_changes_detects_new_container(self):
        (self.brain / "state").mkdir(exist_ok=True)
        old = {"generated": "2026-01-01T00:00:00", "containers": {"a": {"kind": "docker", "state": "running"}}}
        new = {"generated": "2026-01-02T00:00:00", "containers": {
            "a": {"kind": "docker", "state": "running"}, "b": {"kind": "docker", "state": "running"}}}
        (self.brain / "state" / "previous-state.json").write_text(json.dumps(old))
        (self.brain / "inventory" / "state.json").write_text(json.dumps(new))
        self.run_script("changes.py")
        self.assertIn("container b (docker) is new", (self.brain / "inventory" / "CHANGES.md").read_text())

    def test_injection_with_single_matching_note(self):
        prompt = json.dumps({"prompt": "explain the invoice tool sqlite storage choice"})
        self.assertIn("project-invoice-tool-storage-choice", self.run_script("inject-memory.py", stdin=prompt).stdout)

    def test_parked_items_without_bold_are_listed(self):
        pending = self.brain / "PENDING.md"
        pending.write_text(pending.read_text() + "- plain parked item\n")
        out = json.loads(self.run_script("context.py").stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("plain parked item", out)

    def test_env_loader_accepts_unquoted_header(self):
        (self.brain / ".env").write_text("NOTIFY_AUTH_HEADER=Authorization: Bearer abc\nCURATOR_MODEL='opus'\n")
        out = subprocess.run(
            ["bash", "-c", f'BRAIN="{self.brain}"; . "{self.brain}/bin/load-env.sh"; echo "$NOTIFY_AUTH_HEADER|$CURATOR_MODEL"'],
            capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(out, "Authorization: Bearer abc|opus")

    def test_install_is_idempotent_and_rejects_bad_json(self):
        settings = self.tmp / "settings.json"
        env = {**self.env, "CLAUDE_SETTINGS": str(settings)}
        for _ in range(2):
            subprocess.run(["bash", str(self.brain / "install.sh")], capture_output=True, text=True, env=env)
        data = json.loads(settings.read_text())
        self.assertEqual({k: len(v) for k, v in data["hooks"].items()},
                         {"SessionStart": 1, "SessionEnd": 1, "UserPromptSubmit": 1})
        self.assertEqual(len(list(self.tmp.glob("settings.json.bak-*"))), 1)
        settings.write_text("{bad")
        result = subprocess.run(["bash", str(self.brain / "install.sh")], capture_output=True, text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not valid JSON", result.stderr)
        self.assertEqual(settings.read_text(), "{bad")


if __name__ == "__main__":
    unittest.main()
