#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

HOME = Path.home()
GROUP = "cortex-md"


def fail(message):
    print(f"install-hooks: {message}", file=sys.stderr)
    sys.exit(1)


def paths():
    return {
        "claude_settings": Path(os.environ.get("CLAUDE_SETTINGS", HOME / ".claude" / "settings.json")),
        "claude_skills": Path(os.environ.get("CLAUDE_SKILLS_DIR", HOME / ".claude" / "skills")),
        "codex_hooks": Path(os.environ.get("CODEX_HOOKS", HOME / ".codex" / "hooks.json")),
        "codex_config": Path(os.environ.get("CODEX_CONFIG", HOME / ".codex" / "config.toml")),
        "agents_skills": Path(os.environ.get("AGENTS_SKILLS_DIR", HOME / ".agents" / "skills")),
        "agy_hooks": Path(os.environ.get("ANTIGRAVITY_HOOKS", HOME / ".gemini" / "config" / "hooks.json")),
        "agy_skills": Path(os.environ.get("ANTIGRAVITY_SKILLS_JSON", HOME / ".gemini" / "config" / "skills.json")),
    }


def detect():
    found = []
    if (HOME / ".claude").exists() or shutil.which("claude"):
        found.append("claude")
    if (HOME / ".codex").exists() or shutil.which("codex"):
        found.append("codex")
    if (HOME / ".gemini").exists() or shutil.which("antigravity") or shutil.which("agy"):
        found.append("antigravity")
    return found


def load(path, kind):
    if not path.exists():
        return kind()
    try:
        data = json.loads(path.read_text() or "null")
    except ValueError as error:
        fail(f"{path} is not valid JSON ({error}); fix it and run again, nothing was changed")
    if data is None:
        return kind()
    if not isinstance(data, kind):
        fail(f"{path} must contain a JSON {kind.__name__}; nothing was changed")
    return data


def save(path, data, before):
    if json.dumps(data, sort_keys=True) == before:
        print(f"{path}: already up to date")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(path, backup)
        print(f"{path}: updated (backup: {backup.name})")
    else:
        print(f"{path}: created")
    path.write_text(json.dumps(data, indent=2) + "\n")


def command(brain, script, *args):
    return " ".join([shlex.quote(str(brain / "bin" / script)), *args])


def merge_groups(hooks, event, group):
    existing = hooks.setdefault(event, [])
    if not isinstance(existing, list):
        fail(f"hooks.{event} must be a list; nothing was changed")
    wanted = {h["command"] for h in group["hooks"]}
    known = {h.get("command") for g in existing if isinstance(g, dict) for h in g.get("hooks", [])}
    if not wanted <= known:
        existing.append(group)


def install_claude(brain, p):
    data = load(p["claude_settings"], dict)
    before = json.dumps(data, sort_keys=True)
    hooks = data.get("hooks")
    if hooks is None:
        hooks = data["hooks"] = {}
    if not isinstance(hooks, dict):
        fail("'hooks' in Claude Code settings must be an object; nothing was changed")
    for event, script, timeout in (
        ("SessionStart", "session-start.sh", 30),
        ("SessionEnd", "session-end.sh", 30),
        ("UserPromptSubmit", "inject-memory.py", 10),
    ):
        merge_groups(hooks, event, {"hooks": [{"type": "command", "command": command(brain, script), "timeout": timeout}]})
    wanted = str(brain / "memory")
    if data.get("autoMemoryDirectory") and data["autoMemoryDirectory"] != wanted:
        print(f"warning: autoMemoryDirectory was {data['autoMemoryDirectory']}; replacing it with {wanted}")
    data["autoMemoryDirectory"] = wanted
    save(p["claude_settings"], data, before)
    link_skills(brain, p["claude_skills"])


def install_codex(brain, p):
    config = p["codex_config"]
    if config.exists() and any(l.strip().startswith(("[hooks", "[[hooks")) for l in config.read_text().splitlines()):
        print(f"warning: {config} defines inline hooks; Codex uses one representation per layer, so cortex-md hooks in "
              f"{p['codex_hooks']} may be ignored. Move them there or add the cortex-md entries to the TOML by hand.")
    data = load(p["codex_hooks"], dict)
    before = json.dumps(data, sort_keys=True)
    hooks = data.get("hooks")
    if hooks is None:
        hooks = data["hooks"] = {}
    if not isinstance(hooks, dict):
        fail("'hooks' in the Codex hooks file must be an object; nothing was changed")
    for event, script, args, timeout in (
        ("SessionStart", "session-start.sh", ("--agent", "codex"), 30),
        ("UserPromptSubmit", "inject-memory.py", (), 10),
        ("SessionEnd", "session-end.sh", ("--light",), 3),
    ):
        group = {"hooks": [{"type": "command", "command": command(brain, script, *args), "timeout": timeout}]}
        if event == "SessionStart":
            group["matcher"] = "startup|resume"
        merge_groups(hooks, event, group)
    save(p["codex_hooks"], data, before)
    link_skills(brain, p["agents_skills"])
    print("Codex: run /hooks once in the CLI to review and trust the new hooks.")


def install_antigravity(brain, p):
    data = load(p["agy_hooks"], dict)
    before = json.dumps(data, sort_keys=True)
    data[GROUP] = {
        "SessionStart": [{"type": "command", "command": command(brain, "session-start.sh", "--agent", "antigravity"), "timeout": 30}],
        "PreInvocation": [{"type": "command", "command": command(brain, "inject-memory.py"), "timeout": 10}],
        "Stop": [{"type": "command", "command": command(brain, "session-end.sh", "--light"), "timeout": 30}],
    }
    save(p["agy_hooks"], data, before)

    skills = load(p["agy_skills"], dict)
    before = json.dumps(skills, sort_keys=True)
    entries = skills.setdefault("entries", [])
    target = str(brain / "skills")
    if not any(isinstance(e, dict) and e.get("path") == target for e in entries):
        entries.append({"path": target})
    save(p["agy_skills"], skills, before)


def link_skills(brain, target_dir):
    source = brain / "skills"
    if not source.is_dir():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for skill in sorted(source.iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        link = target_dir / skill.name
        if link.is_symlink() and Path(os.readlink(link)) == skill:
            continue
        if link.exists() or link.is_symlink():
            print(f"warning: {link} already exists and was left alone")
            continue
        link.symlink_to(skill)
        print(f"{link}: linked")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brain", required=True)
    parser.add_argument("--agents", default="auto", help="comma list of claude, codex, antigravity; or auto, all")
    args = parser.parse_args()
    brain = Path(args.brain).resolve()
    p = paths()
    known = ["claude", "codex", "antigravity"]
    if args.agents == "auto":
        agents = detect() or ["claude"]
    elif args.agents == "all":
        agents = known
    else:
        agents = [a.strip() for a in args.agents.split(",") if a.strip()]
        unknown = [a for a in agents if a not in known]
        if unknown:
            fail(f"unknown agent(s): {', '.join(unknown)}; choose from {', '.join(known)}")
    print(f"Installing for: {', '.join(agents)}")
    installers = {"claude": install_claude, "codex": install_codex, "antigravity": install_antigravity}
    for agent in agents:
        installers[agent](brain, p)


if __name__ == "__main__":
    main()
