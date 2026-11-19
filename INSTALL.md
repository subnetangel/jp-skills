# Install

Every skill here is one folder in the open [Agent Skills](https://agentskills.io/specification) format: a `SKILL.md`
with `name` and `description`, plus `scripts/`, `references/` and `assets/`. Any harness that reads that format can
load them. Each harness only needs the folders copied (or symlinked) into its skills directory.

```bash
git clone https://github.com/subnetangel/jp-skills.git && cd jp-skills
```

Install all of them the same way, so skills that work together find each other (`booth-talk-track` uses
`presentation-coach`'s talk-track builder from the folder next to it). Set `DEST` to your harness's skills folder
from the sections below, then:

```bash
mkdir -p "$DEST"
for s in skills/*/; do cp -r "$s" "$DEST/"; done
cp -r templates/demo-engine "$DEST/demo-engine/template"      # the demo-engine skill's template
```

Use `ln -s "$PWD/skills/<name>" "$DEST/<name>"` instead of `cp -r` if you want `git pull` to update them. Keep each
folder's name: the harnesses require it to match the skill's `name`.

**The persona.** `agents/bragi.md` is a plain system prompt for a presentation coach. Each section says where a
harness looks for one. It is optional: the skills work without it.

**Requirements.** Python 3.9+ for every default script. Node only for the optional browser checks (with Playwright)
and the optional DOM smoke test (with jsdom). No skill needs network access to run.

## Claude Code

```bash
DEST=~/.claude/skills            # every project; or .claude/skills inside one project
```

Claude Code loads skills from `~/.claude/skills/<name>/SKILL.md` and a project's `.claude/skills/`
([docs](https://code.claude.com/docs/en/skills)). Invoke one with `/presentation-coach`, or describe the task.
Persona as a subagent: save `agents/bragi.md` under `~/.claude/agents/bragi.md` with frontmatter
(`name: bragi`, `description: Presentation and communications coach`). Inside this repository, `CLAUDE.md`
imports `AGENTS.md`.

## OpenAI Codex CLI

```bash
DEST=~/.agents/skills            # every repository; or .agents/skills inside one
```

Codex reads skills from `~/.agents/skills` and from `.agents/skills` between your working directory and the
repository root ([docs](https://learn.chatgpt.com/docs/build-skills)). Mention one with `$presentation-coach` or run
`/skills`. Persona: append `agents/bragi.md` to `~/.codex/AGENTS.md`, or run Codex inside this repository, whose
`AGENTS.md` points to it.

## Cursor

```bash
DEST=~/.cursor/skills            # user level; or .cursor/skills (or .agents/skills) inside a project
```

Cursor loads skills from `.cursor/skills/`, `.agents/skills/` and their user-level versions, and also reads
`.claude/skills/` and `.codex/skills/` ([docs](https://cursor.com/docs/skills)). Type `/` in Agent chat to pick
one. Persona: add `agents/bragi.md` as a project rule or keep it in an `AGENTS.md`.

## Gemini CLI

```bash
DEST=~/.gemini/skills            # user level; or .gemini/skills (or .agents/skills) in a workspace
```

Gemini CLI discovers user skills in `~/.gemini/skills/` or `~/.agents/skills/` and workspace skills in
`.gemini/skills/` or `.agents/skills/` ([docs](https://geminicli.com/docs/cli/skills/)). Run `/skills list` to check,
and approve the consent prompt when a skill activates. `/skills link <path>` links a folder without copying.
Persona: put `agents/bragi.md` in your `GEMINI.md`.

## GitHub Copilot (VS Code, Copilot CLI)

```bash
DEST=~/.copilot/skills           # personal; or .github/skills inside a repository
```

Copilot in VS Code and the Copilot CLI read project skills from `.github/skills/` and personal skills from
`~/.copilot/skills/`; VS Code's local sessions also read `.claude/skills/` and `.agents/skills/`
([VS Code docs](https://code.visualstudio.com/docs/agent-customization/agent-skills),
[Copilot CLI docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills)).
Type `/` in chat to run one. Persona: save `agents/bragi.md` as a custom agent or in
`.github/copilot-instructions.md`.

## Kiro

```bash
DEST=~/.kiro/skills              # global; or .kiro/skills inside a workspace
```

Kiro loads workspace skills from `.kiro/skills/` and global skills from `~/.kiro/skills/`, and can import a skill
folder from a public GitHub URL in the Agent Steering & Skills panel ([docs](https://kiro.dev/docs/skills/)). Type
`/` to run one as a slash command. Persona: save `agents/bragi.md` as a steering file or a custom agent prompt.

## Any agent that reads AGENTS.md

Open the agent inside this repository. `AGENTS.md` tells it to act as the coach in `agents/bragi.md`, read the
relevant `skills/<name>/SKILL.md` first, and run the scripts from that folder. For an agent with no skills
support at all: load `agents/bragi.md` as the system prompt, give it read access to `skills/`, and tell it to read
the matching `SKILL.md` before it starts.

## Check the install

Ask: "Use the presentation-coach skill to build the Acme Ledger worked example's checks." The agent should find
`examples/acme-ledger/build.sh` and report `TIMING: … PASS`, `UNSOURCED: 0` and `OFFLINE: … PASS`. Or run
`python3 tools/check_repo.py` yourself.
