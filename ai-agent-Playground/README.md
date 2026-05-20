# AI agent playground

Mock Swiss property APIs plus **Open WebUI**, **LiteLLM**, and **Agent: IAZI Valuation Expert**. Parent repo overview: [../README.md](../README.md).

## Quick start

```bash
docker compose up --build
```

1. Open [http://localhost:3000](http://localhost:3000)
2. **New chat** → model **Agent: IAZI Valuation Expert** (`iazi-valuation-expert`)
3. Paste a prompt from the table below

Provider keys: repo-root [`.env`](../.env). Optional: [`.env.example`](.env.example) (`LITELLM_MASTER_KEY`, `PIPELINES_API_KEY`, `WEBUI_SECRET_KEY`).

```bash
docker compose ps          # all five services Up
docker compose down        # stop
```

## Example prompts (IAZI Valuation Expert)

| # | Prompt |
|---|--------|
| 1 | What is the estimated **purchase price** for a **3-room, 100 m²** apartment in **Bern (BE)**? |
| 2 | Estimate the **monthly rent** for a **4-room, 110 m²** flat in **Zurich (ZH)**. |
| 3 | How much would a **5-room, 120 m²** home in **Geneva (GE)** cost to buy? |
| 4 | What is the rent for a place in **Ticino (TI)**? *(agent should default to 3 rooms, 100 m²)* |
| 5 | Compare **purchase price** for **3 rooms, 100 m²** in **ZH** vs **VD**. |
| 6 | Validate canton **XX** and give me a price in Bern. *(invalid canton)* |
| 7 | I have **ortId 12**, **3 rooms**, **90 m²** — what is the purchase price? |
| 8 | Give me both **price and monthly rent** for **3 rooms, 100 m²** in **Basel-Stadt (BS)**. |

Expected: tool calls to validate canton and estimate price/rent, then a short answer in **CHF** with assumptions stated.

Agent behavior: [`agents/AGENTS.md`](agents/AGENTS.md) · implementation: [`agents/IAZI.Valuation.Agent.py`](agents/IAZI.Valuation.Agent.py)

## URLs

| Service | URL |
|---------|-----|
| **Open WebUI** | [http://localhost:3000](http://localhost:3000) |
| Agent registered? | [http://localhost:9099/v1/models](http://localhost:9099/v1/models) |
| LiteLLM | [http://localhost:4000](http://localhost:4000) |
| ServiceModelR | [http://localhost:8001/docs](http://localhost:8001/docs) |
| AddressValidation | [http://localhost:8002/docs](http://localhost:8002/docs) |

## Mock APIs (summary)

**AddressValidation** — `POST /validate` with `{"canton":"BE"}` → `{"ortId":2}`  
Canton codes: `ZH`, `BE`, `LU`, … `JU` (26 cantons).

**ServiceModelR** — `POST /price` or `POST /rent` with:

```json
{ "ortId": 2, "roomNb": 3, "surfaceLiving": 100 }
```

→ `{"value": <number>}` (CHF; formula uses fixed per-`ortId` location factor + room/surface multipliers).

Constraints: `ortId` 1–26, `roomNb` 1–5, `surfaceLiving` 80–120.

```bash
curl -s -X POST http://localhost:8002/validate -H "Content-Type: application/json" -d '{"canton":"BE"}'
curl -s -X POST http://localhost:8001/price -H "Content-Type: application/json" -d '{"ortId":2,"roomNb":3,"surfaceLiving":100}'
```

## Agents folder

```
agents/
  AGENTS.md                    # behavior per agent
  IAZI.Valuation.Agent.py      # Pipeline loaded by Pipelines container
  lib/runtime.py               # shared tool loop
```

Mounted as `/app/pipelines` in the **pipelines** service. Add new agents as `{Vendor}.{Capability}.Agent.py` + a section in `AGENTS.md`.

Tune LLM model/URLs: **Admin → Pipelines → IAZI.Valuation.Agent → Valves**.

## Aspire (full stack + dashboard)

Orchestrates **all** services (Open WebUI, Pipelines, LiteLLM, both mock APIs) and shows them in the **Aspire Dashboard** with logs, traces, and endpoint links.

```bash
cd aspire/AppHost
dotnet run --launch-profile http
```

Use the login URL printed in the terminal → **Resources** → open endpoints. See **[aspire/README.md](aspire/README.md)** for the full container/URL table and prerequisites.

| Resource | URL |
|----------|-----|
| Aspire Dashboard | `http://localhost:15152` (from console) |
| Open WebUI | [http://localhost:3000](http://localhost:3000) |
| Pipelines | [http://localhost:9099/v1/models](http://localhost:9099/v1/models) |
| LiteLLM | [http://localhost:4000](http://localhost:4000) |
| ServiceModelR | [http://localhost:8001/docs](http://localhost:8001/docs) |
| AddressValidation | [http://localhost:8002/docs](http://localhost:8002/docs) |

Do not run Aspire and `docker compose` at the same time.

## Troubleshooting

| Issue | Action |
|-------|--------|
| Blank :3000 or :9099 | `docker compose ps`; `docker compose up -d`; first WebUI start may take 1–2 min |
| `pipelines` Restarting | `docker logs pipelines --tail 30`; `docker compose restart pipelines` |
| Agent missing in UI | Check [models](http://localhost:9099/v1/models) for `iazi-valuation-expert`; restart pipelines + open-webui |
