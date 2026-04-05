# LLM innovation hub

Small Python utilities to call several **OpenAI-compatible** chat APIs from one place and run shared test prompts against each backend for comparison.

## APIs exercised in this project

The checked-in `config/APIs.json` is set up for three hosted APIs (you can add more provider objects as needed):

| Provider | Service | Base URL (default in config) | Where to get an API key |
|----------|---------|------------------------------|-------------------------|
| **nvidia** | NVIDIA NIM (Build) | `https://integrate.api.nvidia.com/v1` | [NVIDIA Build — explore / discover](https://build.nvidia.com/explore/discover) |
| **groq** | Groq | `https://api.groq.com/openai/v1` | [Groq Console — API keys](https://console.groq.com/keys) |
| **mistral** | Mistral AI | `https://api.mistral.ai/v1` | [Mistral — API keys](https://console.mistral.ai/api-keys/) |

All three use the same HTTP shape as OpenAI’s **chat completions** API. This repo uses the official [`openai`](https://pypi.org/project/openai/) Python package with a per-provider `base_url` and API key. Timeouts use **`httpx`** (separate connect vs read limits) to avoid long hangs on bad networks.

## Quick start

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Secrets:** Copy **`.env.example`** to **`.env`** and fill in your keys (`.env` is **gitignored**):

   ```bash
   cp .env.example .env
   ```

   When `api_key` is empty in `config/APIs.json`, the app reads **`{PROVIDER}_API_KEY`** (e.g. `GROQ_API_KEY`, `NVIDIA_API_KEY`, `MISTRAL_API_KEY`). You can override the variable name per provider with **`api_key_env`** in that provider’s block. Alternatively, you may set `api_key` directly in JSON (avoid committing real keys).

3. **Config:** `config/APIs.json` is **tracked in git** as a template (URLs, models, `max_tokens`, `temperature`, `top_p`, `timeout_seconds`, `connect_timeout_seconds`, `max_retries`). **Do not commit real keys** in JSON; keep them in `.env` or a private override.

4. Edit **`prompts.json`** with the cases you care about. Each entry is an object with:
   - **`case`** — id used by `--case` (e.g. `"1"`, `"2"`);
   - **`context`** — short human-readable description (shown in the report);
   - **`prompt`** — the user message sent to every selected provider.

5. From the project root, run the driver (see **CLI examples** below).

## CLI — `test_basic_prompts.py`

### Examples

Run **all** providers against **all** cases:

```bash
python test_basic_prompts.py
python test_basic_prompts.py --api groq
python test_basic_prompts.py --help # check for further opetions
```

## Layout

Repository layout (create `.env` locally from `.env.example`; it is gitignored):

```text
.
├── .env.example              # API key template — safe to commit; copy to .env
├── .gitignore
├── README.md
├── config
│   └── APIs.json             # provider URLs, models, generation defaults (no real keys)
├── prompts.json              # test cases: case, context, prompt
├── requirements.txt
├── test_basic_prompts.py     # CLI: load config/prompts, --api / --case, run report
└── utils
    ├── __init__.py
    ├── chat_provider.py      # complete_chat(...): OpenAI client, keys, optional verbose log
    ├── config_loader.py      # APIs.json + python-dotenv
    ├── prompt_loader.py      # prompts.json
    └── terminal_report.py    # ANSI report sections for stdout
```

`.env` (real `{PROVIDER}_API_KEY` values) lives beside `.env.example` when you configure the project; it is not tracked.

## Requirements

See **`requirements.txt`**: `openai`, `python-dotenv` (and `httpx` as a dependency of `openai`).
