#!/usr/bin/env python3
"""Install the dcs-mission-generator skill into AI harness skill folders.

The canonical skill lives in this repo under ``skills/``. Harnesses discover
skills in their own directories, so this script copies it there:

    Harness          User scope                Project scope
    --------------   -----------------------   --------------------
    cursor           ~/.cursor/skills/         .cursor/skills/
    claude           ~/.claude/skills/         .claude/skills/
    copilot          (project only)            .github/skills/

Usage:
    python scripts/install_skills.py                  # all harnesses, user scope
    python scripts/install_skills.py --harness cursor
    python scripts/install_skills.py --scope project --project-dir path/to/repo

Re-running overwrites the installed copy, so run it again after pulling
skill updates.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SRC = REPO_ROOT / "skills" / "dcs-mission-generator"

HARNESS_DIRS = {
    "cursor": {"user": Path.home() / ".cursor" / "skills",
               "project": Path(".cursor") / "skills"},
    "claude": {"user": Path.home() / ".claude" / "skills",
               "project": Path(".claude") / "skills"},
    "copilot": {"user": None,  # Copilot discovers skills per-repository
                "project": Path(".github") / "skills"},
}


def install(harness: str, scope: str, project_dir: Path) -> Path | None:
    target_base = HARNESS_DIRS[harness][scope]
    if target_base is None:
        print(f"  {harness}: no {scope}-scope skill directory; use --scope project")
        return None
    if scope == "project":
        target_base = project_dir / target_base
    target = target_base / SKILL_SRC.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SRC, target, dirs_exist_ok=True)
    print(f"  {harness}: installed -> {target}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--harness", choices=[*HARNESS_DIRS, "all"], default="all")
    parser.add_argument("--scope", choices=["user", "project"], default="user",
                        help="user: available everywhere; project: committed with a repo")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(),
                        help="target repo root for --scope project (default: cwd)")
    args = parser.parse_args()

    if not SKILL_SRC.is_dir():
        print(f"error: skill source not found at {SKILL_SRC}", file=sys.stderr)
        return 1

    harnesses = list(HARNESS_DIRS) if args.harness == "all" else [args.harness]
    print(f"Installing skill from {SKILL_SRC} ({args.scope} scope):")
    for h in harnesses:
        install(h, args.scope, args.project_dir)
    print("\nDone. Restart your agent session so it picks up the new skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
