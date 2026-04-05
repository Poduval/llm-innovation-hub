"""
Load LLM provider definitions from ``config/APIs.json``.

The JSON file is expected at the project root under ``config/APIs.json``. Each
top-level key whose value is an object is treated as a named provider (for example
``nvidia``, ``groq``, ``mistral``).
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "APIs.json"

# Load `.env` from project root so API keys can live outside `config/APIs.json`.
load_dotenv(_PROJECT_ROOT / ".env")


@lru_cache(maxsize=1)
def load_raw_config() -> dict[str, Any]:
    """
    Read and parse ``config/APIs.json`` (cached for the lifetime of the process).

    Exits with code 1 if the file is missing, unreadable, or not a JSON object.
    """
    if not _CONFIG_PATH.is_file():
        print(
            f"Missing {_CONFIG_PATH.relative_to(_PROJECT_ROOT)}. "
            "Create it with per-provider objects: api_key, base_url, model, max_tokens; "
            "optional temperature, top_p, timeout_seconds, connect_timeout_seconds, max_retries.",
            file=sys.stderr,
        )
        sys.exit(1)
    with _CONFIG_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print("config/APIs.json must be a JSON object at the top level.", file=sys.stderr)
        sys.exit(1)
    return data


def list_provider_names() -> list[str]:
    """
    Return the names of all providers defined in ``config/APIs.json``.

    Only top-level keys whose values are JSON objects are included (nested objects
    under non-dict values are ignored).

    Returns:
        Provider names in the order they appear in the file.
    """
    cfg = load_raw_config()
    return [k for k, v in cfg.items() if isinstance(v, dict)]


def get_provider(name: str) -> dict[str, Any]:
    """
    Return the configuration block for a single provider.

    Args:
        name: Provider key as it appears in ``config/APIs.json`` (for example ``"groq"``).

    Returns:
        That provider's JSON object as a dictionary.

    Exits:
        The process with code 1 if ``name`` is missing or not an object.
    """
    cfg = load_raw_config()
    block = cfg.get(name)
    if not isinstance(block, dict):
        print(
            f'config/APIs.json must contain a "{name}" object (see other providers for keys).',
            file=sys.stderr,
        )
        sys.exit(1)
    return block
