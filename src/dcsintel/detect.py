"""Detect the DCS World installation and enumerate owned content.

Search order for the install directory:

1. ``DCSINTEL_DCS_PATH`` environment variable
2. ``dcs_install`` key in a ``dcsintel.config.json`` (current directory,
   then ``~/.dcsintel/config.json``)
3. pydcs's registry lookup (standalone stable/openbeta keys, then Steam)
4. Standalone default paths under Program Files ("Eagle Dynamics/DCS World*")
5. Steam libraries (parses ``libraryfolders.vdf`` for ``DCSWorld``)

Owned flyable modules are inferred from ``<install>/Mods/aircraft/*`` folder
names via ``data/modules.json``; terrains from ``<install>/Mods/terrains/*``.
If no install is found, ownership falls back entirely to the config file,
which may list ``modules`` and ``terrains`` directly.

The result is cached in ``~/.dcsintel/detected.json`` so agent workflows
don't rescan on every mission. Pass ``refresh=True`` (CLI: ``--refresh``)
to force a rescan.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Optional

from .data import load_data

CACHE_PATH = Path.home() / ".dcsintel" / "detected.json"
USER_CONFIG_PATH = Path.home() / ".dcsintel" / "config.json"
LOCAL_CONFIG_NAME = "dcsintel.config.json"


def _read_config() -> dict:
    """Merge local (cwd) and user (~/.dcsintel) config files; local wins."""
    merged: dict = {}
    for path in (USER_CONFIG_PATH, Path.cwd() / LOCAL_CONFIG_NAME):
        if path.is_file():
            try:
                merged.update(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
    return merged


def _steam_library_paths() -> list[Path]:
    """Return all Steam library roots found via libraryfolders.vdf."""
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Steam",
    ]
    libraries: list[Path] = []
    for steam in candidates:
        vdf = steam / "steamapps" / "libraryfolders.vdf"
        if not vdf.is_file():
            continue
        libraries.append(steam)
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
            # "path"    "D:\\SteamLibrary"
            for m in re.finditer(r'"path"\s+"([^"]+)"', text):
                libraries.append(Path(m.group(1).replace("\\\\", "\\")))
        except OSError:
            pass
    return libraries


def find_dcs_install() -> Optional[Path]:
    """Locate the DCS World install directory, or None if not found."""
    env = os.environ.get("DCSINTEL_DCS_PATH")
    if env and Path(env).is_dir():
        return Path(env)

    cfg = _read_config()
    if cfg.get("dcs_install") and Path(cfg["dcs_install"]).is_dir():
        return Path(cfg["dcs_install"])

    # pydcs reads the Eagle Dynamics / Steam registry keys, which catch
    # installs on non-default drives that a filesystem scan would miss.
    try:
        from dcs.installation import get_dcs_install_directory

        registry_path = get_dcs_install_directory()
        if registry_path and Path(registry_path).is_dir():
            return Path(registry_path)
    except Exception:
        pass

    for pf_var in ("ProgramFiles", "ProgramFiles(x86)"):
        pf = Path(os.environ.get(pf_var, ""))
        ed = pf / "Eagle Dynamics"
        if ed.is_dir():
            for child in sorted(ed.iterdir()):
                if child.is_dir() and child.name.startswith("DCS World"):
                    return child

    for lib in _steam_library_paths():
        candidate = lib / "steamapps" / "common" / "DCSWorld"
        if candidate.is_dir():
            return candidate

    return None


def find_saved_games() -> Optional[Path]:
    """Locate the DCS Saved Games folder (release preferred over openbeta)."""
    saved = Path.home() / "Saved Games"
    for name in ("DCS", "DCS.release", "DCS.openbeta"):
        if (saved / name).is_dir():
            return saved / name
    return None


def _scan_modules(install: Path) -> tuple[list[str], list[str]]:
    """Return (flyable aircraft ids, unrecognized folder names)."""
    mapping = load_data("modules")
    flyable: set[str] = set(mapping["always_flyable"])
    unknown: list[str] = []
    aircraft_dir = install / "Mods" / "aircraft"
    if aircraft_dir.is_dir():
        for folder in aircraft_dir.iterdir():
            if not folder.is_dir():
                continue
            ids = mapping["folders"].get(folder.name)
            if ids:
                flyable.update(ids)
            else:
                unknown.append(folder.name)
    return sorted(flyable), sorted(unknown)


def _scan_terrains(install: Path) -> list[str]:
    """Return pydcs terrain names for installed terrain folders."""
    mapping = load_data("modules")["terrain_folders"]
    terrains: set[str] = set()
    terrain_dir = install / "Mods" / "terrains"
    if terrain_dir.is_dir():
        for folder in terrain_dir.iterdir():
            if folder.is_dir() and folder.name in mapping:
                terrains.add(mapping[folder.name])
    return sorted(terrains)


def detect(refresh: bool = False) -> dict:
    """Detect DCS install, owned modules, and terrains.

    Returns a dict with keys: ``dcs_install``, ``saved_games``, ``modules``,
    ``terrains``, ``unknown_module_folders``, ``source``, ``detected_at``.
    Results are cached; pass refresh=True to rescan.
    """
    if not refresh and CACHE_PATH.is_file():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    cfg = _read_config()
    install = find_dcs_install()
    saved_games = find_saved_games()

    if install is not None:
        modules, unknown = _scan_modules(install)
        terrains = _scan_terrains(install)
        source = "scan"
    else:
        modules, unknown = sorted(set(cfg.get("modules", []))), []
        terrains = sorted(set(cfg.get("terrains", [])))
        source = "config" if (modules or terrains) else "none"

    # Config can supplement a scan (e.g. modules installed elsewhere).
    modules = sorted(set(modules) | set(cfg.get("extra_modules", [])))
    terrains = sorted(set(terrains) | set(cfg.get("extra_terrains", [])))

    result = {
        "dcs_install": str(install) if install else None,
        "saved_games": str(saved_games) if saved_games else None,
        "modules": modules,
        "terrains": terrains,
        "unknown_module_folders": unknown,
        "source": source,
        "detected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
