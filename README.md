# LLM innovation hub

This repository combines two related experiments:

1. **LLM prompt comparison** (repo root) — run the same prompts against several **OpenAI-compatible** chat APIs (NVIDIA NIM, Groq, Mistral) using shared config and a terminal report.
2. **`ai-agent-playground/`** — two mock **Swiss real-estate** HTTP services (FastAPI) for agent/tool demos, with **Docker Compose** and optional **.NET Aspire** orchestration and **OpenTelemetry**.

The two parts are independent: no shared Python imports or config files between them.

---

## Tech stack

| Area | Languages / runtimes | Main libraries & tools |
|------|----------------------|-------------------------|
| **LLM comparison** | Python 3.12+ | [`openai`](https://pypi.org/project/openai/) (chat completions), [`python-dotenv`](https://pypi.org/project/python-dotenv/), [`httpx`](https://pypi.org/project/httpx/) (timeouts via `openai` client) |
| **Playground APIs** | Python 3.12 | [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic](https://docs.pydantic.dev/) v2 |
| **Playground observability** | — | [OpenTelemetry](https://opentelemetry.io/) SDK + OTLP exporters (gRPC/HTTP); auto-instrumentation for FastAPI and logging |
| **Playground hosting** | Docker | `docker compose` (two services, Python 3.12-slim images) |
| **Playground orchestration** | .NET 9 | [Aspire](https://learn.microsoft.com/dotnet/aspire/) 9.3 AppHost (`Aspire.Hosting.AppHost`), Dockerfile resources for both Python apps |

---

## Repository layout

```text
.
├── .env.example                 # Template for LLM API keys (copy to .env)
├── .gitignore
├── README.md
├── config/
│   └── APIs.json                # LLM provider URLs, models, generation settings
├── prompts.json                 # Test cases: case, context, prompt
├── requirements.txt             # Root venv: openai, python-dotenv
├── test_basic_prompts.py        # CLI driver for LLM comparison
├── utils/
│   ├── config_loader.py         # Load APIs.json; dotenv; list_provider_names()
│   ├── prompt_loader.py         # Load prompts.json
│   ├── chat_provider.py         # complete_chat(prompt, api, verbose=...)
│   └── terminal_report.py       # ANSI stdout/stderr report helpers
└── ai-agent-playground/         # Self-contained playground (see below)
    ├── AgentsPlayground.sln
    ├── docker-compose.yml
    ├── README.md                # API contracts & playground-specific run steps
    ├── servicemodelr/           # FastAPI: POST /price, POST /rent
    ├── addressvalidation/       # FastAPI: POST /validate
    └── aspire/
        ├── aspire.config.json
        └── AppHost/             # Aspire: builds Docker contexts ../../servicemodelr, ../../addressvalidation
```

Paths inside **`ai-agent-playground/`** are written relative to that folder (whether the repo lives standalone or under this hub).

---

## Part 1 — LLM prompt comparison (repo root)

### What it does

- Reads provider definitions from **`config/APIs.json`** (top-level keys = provider names, e.g. `nvidia`, `groq`, `mistral`).
- Reads test cases from **`prompts.json`** (array of `{ "case", "context", "prompt" }`).
- For each selected case and provider, calls **`utils.chat_provider.complete_chat(prompt, api)`** and prints a formatted report to the terminal.

### APIs under test

| Provider key | Service | Default `base_url` | API key |
|--------------|---------|-------------------|---------|
| `nvidia` | [NVIDIA NIM (Build)](https://build.nvidia.com/explore/discover) | `https://integrate.api.nvidia.com/v1` | `NVIDIA_API_KEY` |
| `groq` | [Groq](https://console.groq.com/) | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| `mistral` | [Mistral AI](https://console.mistral.ai/) | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` |

All use the OpenAI **chat completions** shape (`POST …/chat/completions`).

### `config/APIs.json` fields (per provider)

| Field | Required | Description |
|-------|----------|-------------|
| `api_key` | No* | Inline key; leave empty to use env (see below) |
| `api_key_env` | No | Override env var name (default: `{PROVIDER}_API_KEY`) |
| `base_url` | Yes | OpenAI-compatible API root |
| `model` | Yes | Model id for `chat.completions` |
| `max_tokens` | Yes | Max completion tokens |
| `temperature` | No | Sent to API if present |
| `top_p` | No | Sent to API if present |
| `timeout_seconds` | No | Read timeout for the HTTP client (default **60**) |
| `connect_timeout_seconds` | No | Connect timeout (default **15**) |
| `max_retries` | No | OpenAI client retries (default **1**) |

\*At least one of `api_key` or the resolved env var must be set.

### Secrets (`.env`)

```bash
cp .env.example .env
# Edit .env — never commit it (.gitignore)
```

`config_loader` loads **`.env`** from the **project root** on import. Keys in `.env.example` match the default `{PROVIDER}_API_KEY` names.

### Setup and run

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python test_basic_prompts.py
python test_basic_prompts.py --help
```

### CLI — `test_basic_prompts.py`

| Flag | Description |
|------|-------------|
| `--api NAME` | Limit providers (repeat or comma-separated, e.g. `--api groq` or `--api groq,mistral`). Default: all keys in `APIs.json`. |
| `--case IDS` | Comma-separated `case` ids from `prompts.json` (e.g. `--case 1,2`). Default: all cases. |
| `--verbose` | Extra stderr logging per call (`--verbose`, `--verbose true`, or `--verbose false`). |

Examples:

```bash
python test_basic_prompts.py
python test_basic_prompts.py --api groq
python test_basic_prompts.py --case 1 --api nvidia,groq
python test_basic_prompts.py --verbose
```

On failure for one provider, the script prints `ERROR:` on stderr and continues with the remaining providers.

### Core Python API

```python
from utils.chat_provider import complete_chat

text = complete_chat("Explain JSON in one sentence.", "groq", verbose=False)
```

`api` must match a top-level key in `config/APIs.json` (case-insensitive).

---

## Part 2 — `ai-agent-playground/`

Mock backends for flows like: **canton → `ortId` → price/rent estimate**. Full request/response schemas and formulas are in **`ai-agent-playground/README.md`**.

### Services and ports (host)

| Service | Host port | Container port | Endpoints |
|---------|-----------|------------------|-----------|
| **servicemodelr** | **8001** | 8000 | `POST /price`, `POST /rent`, `GET /health` |
| **addressvalidation** | **8002** | 8000 | `POST /validate`, `GET /health` |

Aspire exposes the same host ports when using the AppHost.

### How paths work in this monorepo

| Entry point | Working directory | Notes |
|-------------|-------------------|--------|
| `docker compose` | `ai-agent-playground/` | `build: ./servicemodelr` and `./addressvalidation` |
| `uvicorn` (local) | `ai-agent-playground/servicemodelr` or `…/addressvalidation` | See playground README |
| Aspire AppHost | `ai-agent-playground/aspire/AppHost` | `Program.cs` uses `../../servicemodelr` and `../../addressvalidation` as Docker build contexts |
| Visual Studio solution | `ai-agent-playground/AgentsPlayground.sln` | Project path `aspire\AppHost\AppHost.csproj` |

From the **repo root**, you can still build the solution:

```bash
dotnet build ai-agent-playground/AgentsPlayground.sln
```

### Run with Docker Compose (recommended for a quick check)

```bash
cd ai-agent-playground
docker compose up --build
```

- OpenAPI UI: http://localhost:8001/docs and http://localhost:8002/docs  
- Health: http://localhost:8001/health , http://localhost:8002/health  

Stop: `docker compose down` in the same directory.

Or from the repo root:

```bash
docker compose -f ai-agent-playground/docker-compose.yml up --build
```

### Run with .NET Aspire (dev dashboard + OTLP)

**Prerequisites:** [.NET 9 SDK](https://dotnet.microsoft.com/download) and Docker (Aspire builds the Python images).

```bash
cd ai-agent-playground/aspire/AppHost
dotnet run --launch-profile http
```

The console prints an Aspire Dashboard login URL (e.g. `http://localhost:15152/login?t=…`). Use it for logs, traces, and metrics. Python services export OTLP when Aspire sets `OTEL_EXPORTER_OTLP_ENDPOINT`; without it, telemetry stays local-only (no export).

**Do not** run Docker Compose and Aspire at the same time — both bind **8001** and **8002**.

> **Platform note:** `aspire/AppHost/AppHost.csproj` currently references **macOS ARM64** Aspire orchestration packages (`Aspire.Hosting.Orchestration.osx-arm64`, `Aspire.Dashboard.Sdk.osx-arm64`). On Linux or Windows you may need to swap these for the RID-appropriate Aspire packages for your machine.

Alternative (Aspire CLI, if installed):

```bash
cd ai-agent-playground/aspire
aspire run
```

(`aspire.config.json` points at `AppHost/AppHost.csproj`.)

### Example API flow

```bash
curl -s -X POST http://127.0.0.1:8002/validate \
  -H "Content-Type: application/json" -d '{"canton":"BE"}'

curl -s -X POST http://127.0.0.1:8001/price \
  -H "Content-Type: application/json" \
  -d '{"ortId":2,"roomNb":3,"surfaceLiving":80}'
```

### Playground Python dependencies

Each service has its own `requirements.txt` under `servicemodelr/` and `addressvalidation/` (FastAPI, Uvicorn, OpenTelemetry stack). Dockerfiles use **Python 3.12-slim** and run:

`uvicorn main:app --host 0.0.0.0 --port 8000`

---

## Ports at a glance

| Port | Used by |
|------|---------|
| 8001 | Playground — ServiceModelR |
| 8002 | Playground — AddressValidation |
| 15152 (typical) | Aspire Dashboard (HTTP profile) |
| — | LLM comparison has **no** HTTP server; outbound HTTPS only |

---

## Prerequisites summary

| Task | You need |
|------|----------|
| LLM comparison | Python 3.12+, venv, API keys in `.env` |
| Playground (Docker) | Docker Engine, Compose v2 |
| Playground (Aspire) | .NET 9 SDK, Docker, macOS ARM packages as committed (or adjust csproj) |
| Playground (local Python) | Python 3.12+, per-service `pip install -r requirements.txt` |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `No API key for "groq"` | Missing `.env` or empty `GROQ_API_KEY` / `api_key` in `APIs.json` |
| `Unknown API` / `unknown --api` | Typo; provider key must exist in `APIs.json` |
| `ModuleNotFoundError: utils` | Run scripts from the **repo root**, not from inside `utils/` |
| Docker build fails | Run `docker compose` from **`ai-agent-playground/`** (or pass `-f` path) |
| Port already in use | Another process on 8001/8002, or Compose + Aspire both running |
| `curl` to localhost fails | Confirm containers are up (`docker ps`); try `127.0.0.1` instead of `localhost` |

---

## Requirements files

| File | Purpose |
|------|---------|
| `requirements.txt` (root) | LLM comparison: `openai`, `python-dotenv` |
| `ai-agent-playground/servicemodelr/requirements.txt` | ServiceModelR service |
| `ai-agent-playground/addressvalidation/requirements.txt` | AddressValidation service |
