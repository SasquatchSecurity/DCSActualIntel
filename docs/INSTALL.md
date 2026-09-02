# Installation

You need **Python 3.10 or newer** (3.13 is fine) and **Git**. A DCS World install on the same PC makes module detection automatic; you can also list modules by hand — see [detection without DCS](#no-dcs-on-this-machine) below.

## Full setup (CLI + agent skill)

```bash
git clone https://github.com/SasquatchSecurity/DCSActualIntel.git
cd DCSActualIntel
pip install .
```

Use a virtual environment if you like:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate
pip install .
```

That installs the `dcsintel` command and pulls **[pydcs](https://github.com/pydcs/dcs)** from the commit pinned in `pyproject.toml`. Do not `pip install pydcs` separately unless you know you need a different version.

### Agent skill

The skill teaches Cursor, Claude Code, Copilot, and other [Agent Skills](https://agentskills.io) hosts how to run `dcsintel` and write specs:

```bash
python scripts/install_skills.py                    # all supported harnesses
python scripts/install_skills.py --harness cursor   # Cursor only
python scripts/install_skills.py --harness claude   # Claude Code only
python scripts/install_skills.py --scope project    # copy into this repo
```

| Harness | User install path | Project install path |
|---|---|---|
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| GitHub Copilot | — | `.github/skills/` |

Restart the agent session after install. Then ask for a mission in plain language.

### Updates

```bash
git pull
pip install .
python scripts/install_skills.py
```

The install script overwrites the copied skill files.

## CLI only (no clone)

```bash
pip install git+https://github.com/SasquatchSecurity/DCSActualIntel.git
```

You get `dcsintel` but not the skill folder. Clone the repo if you want doctrine docs or `install_skills.py`.

## Verify

```bash
dcsintel detect
dcsintel generate --type cap --no-ownership-check --out test_cap.miz
dcsintel validate test_cap.miz
```

`detect` prints JSON with owned modules and terrains. See [Usage](USAGE.md) for what to do when detection fails.

## No DCS on this machine

Mission **generation** works without DCS installed (useful on a laptop or in CI). Detection falls back to a config file.

Create `dcsintel.config.json` in the working directory, or `~/.dcsintel/config.json`:

```json
{
  "modules": ["F-16C_50", "FA-18C_hornet", "Su-25T"],
  "terrains": ["Caucasus", "Syria"]
}
```

Optional keys: `"dcs_install"`, `"extra_modules"`, `"extra_terrains"` to point at a non-standard install or add modules the scanner missed.

Set `DCSINTEL_DCS_PATH` to the DCS root if auto-discovery picks the wrong folder.

## Troubleshooting

**`pip install pydcs` / import crashes on Python 3.13**  
PyPI pydcs 0.15.0 breaks under 3.13. Install *this* package only; it pins a fixed pydcs commit from GitHub.

**`no owned modules detected`**  
Run `dcsintel detect --refresh`. If the install path is unusual, set `DCSINTEL_DCS_PATH` or use `dcsintel.config.json`.

**Bought a module but detect is stale**  
Cache lives at `~/.dcsintel/detected.json`. Run `dcsintel detect --refresh`.

**`unknown_module_folders` in detect output**  
A mod folder is not mapped yet. Add it to `src/dcsintel/data/modules.json` and open a PR.

Next: [Usage](USAGE.md) · [FAQ](FAQ.md)
