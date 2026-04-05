"""
ANSI styling, rules, wrapping, and structured blocks for terminal comparison reports.
"""

from __future__ import annotations

import os
import sys
import textwrap
from datetime import datetime

REPORT_WIDTH = 72


def colors_enabled() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""


def styled(text: str, *codes: int) -> str:
    if not colors_enabled():
        return text
    seq = ";".join(str(c) for c in codes)
    return f"\033[{seq}m{text}\033[0m"


def emit_rule(char: str = "─") -> None:
    print(char * REPORT_WIDTH, flush=True)


def emit_blank() -> None:
    print(flush=True)


def fmt_elapsed(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.2f} s"


def status_badge(ok: bool) -> str:
    if colors_enabled():
        return styled("✓ OK", 1, 32) if ok else styled("✗ FAIL", 1, 31)
    return "[ OK ]" if ok else "[FAIL]"


def wrap_indent(text: str, prefix: str, width: int) -> None:
    initial = width - len(prefix.expandtabs())
    for para in text.split("\n"):
        chunk = textwrap.fill(
            para,
            width=max(20, initial),
            break_long_words=False,
            break_on_hyphens=False,
        )
        first = True
        for line in chunk.splitlines() or [""]:
            pad = prefix if first else " " * len(prefix)
            print(pad + line, flush=True)
            first = False


def text_wrap_width() -> int:
    return max(32, REPORT_WIDTH - 6)


def emit_run_header(*, n_cases: int, providers: list[str]) -> None:
    n_prov = len(providers)
    prov_line = ", ".join(providers)
    if len(prov_line) > REPORT_WIDTH - 6:
        prov_line = prov_line[: REPORT_WIDTH - 9] + "…"

    emit_rule("=")
    print(styled("  LLM INNOVATION HUB", 1, 36), flush=True)
    print(styled("  API comparison run", 2, 37), flush=True)
    emit_rule("─")
    print(
        styled(
            f"  {n_cases} test case{'s' if n_cases != 1 else ''}  ×  "
            f"{n_prov} provider{'s' if n_prov != 1 else ''}",
            1,
            37,
        ),
        flush=True,
    )
    print(styled(f"  Providers: {prov_line}", 2, 37), flush=True)
    print(
        styled(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 2, 37),
        flush=True,
    )
    emit_rule("=")
    emit_blank()


def emit_run_footer(*, n_cases: int) -> None:
    emit_blank()
    emit_rule("=")
    print(
        styled(
            f"  Done · {n_cases} case{'s' if n_cases != 1 else ''} completed",
            2,
            37,
        ),
        flush=True,
    )
    emit_rule("=")


def emit_case_banner(
    idx: int,
    n_cases: int,
    *,
    context: str,
    case: str,
) -> None:
    emit_rule("=")
    print(styled(f"  CASE {idx} OF {n_cases}", 1, 35), flush=True)
    if context:
        print(styled(f"  {context}", 1, 37), flush=True)
    elif case:
        print(styled(f"  {case}", 1, 37), flush=True)


def emit_prompt_section(prompt: str, *, wrap_width: int | None = None) -> None:
    w = text_wrap_width() if wrap_width is None else wrap_width
    emit_rule("─")
    print(styled("  PROMPT", 1, 33), flush=True)
    wrap_indent(prompt, "    ", w)


def emit_responses_section_header() -> None:
    emit_rule("─")
    print(styled("  RESPONSES", 1, 32), flush=True)
    emit_blank()


def emit_provider_result_header(*, ok: bool, api: str, elapsed_s: float) -> None:
    api_style = (1, 31) if not ok else (1, 36)
    line = (
        f"    {status_badge(ok)}  {styled(api, *api_style)}  ·  "
        f"{styled(fmt_elapsed(elapsed_s), 2, 37)}"
    )
    print(line, flush=True)


def emit_provider_result_body(text: str, *, wrap_width: int | None = None) -> None:
    w = text_wrap_width() if wrap_width is None else wrap_width
    wrap_indent(text, "      ", w)
    emit_blank()


def emit_provider_error_hint() -> None:
    print(
        styled("      (see ERROR above on stderr for details)", 2, 37),
        flush=True,
    )
    emit_blank()


def emit_querying_stderr(api: str) -> None:
    if sys.stderr.isatty():
        print(styled(f"    · querying {api}…", 2, 37), file=sys.stderr, flush=True)
