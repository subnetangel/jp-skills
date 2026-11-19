#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Repository checks: skill format, instruction files in sync, shared script copies identical, licence headers.

Usage: python3 tools/check_repo.py      (from anywhere; exit 0 when every check passes)

  * Every skills/<name>/SKILL.md has YAML frontmatter with name (matching the folder; lowercase letters, digits and
    single hyphens; at most 64 characters), description (1 to 1024 characters) and license.
  * CLAUDE.md imports AGENTS.md, so Claude Code and AGENTS.md readers get the same instructions.
  * Files that are copied between skills on purpose (so each skill installs on its own) are byte-identical.
  * Every script (.py .js .mjs .sh) carries an SPDX-License-Identifier line, and every .py compiles.
Python 3.9+, standard library only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
COPIES = [
    ["skills/presentation-coach/scripts/offline_check.py", "skills/terminal-replay/scripts/offline_check.py",
     "skills/demo-cheat-sheet/scripts/offline_check.py", "skills/terminal-replay-demo/scripts/offline_check.py",
     "templates/demo-engine/offline_check.py"],
    ["skills/terminal-replay/assets/term-player.js", "templates/demo-engine/src/term-player.js"],
    ["skills/terminal-replay/assets/term-player.css", "templates/demo-engine/src/term-player.css"],
]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
fails = []


def front(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_-]+:", line):
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
        elif key and line.startswith(" "):
            out[key] += " " + line.strip()
    return out


for sk in sorted((ROOT / "skills").iterdir()):
    if not sk.is_dir():
        continue
    f = sk / "SKILL.md"
    if not f.is_file():
        fails.append(f"{sk.name}: no SKILL.md")
        continue
    fm = front(f.read_text(encoding="utf-8"))
    if fm is None:
        fails.append(f"{sk.name}: no frontmatter")
        continue
    name, desc = fm.get("name", ""), fm.get("description", "").strip("|> ").strip()
    if name != sk.name or not NAME.match(name) or len(name) > 64:
        fails.append(f"{sk.name}: name '{name}' must match the folder and the naming rule")
    if not 1 <= len(desc) <= 1024:
        fails.append(f"{sk.name}: description is {len(desc)} characters (1 to 1024)")
    if not fm.get("license"):
        fails.append(f"{sk.name}: no license field")
    print(f"skill {sk.name:<24} name ok={name == sk.name}  description {len(desc)} chars")

claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
if "@AGENTS.md" not in claude:
    fails.append("CLAUDE.md does not import @AGENTS.md")

for group in COPIES:
    blobs = {p: (ROOT / p).read_bytes() for p in group if (ROOT / p).is_file()}
    missing = [p for p in group if p not in blobs]
    if missing:
        fails.append(f"missing copies: {missing}")
    if len(set(blobs.values())) > 1:
        fails.append(f"copies differ: {group}")

scripts = [p for d in ("skills", "templates", "tools", "examples") for p in (ROOT / d).rglob("*")
           if p.suffix in (".py", ".js", ".mjs", ".sh") and "node_modules" not in p.parts]
for p in scripts:
    head = p.read_text(encoding="utf-8", errors="replace")[:600]
    if "SPDX-License-Identifier:" not in head:
        fails.append(f"no SPDX line: {p.relative_to(ROOT)}")
    if p.suffix == ".py":
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")   # syntax check, writes no .pyc
        except SyntaxError as e:
            fails.append(f"does not compile: {p.relative_to(ROOT)}: {e.msg}")
print(f"scripts checked: {len(scripts)}")
for f in fails:
    print("FAIL", f)
print("CHECK_REPO:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
