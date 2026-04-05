#!/usr/bin/env python3
"""
Exercise LLM providers from ``config/APIs.json`` against cases in ``prompts.json``.

Use ``--api`` to limit which providers run (default: all). Use ``--case`` to limit which
prompt cases run by ``case`` id in ``prompts.json`` (default: all). Use ``--verbose`` for
detailed stderr logs. Failed calls print ``ERROR:`` on stderr and the run continues.
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from collections import defaultdict
from typing import Any

from utils.chat_provider import complete_chat
from utils.config_loader import list_provider_names
from utils.prompt_loader import load_prompts
from utils.terminal_report import (
    emit_blank,
    emit_case_banner,
    emit_prompt_section,
    emit_provider_error_hint,
    emit_provider_result_body,
    emit_provider_result_header,
    emit_querying_stderr,
    emit_responses_section_header,
    emit_run_footer,
    emit_run_header,
    text_wrap_width,
)


def _boolish_verbose(value: object) -> bool:
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "1", "yes", "on"):
        return True
    if s in ("false", "0", "no", "off"):
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def _expand_api_args(values: list[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for item in values:
        for part in item.split(","):
            p = part.strip().lower()
            if p:
                out.append(p)
    return out


def _expand_case_arg(raw: str | None) -> list[str] | None:
    if raw is None or not str(raw).strip():
        return None
    out: list[str] = []
    for part in str(raw).split(","):
        p = part.strip()
        if p:
            out.append(p)
    if not out:
        return None
    seen: set[str] = set()
    deduped: list[str] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped


def _prompts_by_case_id(prompts: list[Any]) -> dict[str, list[dict[str, Any]]]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in prompts:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("case", "")).strip()
        if cid:
            by_case[cid].append(entry)
    return by_case


def _select_prompts_for_cases(
    prompts: list[Any],
    wanted_ids: list[str],
) -> list[dict[str, Any]]:
    by_case = _prompts_by_case_id(prompts)
    available = sorted(by_case.keys(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x.lower()))

    selected: list[dict[str, Any]] = []
    for cid in wanted_ids:
        if cid not in by_case:
            print(
                f"ERROR: unknown --case {cid!r}. Known case ids: {', '.join(available) or '(none)'}",
                file=sys.stderr,
            )
            sys.exit(1)
        selected.extend(by_case[cid])
    return selected


def _resolve_providers(configured: list[str], wanted_lower: list[str]) -> list[str]:
    if not wanted_lower:
        return list(configured)
    by_lower = {name.lower(): name for name in configured}
    seen: list[str] = []
    for w in wanted_lower:
        if w not in by_lower:
            print(
                f'ERROR: unknown --api {w!r}. Configured providers: {", ".join(configured)}',
                file=sys.stderr,
            )
            sys.exit(1)
        canon = by_lower[w]
        if canon not in seen:
            seen.append(canon)
    return seen


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run prompts.json cases against OpenAI-compatible APIs from config/APIs.json.",
    )
    parser.add_argument(
        "--api",
        action="append",
        dest="apis",
        metavar="NAME",
        help="Provider key from config (repeat or comma-separate). Default: all providers.",
    )
    parser.add_argument(
        "--case",
        metavar="IDS",
        help='Comma-separated ``case`` values from prompts.json (e.g. ``1,2``). Default: all cases.',
    )
    parser.add_argument(
        "--verbose",
        nargs="?",
        const=True,
        default=False,
        type=_boolish_verbose,
        help="Detailed stderr logs for each call. Use alone, or `--verbose true` / `--verbose false`.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    verbose = bool(args.verbose)

    prompts = load_prompts()
    configured = list_provider_names()
    if not configured:
        print("No provider objects found in config/APIs.json.", file=sys.stderr)
        sys.exit(1)

    wanted = _expand_api_args(args.apis)
    providers = _resolve_providers(configured, wanted)
    if not providers:
        print("ERROR: no providers to run after --api filter.", file=sys.stderr)
        sys.exit(1)

    case_filter = _expand_case_arg(args.case)
    if case_filter is not None:
        to_run = _select_prompts_for_cases(prompts, case_filter)
        if not to_run:
            print("ERROR: no prompts matched --case filter.", file=sys.stderr)
            sys.exit(1)
    else:
        to_run = list(prompts)

    n_cases = len(to_run)
    emit_run_header(n_cases=n_cases, providers=providers)
    wrap_w = text_wrap_width()

    for idx, entry in enumerate(to_run, start=1):
        if not isinstance(entry, dict):
            print("Each prompts.json entry must be an object.", file=sys.stderr)
            sys.exit(1)

        case = str(entry.get("case", "")).strip() or "case ?"
        context = str(entry.get("context", "")).strip()
        prompt = str(entry.get("prompt", "")).strip()
        if not prompt:
            print(f'prompts.json entry "{case}" has an empty prompt.', file=sys.stderr)
            sys.exit(1)

        emit_case_banner(idx, n_cases, context=context, case=case)
        emit_prompt_section(prompt, wrap_width=wrap_w)
        emit_responses_section_header()

        for api in providers:
            if not verbose:
                emit_querying_stderr(api)
            t0 = time.perf_counter()
            try:
                response_text = complete_chat(prompt, api, verbose=verbose)
            except Exception as exc:
                elapsed = time.perf_counter() - t0
                print(f"ERROR: {api}: {exc}", file=sys.stderr, flush=True)
                if verbose:
                    traceback.print_exc(file=sys.stderr)
                emit_provider_result_header(ok=False, api=api, elapsed_s=elapsed)
                emit_provider_error_hint()
                continue

            elapsed = time.perf_counter() - t0
            emit_provider_result_header(ok=True, api=api, elapsed_s=elapsed)
            emit_provider_result_body(response_text, wrap_width=wrap_w)

        emit_blank()

    emit_run_footer(n_cases=n_cases)


if __name__ == "__main__":
    main()
