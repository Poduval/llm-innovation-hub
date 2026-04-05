"""
Call OpenAI-compatible chat completion APIs using per-provider settings from ``config/APIs.json``.

Uses the ``openai`` Python client with a custom ``base_url`` so the same code path can target
NVIDIA NIM, Groq, Mistral, or any other provider listed in the config file.

API keys may be set in ``config/APIs.json`` or, when ``api_key`` is empty, via environment
variables (typically from a project-root ``.env`` file): ``NVIDIA_API_KEY``, ``GROQ_API_KEY``,
``{PROVIDER}_API_KEY``, or a custom name via ``api_key_env`` in the provider block.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from openai import OpenAI

from utils.config_loader import get_provider, list_provider_names


def _resolve_api_key(provider: str, block: dict[str, Any]) -> str:
    """
    Use ``api_key`` from config when set; otherwise read from the environment.

    Env var name: optional ``api_key_env`` in the provider block, else ``{PROVIDER}_API_KEY``
    (e.g. ``groq`` → ``GROQ_API_KEY``). Values are loaded from ``.env`` via ``config_loader``.
    """
    raw = block.get("api_key")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    env_name_raw = block.get("api_key_env")
    if env_name_raw is not None and str(env_name_raw).strip():
        env_name = str(env_name_raw).strip()
    else:
        env_name = f"{provider.upper()}_API_KEY"
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    raise ValueError(
        f'No API key for "{provider}": set environment variable {env_name} '
        f'or config/APIs.json["{provider}"]["api_key"].'
    )


def _require_str(block: dict[str, Any], key: str, provider: str) -> str:
    """Return a non-empty string field from ``block`` or raise ``ValueError``."""
    raw = block.get(key)
    if raw is None or not str(raw).strip():
        raise ValueError(
            f'config/APIs.json["{provider}"]["{key}"] must be a non-empty string.'
        )
    return str(raw).strip()


def _require_int(block: dict[str, Any], key: str, provider: str) -> int:
    """Return a required integer field from ``block`` or raise ``ValueError``."""
    if key not in block:
        raise ValueError(
            f'config/APIs.json["{provider}"]["{key}"] is required (integer).'
        )
    try:
        return int(block[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'config/APIs.json["{provider}"]["{key}"] must be an integer.'
        ) from exc


def _optional_float(block: dict[str, Any], key: str, provider: str) -> float | None:
    """Optional float; ``None`` if missing. Raises if present but not numeric."""
    if key not in block:
        return None
    try:
        return float(block[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'config/APIs.json["{provider}"]["{key}"] must be a number.'
        ) from exc


def _optional_int(block: dict[str, Any], key: str, provider: str, default: int) -> int:
    """Optional int with ``default`` if missing. Raises if present but not an integer."""
    if key not in block:
        return default
    try:
        return int(block[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'config/APIs.json["{provider}"]["{key}"] must be an integer.'
        ) from exc


def _vlog(verbose: bool, message: str) -> None:
    if verbose:
        print(message, file=sys.stderr, flush=True)


def complete_chat(prompt: str, api: str, *, verbose: bool = False) -> str:
    """
    Send a single user message to the given provider and return the assistant reply text.

    Args:
        prompt: User message content.
        api: Provider name matching a top-level key in ``config/APIs.json`` (case-insensitive),
            for example ``"groq"`` or ``"nvidia"``.
        verbose: When ``True``, log request settings and response metadata to stderr.

    Returns:
        The first choice's message content, stripped of leading and trailing whitespace.
        Empty string if the API returns no content.

    Raises:
        ValueError: If ``api`` is not a configured provider, ``prompt`` is empty after stripping,
            or required provider fields in ``config/APIs.json`` are missing or invalid.
    """
    api = str(api).strip().lower()
    configured = list_provider_names()
    if api not in configured:
        names = ", ".join(sorted(configured))
        raise ValueError(f'Unknown API "{api}". Config providers: {names}')

    p = get_provider(api)
    user_text = str(prompt).strip()
    if not user_text:
        raise ValueError("prompt must be a non-empty string.")

    api_key = _resolve_api_key(api, p)
    base_url = _require_str(p, "base_url", api)
    model = _require_str(p, "model", api)
    max_tokens = _require_int(p, "max_tokens", api)

    timeout_raw = _optional_float(p, "timeout_seconds", api)
    read_timeout = 90.0 if timeout_raw is None else float(timeout_raw)
    connect_timeout = _optional_float(p, "connect_timeout_seconds", api)
    connect_sec = 15.0 if connect_timeout is None else float(connect_timeout)
    # Avoid hanging on TCP/TLS when a host is slow or unroutable (read timeout alone can
    # still wait a long time for the connect phase on some stacks).
    httpx_timeout = httpx.Timeout(read_timeout, connect=connect_sec)
    max_retries = _optional_int(p, "max_retries", api, 1)

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=httpx_timeout,
        max_retries=max_retries,
    )

    request: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": user_text}],
        "max_tokens": max_tokens,
    }

    temp = _optional_float(p, "temperature", api)
    if temp is not None:
        request["temperature"] = temp

    top_p = _optional_float(p, "top_p", api)
    if top_p is not None:
        request["top_p"] = top_p

    _vlog(
        verbose,
        "[verbose] "
        + f"provider={api} base_url={base_url} model={model} max_tokens={max_tokens} "
        + f"read_timeout_s={read_timeout} connect_timeout_s={connect_sec} max_retries={max_retries} "
        + "api_key=(redacted)",
    )
    _vlog(verbose, f"[verbose] chat.completions.create kwargs={ {k: v for k, v in request.items()} }")

    response = client.chat.completions.create(**request)
    choice0 = response.choices[0]
    content = choice0.message.content
    _vlog(verbose, f"[verbose] response id={getattr(response, 'id', None)!r}")
    _vlog(verbose, f"[verbose] response model={getattr(response, 'model', None)!r}")
    _vlog(verbose, f"[verbose] finish_reason={choice0.finish_reason!r}")
    usage = getattr(response, "usage", None)
    if usage is not None:
        _vlog(verbose, f"[verbose] usage={usage!r}")
    return (content or "").strip()
