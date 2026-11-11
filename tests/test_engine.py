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

    def install(self, home, *args):
        env = {**self.env, "HOME": str(home)}
        for key in ("CLAUDE_SETTINGS", "CODEX_HOOKS", "ANTIGRAVITY_HOOKS", "ANTIGRAVITY_SKILLS_JSON"):
            env.pop(key, None)
        return subprocess.run(["bash", str(self.brain / "install.sh"), *args], capture_output=True, text=True, env=env)

    def test_install_all_agents_is_idempotent(self):
        home = self.tmp / "home"
        home.mkdir()
        for _ in range(2):
            self.assertEqual(self.install(home, "--agents", "all").returncode, 0)
        claude = json.loads((home / ".claude" / "settings.json").read_text())
        self.assertEqual({k: len(v) for k, v in claude["hooks"].items()},
                         {"SessionStart": 1, "SessionEnd": 1, "UserPromptSubmit": 1})
        codex = json.loads((home / ".codex" / "hooks.json").read_text())
        self.assertEqual({k: len(v) for k, v in codex["hooks"].items()},
                         {"SessionStart": 1, "UserPromptSubmit": 1, "SessionEnd": 1})
        self.assertIn("--agent codex", codex["hooks"]["SessionStart"][0]["hooks"][0]["command"])
        agy = json.loads((home / ".gemini" / "config" / "hooks.json").read_text())
        self.assertEqual(sorted(agy["cortex-md"]), ["PreInvocation", "SessionStart", "Stop"])
        skills = json.loads((home / ".gemini" / "config" / "skills.json").read_text())
        self.assertEqual(skills["entries"], [{"path": str(self.brain / "skills")}])
        for directory in (home / ".claude" / "skills", home / ".agents" / "skills"):
            self.assertTrue((directory / "memory-keeping" / "SKILL.md").exists())
        self.assertEqual(len(list((home / ".claude").glob("settings.json.bak-*"))), 0)

    def test_install_preserves_foreign_hooks_and_rejects_bad_json(self):
        home = self.tmp / "home"
        (home / ".claude").mkdir(parents=True)
        settings = home / ".claude" / "settings.json"
        settings.write_text(json.dumps({"theme": "dark", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}))
        self.assertEqual(self.install(home, "--agents", "claude").returncode, 0)
        data = json.loads(settings.read_text())
        self.assertEqual(data["theme"], "dark")
        self.assertIn("Stop", data["hooks"])
        self.assertEqual(len(list((home / ".claude").glob("settings.json.bak-*"))), 1)
        settings.write_text("{bad")
        result = self.install(home, "--agents", "claude")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not valid JSON", result.stderr)
        self.assertEqual(settings.read_text(), "{bad")

    def test_install_rejects_unknown_agent(self):
        result = self.install(self.tmp, "--agents", "nope")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown agent", result.stderr)

    def test_context_antigravity_format(self):
        out = subprocess.run([sys.executable, str(self.brain / "bin" / "context.py"), "--agent", "antigravity"],
                             capture_output=True, text=True, env=self.env).stdout
        data = json.loads(out)
        self.assertNotIn("hookSpecificOutput", data)
        self.assertIn("Open fronts", data["injectSteps"][0]["systemMessage"]["systemMessage"])

    def test_injection_antigravity_format(self):
        prompt = json.dumps({"lastUserInput": "explain the invoice tool sqlite storage choice", "conversationId": "c1"})
        data = json.loads(self.run_script("inject-memory.py", stdin=prompt).stdout)
        self.assertIn("project-invoice-tool-storage-choice", data["injectSteps"][0]["ephemeralMessage"])

    def test_session_end_light_commits_and_prints_json(self):
        subprocess.run(["git", "init", "-q"], cwd=self.brain, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], cwd=self.brain, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], cwd=self.brain, check=True)
        (self.brain / "PENDING.md").write_text("changed\n")
        env = {**self.env, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        out = subprocess.run(["bash", str(self.brain / "bin" / "session-end.sh"), "--light"], capture_output=True, text=True, env=env).stdout
        self.assertEqual(out.strip(), "{}")
        log = subprocess.run(["git", "log", "--format=%s"], cwd=self.brain, capture_output=True, text=True).stdout
        self.assertIn("Session of", log)


    def write_transcripts(self):
        home = self.tmp / "home"
        claude = self.tmp / "projects" / "-some-project"
        claude.mkdir(parents=True)
        (claude / "s1.jsonl").write_text(json.dumps({"type": "user", "message": {"content": "fix the nginx redirect loop"}}) + "\n")
        agy = home / ".gemini" / "antigravity-cli" / "brain" / "abc" / ".system_generated" / "logs"
        agy.mkdir(parents=True)
        (agy / "transcript_full.jsonl").write_text(
            json.dumps({"type": "SYSTEM_MESSAGE", "content": "hook text"}) + "\n"
            + json.dumps({"type": "USER_INPUT", "content": "<USER_REQUEST>\nrotate the backup disk\n</USER_REQUEST>\n<ADDITIONAL_METADATA>x</ADDITIONAL_METADATA>"}) + "\n")
        codex = home / ".codex" / "sessions" / "2026" / "11" / "11"
        codex.mkdir(parents=True)
        (codex / "rollout-1.jsonl").write_text(
            json.dumps({"type": "response_item", "payload": {"role": "user", "content": [{"type": "input_text", "text": "<environment_context>x"}]}}) + "\n"
            + json.dumps({"type": "response_item", "payload": {"role": "user", "content": [{"type": "input_text", "text": "upgrade the postgres container"}]}}) + "\n")
        return {**self.env, "HOME": str(home), "CLAUDE_PROJECTS_DIR": str(self.tmp / "projects"),
                "GEMINI_HOME": str(home / ".gemini"), "CODEX_HOME": str(home / ".codex")}

    def test_transcripts_cover_all_three_agents(self):
        env = self.write_transcripts()
        out = subprocess.run([sys.executable, str(self.brain / "bin" / "transcripts.py")], capture_output=True, text=True, env=env).stdout
        self.assertEqual(sorted(l.split("\t")[0] for l in out.splitlines()), ["antigravity", "claude", "codex"])
        count = subprocess.run([sys.executable, str(self.brain / "bin" / "transcripts.py"), "--count", "--agent", "codex"],
                               capture_output=True, text=True, env=env).stdout
        self.assertEqual(count.strip(), "1")

    def test_context_lists_conversations_from_every_agent(self):
        env = self.write_transcripts()
        out = json.loads(subprocess.run([sys.executable, str(self.brain / "bin" / "context.py")],
                                        capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL).stdout)
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("rotate the backup disk", text)
        self.assertIn("(antigravity)", text)

    def test_context_skips_the_current_conversation(self):
        env = self.write_transcripts()
        payload = json.dumps({"conversationId": "abc"})
        out = json.loads(subprocess.run([sys.executable, str(self.brain / "bin" / "context.py"), "--agent", "antigravity"],
                                        capture_output=True, text=True, env=env, input=payload).stdout)
        self.assertNotIn("rotate the backup disk", out["injectSteps"][0]["systemMessage"]["systemMessage"])


    def test_session_start_stdout_is_pure_json_with_remote_and_dirty_tree(self):
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.brain, check=True)
        subprocess.run([*git, "add", "-A"], cwd=self.brain, check=True)
        subprocess.run([*git, "commit", "-qm", "init"], cwd=self.brain, check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.brain, check=True)
        subprocess.run(["git", "push", "-q", "-u", "origin", "main"], cwd=self.brain, check=True)
        (self.brain / "PENDING.md").write_text("dirty\n")
        env = {**self.env, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        out = subprocess.run(["bash", str(self.brain / "bin" / "session-start.sh")], capture_output=True, text=True,
                             env=env, stdin=subprocess.DEVNULL).stdout
        self.assertIn("hookSpecificOutput", json.loads(out))


if __name__ == "__main__":
    unittest.main()
