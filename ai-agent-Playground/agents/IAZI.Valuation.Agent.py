"""
title: Agent: IAZI Valuation Expert
author: llm-innovation-hub
version: 1.1.0
license: MIT
description: |
  IAZI Valuation Expert — LiteLLM brain + AddressValidation + ServiceModelR.
  Behavior is defined in agents/AGENTS.md (section IAZI Valuation Expert).
requirements: httpx
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Generator, Iterator, Union

# Shared helpers live in agents/lib/ (not auto-loaded by Pipelines)
_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from runtime import (  # noqa: E402
    IAZI_TOOL_SPECS,
    ServiceValves,
    load_agent_instructions,
    run_agent_pipe,
)

AGENT_KEY = "IAZI Valuation Expert"
DISPLAY_NAME = "Agent: IAZI Valuation Expert"
MODEL_ID = "iazi-valuation-expert"


class Pipeline:
    """Open WebUI Pipelines entry (class name must be ``Pipeline``)."""

    Valves = ServiceValves

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.id = MODEL_ID
        self.name = DISPLAY_NAME
        self._system_prompt = load_agent_instructions(AGENT_KEY)

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: list[dict[str, Any]],
        body: dict,
    ) -> Union[str, Generator[str, None, None], Iterator[str]]:
        del user_message, model_id
        return run_agent_pipe(
            valves=self.valves,
            system_prompt=self._system_prompt,
            tool_specs=IAZI_TOOL_SPECS,
            display_name=DISPLAY_NAME,
            messages=messages,
            body=body,
        )
