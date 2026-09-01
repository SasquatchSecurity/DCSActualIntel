"""JSON data catalogs (unit types, module folder mappings).

Loaded via :func:`load_data`. Kept as JSON so contributors can add
units, modules, and terrains without touching any logic.
"""

import json
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_data(name: str) -> dict:
    """Load a bundled JSON catalog by bare name, e.g. ``load_data("catalog")``."""
    with open(_DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)
