# Aspire orchestration

Runs the **full playground stack** in Docker: mock APIs, LiteLLM, Pipelines (agents), and Open WebUI. The **Aspire Dashboard** lists every container, logs, traces, and clickable HTTP endpoints.

## Prerequisites

- [.NET 9 SDK](https://dotnet.microsoft.com/download)
- Docker Desktop (running)
- Repo-root `.env` with `NVIDIA_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY` (optional but required for LiteLLM calls)

> **Platform:** `AppHost.csproj` references **macOS ARM64** Aspire packages. On Linux/Windows, swap `Aspire.Hosting.Orchestration.osx-arm64` and `Aspire.Dashboard.Sdk.osx-arm64` for your RID.

## Start

```bash
cd ai-agent-playground/aspire/AppHost
dotnet run --launch-profile http
```

Or from `ai-agent-playground/aspire`:

```bash
aspire run
```

The terminal prints a **dashboard login URL** (token in query string). The browser may open automatically.

**Do not** run this and `docker compose up` at the same time — the same host ports are used.

## Aspire Dashboard

| Profile | Dashboard URL (typical) |
|---------|-------------------------|
| `http` | [http://localhost:15152](http://localhost:15152) |
| `https` | [https://localhost:17209](https://localhost:17209) |

Use the **exact** URL from your terminal (`…/login?t=…`). In the dashboard:

1. **Resources** — all containers and health
2. **Console logs** — per resource
3. **Traces / Metrics / Structured logs** — OTLP from Python services and containers
4. **Endpoints** — links to each HTTP URL below

## Containers and API endpoints

| Resource | Host port | Endpoint | Purpose |
|----------|-----------|----------|---------|
| **open-webui** | 3000 | [http://localhost:3000](http://localhost:3000) | Chat UI → **Agent: IAZI Valuation Expert** |
| **pipelines** | 9099 | [http://localhost:9099](http://localhost:9099) | Agent runtime |
| | | [http://localhost:9099/v1/models](http://localhost:9099/v1/models) | Registered agents (`iazi-valuation-expert`) |
| **litellm** | 4000 | [http://localhost:4000](http://localhost:4000) | LLM proxy |
| | | `POST http://localhost:4000/v1/chat/completions` | OpenAI-compatible chat |
| **servicemodelr** | 8001 | [http://localhost:8001/docs](http://localhost:8001/docs) | `POST /price`, `POST /rent` |
| | | [http://localhost:8001/health](http://localhost:8001/health) | Health |
| **addressvalidation** | 8002 | [http://localhost:8002/docs](http://localhost:8002/docs) | `POST /validate` |
| | | [http://localhost:8002/health](http://localhost:8002/health) | Health |

Internal Docker DNS (container-to-container): `http://litellm:4000`, `http://pipelines:9099`, `http://servicemodelr:8000`, `http://addressvalidation:8000`.

## Test the IAZI agent

1. Open [http://localhost:3000](http://localhost:3000)
2. Model: **Agent: IAZI Valuation Expert**
3. Example: *What is the estimated purchase price for a 3-room, 100 m² apartment in Bern (BE)?*

More prompts: [../README.md](../README.md#example-prompts-iazi-valuation-expert).

## Configuration

| Source | Used for |
|--------|----------|
| `../../../.env` (repo root) | `NVIDIA_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY` → LiteLLM container |
| `litellm/config.yaml` | Model list (bind-mounted) |
| `agents/` | IAZI agent + future agents (bind-mounted to Pipelines) |

AppHost defaults: `LITELLM_MASTER_KEY=sk-litellm-local`, `PIPELINES_API_KEY=0p3n-w3bu!` (override via env or `.env`).

## Stop

`Ctrl+C` in the terminal running the AppHost, or stop from the Aspire Dashboard.
