"""dcsintel command-line interface.

Three subcommands, all emitting JSON on stdout so both humans and AI
agents can consume the output:

- ``dcsintel detect [--refresh]`` - find DCS, list owned modules/terrains
- ``dcsintel generate --type sead | --spec spec.json [options]`` - build a .miz
- ``dcsintel training --curriculum sead_viper [options]`` - F-16 training sortie
- ``dcsintel validate mission.miz`` - reload and sanity-check a .miz

Exit code 0 on success; 1 with a JSON ``{"error": ...}`` payload on failure.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# pydcs's livery scanner logs (harmless) parse errors for some stock livery
# files at import time. The CLI reports real failures via its JSON payload,
# so keep stray log noise out of agent-facing stdout/stderr.
logging.disable(logging.ERROR)


def _print(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


def cmd_detect(args: argparse.Namespace) -> int:
    from .detect import detect

    _print(detect(refresh=args.refresh))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from .builder import build_mission
    from .detect import detect
    from .spec import normalize

    if args.spec:
        raw = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        raw = {"type": args.type}

    # CLI flags override spec-file fields for quick one-liners.
    if args.type:
        raw["type"] = args.type
    if args.terrain:
        raw["terrain"] = args.terrain
    if args.seed is not None:
        raw["seed"] = args.seed
    if args.aircraft:
        raw.setdefault("player", {})["aircraft"] = args.aircraft

    ownership = None if args.no_ownership_check else detect()
    spec = normalize(raw, ownership)

    out_path = args.out
    if out_path is None and ownership and ownership.get("saved_games"):
        missions_dir = Path(ownership["saved_games"]) / "Missions"
        out_path = str(missions_dir / f"{spec['type']}_{spec['terrain']}_{spec['seed']}.miz")

    path = build_mission(spec, out_path)
    _print({
        "miz": str(path.resolve()),
        "type": spec["type"],
        "terrain": spec["terrain"],
        "aircraft": spec["player"]["aircraft"],
        "seed": spec["seed"],
        "briefing_objective": spec["briefing"]["objective"],
    })
    return 0


def cmd_training(args: argparse.Namespace) -> int:
    from .detect import detect
    from .difficulty import DIFFICULTY_TIERS
    from .training import build_training
    from .training_spec import normalize_training

    if args.spec:
        raw = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        raw = {}

    if args.curriculum:
        raw["curriculum"] = args.curriculum
    if args.difficulty:
        raw["difficulty"] = args.difficulty
    if args.terrain:
        raw["terrain"] = args.terrain
    if args.seed is not None:
        raw["seed"] = args.seed

    ownership = None if args.no_ownership_check else detect()
    spec = normalize_training(raw, ownership)

    out_path = args.out
    if out_path is None and ownership and ownership.get("saved_games"):
        diff = spec["difficulty"]
        missions_dir = Path(ownership["saved_games"]) / "Missions"
        out_path = str(
            missions_dir
            / f"training_{spec['curriculum']}_{diff}_{spec['terrain']}_{spec['seed']}.miz"
        )

    path = build_training(spec, out_path)
    _print({
        "miz": str(path.resolve()),
        "curriculum": spec["curriculum"],
        "difficulty": spec["difficulty"],
        "difficulty_label": spec["difficulty_profile"]["label"],
        "terrain": spec["terrain"],
        "aircraft": spec["aircraft"],
        "seed": spec["seed"],
        "briefing_objective": spec["briefing"]["objective"],
        "difficulty_tiers": list(DIFFICULTY_TIERS),
    })
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from .builder import validate_miz

    _print(validate_miz(args.miz))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dcsintel",
        description="Generate random DCS World missions (see README for the full guide).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_detect = sub.add_parser("detect", help="detect DCS install, owned modules and terrains")
    p_detect.add_argument("--refresh", action="store_true", help="ignore the cache and rescan")
    p_detect.set_defaults(func=cmd_detect)

    p_gen = sub.add_parser("generate", help="generate a .miz from a spec file or --type")
    p_gen.add_argument("--spec", help="path to a MissionSpec JSON file")
    p_gen.add_argument("--type", help="mission type (dogfight|cap|sead|strike|escort|cas|intercept)")
    p_gen.add_argument("--terrain", help="terrain name, e.g. Caucasus")
    p_gen.add_argument("--aircraft", help="player aircraft DCS type id, e.g. F-16C_50")
    p_gen.add_argument("--seed", type=int, help="random seed for reproducible missions")
    p_gen.add_argument("--out", help="output .miz path (default: Saved Games/DCS/Missions)")
    p_gen.add_argument(
        "--no-ownership-check", action="store_true",
        help="skip module/terrain ownership validation",
    )
    p_gen.set_defaults(func=cmd_generate)

    p_trn = sub.add_parser(
        "training",
        help="generate an F-16 scripted training mission (SEAD curriculum v1)",
    )
    p_trn.add_argument("--spec", help="path to a TrainingSpec JSON file")
    p_trn.add_argument(
        "--curriculum",
        default="sead_viper",
        help="training curriculum id (default: sead_viper)",
    )
    p_trn.add_argument(
        "--difficulty",
        choices=["training", "routine", "contested", "high_threat"],
        help="threat tier: training, routine, contested, or high_threat (default: routine)",
    )
    p_trn.add_argument("--terrain", help="terrain name, e.g. Caucasus")
    p_trn.add_argument("--seed", type=int, help="random seed for reproducible layout")
    p_trn.add_argument("--out", help="output .miz path (default: Saved Games/DCS/Missions)")
    p_trn.add_argument(
        "--no-ownership-check", action="store_true",
        help="skip module/terrain ownership validation",
    )
    p_trn.set_defaults(func=cmd_training)

    p_val = sub.add_parser("validate", help="reload a generated .miz and sanity-check it")
    p_val.add_argument("miz", help="path to the .miz file")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    if args.command == "generate" and not (args.spec or args.type):
        parser.error("generate requires --spec or --type")

    try:
        return args.func(args)
    except Exception as exc:  # agent-facing: always structured output
        _print({"error": f"{type(exc).__name__}: {exc}"})
        return 1


if __name__ == "__main__":
    sys.exit(main())
