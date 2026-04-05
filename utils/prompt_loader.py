"""
Load test prompt cases from ``prompts.json`` at the project root.

Each file entry is expected to be an object with at least ``prompt``, and typically
``case`` and ``context`` for labeling output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROMPTS_PATH = _PROJECT_ROOT / "prompts.json"


def load_prompts() -> list[dict[str, Any]]:
    """
    Read ``prompts.json`` and return the list of prompt cases.

    Returns:
        A list of dictionaries, one per test case.

    Exits:
        The process with code 1 if the file is missing or the root JSON value is not an array.
    """
    if not _PROMPTS_PATH.is_file():
        print(
            f"Missing {_PROMPTS_PATH.relative_to(_PROJECT_ROOT)} at the project root.",
            file=sys.stderr,
        )
        sys.exit(1)
    with _PROMPTS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("prompts.json must be a JSON array of objects.", file=sys.stderr)
        sys.exit(1)
    return data
