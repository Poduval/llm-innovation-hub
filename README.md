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

2. **Secrets:** Put API keys in a project-root **`.env`** file (recommended, and **gitignored**), or set `api_key` inside each provider in `config/APIs.json`.  
   When `api_key` is empty in JSON, the code reads **`{PROVIDER}_API_KEY`** (e.g. `GROQ_API_KEY`, `NVIDIA_API_KEY`, `MISTRAL_API_KEY`). You can override the env var name per provider with **`api_key_env`** in that provider’s block.

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
```

Run **one** provider (name must match a key in `config/APIs.json`):

```bash
python test_basic_prompts.py --api groq
```

Run **several** providers (repeat the flag or use a comma-separated list):

```bash
python test_basic_prompts.py --api groq --api mistral
python test_basic_prompts.py --api groq,mistral
```

Run **specific** prompt cases by **`case`** id from `prompts.json` (comma-separated; order is preserved; duplicates are collapsed):

```bash
python test_basic_prompts.py --case 1
python test_basic_prompts.py --case 1,2
python test_basic_prompts.py --case 2,1 --api groq
```

**Verbose** stderr logs (provider settings redacted, `chat.completions.create` kwargs, response id / model / `finish_reason` / `usage`). Use the flag alone, or `true` / `false`:

```bash
python test_basic_prompts.py --verbose
python test_basic_prompts.py --api groq --verbose true
python test_basic_prompts.py --api groq --verbose false
```

Combine filters:

```bash
python test_basic_prompts.py --api groq,mistral --case 1,3 --verbose
```

### Flags

| Flag | Description |
|------|-------------|
| `--api NAME` | Limit to one or more providers (default: all). Unknown names exit with an error listing valid providers. |
| `--case IDS` | Comma-separated `case` values from `prompts.json` (default: all cases). Unknown ids exit with an error listing known ids. |
| `--verbose` | Detailed logs on stderr; same as `--verbose true`. |

### Output

The driver prints a **structured terminal report** (implemented in `utils/terminal_report.py`): run header (case count, providers, timestamp), per-case sections (**PROMPT** / **RESPONSES**), status lines (**✓ OK** / **✗ FAIL** or ASCII fallbacks), timings, and word-wrapped text. Set **`NO_COLOR=1`** to disable ANSI colors.

### Errors

If a call fails, the script prints **`ERROR: <provider>: <reason>`** on stderr, a full traceback when **`--verbose`** is on, then continues. A short “skipped” line is still printed on stdout for that attempt.

## Layout

| Path | Role |
|------|------|
| `.env` | Optional secrets (`{PROVIDER}_API_KEY`). **Not committed** (see `.gitignore`). |
| `config/APIs.json` | Provider endpoints and generation defaults; safe to commit if keys stay empty. |
| `prompts.json` | Test cases (`case`, `context`, `prompt`). |
| `test_basic_prompts.py` | CLI driver: loads config/prompts, filters by `--api` / `--case`, calls APIs, prints the report. |
| `utils/config_loader.py` | Loads `config/APIs.json` (cached), lists providers, resolves a provider block; loads `.env` via `python-dotenv`. |
| `utils/prompt_loader.py` | Loads `prompts.json`. |
| `utils/chat_provider.py` | `complete_chat(prompt, api, verbose=...)` — OpenAI client + key resolution + optional verbose logging. |
| `utils/terminal_report.py` | ANSI styling, rules, wrapping, run/case/response sections for stdout. |

## Requirements

See **`requirements.txt`**: `openai`, `python-dotenv` (and `httpx` as a dependency of `openai`).
