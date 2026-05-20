# LLM innovation hub

Two independent parts:

1. **LLM prompt comparison** (repo root) — same prompts across NVIDIA NIM, Groq, and Mistral via `test_basic_prompts.py`.
2. **`ai-agent-playground/`** — mock Swiss property APIs, **LiteLLM**, **Open WebUI**, and **Agent: IAZI Valuation Expert**.

No shared code between them. API keys for LLMs live in repo-root `.env` (see `.env.example`).

---

## Quick start — IAZI agent (Open WebUI)

```bash
cd ai-agent-playground
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000) → **New chat** → model **Agent: IAZI Valuation Expert** (`iazi-valuation-expert`).

Confirm the stack is up: `docker compose ps` (all services should be **Up**).

### Example prompts to test the agent

Copy any of these into the chat. The agent should call **AddressValidation** and **ServiceModelR** tools and answer in CHF.

| # | Prompt | What it exercises |
|---|--------|-------------------|
| 1 | What is the estimated **purchase price** for a **3-room, 100 m²** apartment in **Bern (BE)**? | Canton → `ortId`, then `/price` |
| 2 | Estimate the **monthly rent** for a **4-room, 110 m²** flat in **Zurich (ZH)**. | Canton validation + `/rent` |
| 3 | How much would a **5-room, 120 m²** home in **Geneva (GE)** cost to buy? | Upper bounds on rooms/surface |
| 4 | What is the rent for a place in **Ticino (TI)**? | Defaults (3 rooms, 100 m²) when details omitted |
| 5 | Compare **purchase price** for the same property (**3 rooms, 100 m²**) in **ZH** vs **VD**. | Two canton lookups + two price calls |
| 6 | Validate canton **XX** and give me a price in Bern. | Invalid canton error handling |
| 7 | I have **ortId 12**, **3 rooms**, **90 m²** — what is the purchase price? | Skips canton step when `ortId` given |
| 8 | Give me both **price and monthly rent** for a **3-room, 100 m²** apartment in **Basel-Stadt (BS)**. | Price + rent in one thread |

More behavior rules: [`ai-agent-playground/agents/AGENTS.md`](ai-agent-playground/agents/AGENTS.md). Playground details: [`ai-agent-playground/README.md`](ai-agent-playground/README.md).

### Service URLs (Docker Compose)

| Service | URL |
|---------|-----|
| **Open WebUI** (chat) | [http://localhost:3000](http://localhost:3000) |
| Pipelines / agents | [http://localhost:9099/v1/models](http://localhost:9099/v1/models) |
| LiteLLM | [http://localhost:4000](http://localhost:4000) |
| ServiceModelR API | [http://localhost:8001/docs](http://localhost:8001/docs) |
| AddressValidation API | [http://localhost:8002/docs](http://localhost:8002/docs) |

---

## Part 1 — LLM prompt comparison

Runs prompts from `prompts.json` against every provider in `config/APIs.json`.

```bash
cp .env.example .env   # add NVIDIA_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python test_basic_prompts.py
python test_basic_prompts.py --api groq --case 1
```

| Provider | Env variable |
|----------|----------------|
| `nvidia` | `NVIDIA_API_KEY` |
| `groq` | `GROQ_API_KEY` |
| `mistral` | `MISTRAL_API_KEY` |

```python
from utils.chat_provider import complete_chat
text = complete_chat("Say hello.", "groq")
```

---

## Part 2 — `ai-agent-playground/`

Mock flow: **canton → `ortId` → price or rent**. Details: **[`ai-agent-playground/README.md`](ai-agent-playground/README.md)**.

```bash
cd ai-agent-playground
docker compose up --build    # all services (see URL table above)
```

### Aspire (full stack + dashboard)

Same containers as Compose, plus the **Aspire Dashboard** (resources, logs, traces, endpoint links):

```bash
cd ai-agent-playground/aspire/AppHost
dotnet run --launch-profile http
```

Open the dashboard URL from the console (e.g. [http://localhost:15152](http://localhost:15152)). Chat UI: [http://localhost:3000](http://localhost:3000). Full container/endpoint table: **[`ai-agent-playground/aspire/README.md`](ai-agent-playground/aspire/README.md)**.

Do not run Aspire and `docker compose` together (ports 3000, 4000, 8001, 8002, 9099).

---

## Layout

```text
.
├── config/APIs.json, prompts.json, test_basic_prompts.py, utils/
└── ai-agent-playground/
    ├── docker-compose.yml, agents/, litellm/, open-webui/
    ├── servicemodelr/          # POST /price, /rent
    ├── addressvalidation/      # POST /validate
    └── aspire/                 # AppHost + aspire/README.md (full stack in dashboard)
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Empty page on :3000 or :9099 | `docker compose ps` — start missing services; `docker logs pipelines --tail 30` |
| Agent not in model list | [http://localhost:9099/v1/models](http://localhost:9099/v1/models) should list `iazi-valuation-expert`; then `docker compose restart pipelines open-webui` |
| `No API key for "groq"` | Fill repo-root `.env` for LLM comparison |
| Port in use | Stop duplicate Compose/Aspire or free 3000/4000/8001/8002/9099 |
