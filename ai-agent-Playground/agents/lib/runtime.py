"""Shared runtime for Open WebUI Pipeline agents (not loaded as a pipeline module)."""

from __future__ import annotations

import html
import json
import re
import uuid
from pathlib import Path
from typing import Any, Generator, Iterator, Union

import httpx
from pydantic import BaseModel, Field

AGENTS_MD = Path(__file__).resolve().parent.parent / "AGENTS.md"

IAZI_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "validate_canton",
            "description": (
                "Validate a Swiss canton code (two letters, e.g. ZH, BE) and return ortId (1–26)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "canton": {
                        "type": "string",
                        "description": "Two-letter Swiss canton code",
                    }
                },
                "required": ["canton"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_price",
            "description": (
                "Estimate property purchase price (CHF). Requires ortId from validate_canton."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ortId": {"type": "integer", "description": "Location id 1–26"},
                    "roomNb": {"type": "integer", "description": "Number of rooms (1–5)"},
                    "surfaceLiving": {
                        "type": "number",
                        "description": "Living surface m² (80–120)",
                    },
                },
                "required": ["ortId", "roomNb", "surfaceLiving"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_rent",
            "description": (
                "Estimate monthly rent (CHF). Requires ortId from validate_canton."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ortId": {"type": "integer", "description": "Location id 1–26"},
                    "roomNb": {"type": "integer", "description": "Number of rooms (1–5)"},
                    "surfaceLiving": {
                        "type": "number",
                        "description": "Living surface m² (80–120)",
                    },
                },
                "required": ["ortId", "roomNb", "surfaceLiving"],
            },
        },
    },
]

_FALLBACK_IAZI = (
    "You are the IAZI Valuation Expert. Use validate_canton, estimate_price, and "
    "estimate_rent tools. Default roomNb=3 and surfaceLiving=100 when missing."
)


def load_agent_instructions(agent_key: str) -> str:
    """Load system prompt body from AGENTS.md section ``## Agent: {agent_key}``."""
    if not AGENTS_MD.is_file():
        return _FALLBACK_IAZI if "IAZI" in agent_key else f"You are {agent_key}."

    text = AGENTS_MD.read_text(encoding="utf-8")
    pattern = rf"^## Agent:\s*{re.escape(agent_key)}\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return _FALLBACK_IAZI if "IAZI" in agent_key else f"You are {agent_key}."

    start = match.end()
    next_agent = re.search(r"^## Agent:\s*", text[start:], re.MULTILINE)
    end = start + next_agent.start() if next_agent else len(text)
    section = text[start:end].strip()
    # Drop HTML comment template blocks
    section = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL).strip()
    return f"You are **{agent_key}**.\n\n{section}" if section else _FALLBACK_IAZI


def details_block(call_id: str, name: str, arguments: dict, result: Any) -> str:
    return (
        f'<details type="tool_calls" done="true" '
        f'id="{call_id}" name="{name}" '
        f'arguments="{html.escape(json.dumps(arguments))}">\n'
        f"<summary>Tool Executed</summary>\n"
        f"{html.escape(json.dumps(result, ensure_ascii=False, default=str))}\n"
        f"</details>\n"
    )


class ServiceValves(BaseModel):
    LITELLM_BASE_URL: str = Field(
        default="http://litellm:4000/v1",
        description="LiteLLM OpenAI-compatible base URL",
    )
    LITELLM_API_KEY: str = Field(default="sk-litellm-local", description="LiteLLM master key")
    LITELLM_MODEL: str = Field(
        default="groq-llama-3.1-8b",
        description="LiteLLM model_name from litellm/config.yaml",
    )
    ADDRESS_VALIDATION_URL: str = Field(
        default="http://addressvalidation:8000",
        description="AddressValidation service base URL",
    )
    SERVICEMODELR_URL: str = Field(
        default="http://servicemodelr:8000",
        description="ServiceModelR service base URL",
    )
    MAX_TOOL_ROUNDS: int = Field(default=8, description="Maximum tool-call rounds")


def run_tool(
    client: httpx.Client, valves: ServiceValves, name: str, args: dict[str, Any]
) -> dict[str, Any]:
    if name == "validate_canton":
        canton = str(args.get("canton", "")).strip().upper()
        r = client.post(
            f"{valves.ADDRESS_VALIDATION_URL.rstrip('/')}/validate",
            json={"canton": canton},
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()

    payload = {
        "ortId": int(args["ortId"]),
        "roomNb": int(args["roomNb"]),
        "surfaceLiving": float(args["surfaceLiving"]),
    }
    path = "/price" if name == "estimate_price" else "/rent"
    r = client.post(
        f"{valves.SERVICEMODELR_URL.rstrip('/')}{path}",
        json=payload,
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()


def chat_completion(
    client: httpx.Client,
    valves: ServiceValves,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    url = f"{valves.LITELLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {valves.LITELLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": valves.LITELLM_MODEL,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "stream": False,
    }
    r = client.post(url, json=body, headers=headers, timeout=120.0)
    r.raise_for_status()
    return r.json()


def prepare_messages(
    messages: list[dict[str, Any]], system_prompt: str
) -> list[dict[str, Any]]:
    msgs = list(messages)
    if not msgs or msgs[0].get("role") != "system":
        msgs = [{"role": "system", "content": system_prompt}, *msgs]
    return msgs


def run_agent_pipe(
    *,
    valves: ServiceValves,
    system_prompt: str,
    tool_specs: list[dict[str, Any]],
    display_name: str,
    messages: list[dict[str, Any]],
    body: dict,
) -> Union[str, Generator[str, None, None], Iterator[str]]:
    messages = prepare_messages(messages, system_prompt)

    def stream() -> Generator[str, None, None]:
        yield f"{display_name} is working…\n\n"

        with httpx.Client() as client:
            for _ in range(valves.MAX_TOOL_ROUNDS):
                data = chat_completion(client, valves, messages, tool_specs)
                msg = data["choices"][0]["message"]
                tool_calls = msg.get("tool_calls") or []

                if tool_calls:
                    messages.append(msg)
                    for tc in tool_calls:
                        fn = tc.get("function") or {}
                        name = fn.get("name", "")
                        raw_args = fn.get("arguments") or "{}"
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {"raw": raw_args}
                        call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:12]}"

                        try:
                            result = run_tool(client, valves, name, args)
                        except httpx.HTTPStatusError as exc:
                            result = {
                                "error": True,
                                "status": exc.response.status_code,
                                "detail": exc.response.text,
                            }
                        except Exception as exc:  # noqa: BLE001
                            result = {"error": True, "detail": str(exc)}

                        yield details_block(call_id, name, args, result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": json.dumps(result),
                            }
                        )
                    continue

                content = (msg.get("content") or "").strip()
                yield content or "(No text returned from the model.)"
                return

        yield (
            "Stopped: reached maximum tool rounds. "
            "Increase MAX_TOOL_ROUNDS in Admin → Pipelines → Valves."
        )

    if body.get("stream"):
        return stream()
    return "".join(stream())
