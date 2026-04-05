# LLM innovation hub

Small Python utilities to call several OpenAI-compatible chat APIs from one place and run shared test prompts against each backend.

## APIs exercised in this project

The default `config/APIs.json` is set up for three hosted APIs (you can add more provider blocks as needed):

| Provider | Service | Base URL (default in config) | Where to get an API key |
|----------|---------|--------------------------------|-------------------------|
| **nvidia** | NVIDIA NIM (Build) | `https://integrate.api.nvidia.com/v1` | [NVIDIA Build — explore / discover](https://build.nvidia.com/explore/discover) |
| **groq** | Groq | `https://api.groq.com/openai/v1` | [Groq Console — API keys](https://console.groq.com/keys) |
| **mistral** | Mistral AI | `https://api.mistral.ai/v1` | [Mistral — API keys](https://console.mistral.ai/api-keys/) |

All three use the same HTTP shape as OpenAI’s **chat completions** API; this repo uses the official [`openai`](https://pypi.org/project/openai/) Python package with a per-provider `base_url` and `api_key`.

## Quick start

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Put API keys in a project-root **`.env`** file (recommended) or set them in `config/APIs.json` under each provider’s `api_key`. When `api_key` is empty in JSON, the code reads **`{PROVIDER}_API_KEY`** (for example `GROQ_API_KEY`, `NVIDIA_API_KEY`, `MISTRAL_API_KEY`). Adjust `model`, `base_url`, and generation settings (`max_tokens`, `temperature`, `top_p`, `timeout_seconds`, `connect_timeout_seconds`, `max_retries`) in `config/APIs.json` as needed.

3. Edit `prompts.json` with the test cases you care about (`case`, `context`, `prompt` per entry).

4. From the project root, run the driver (see **examples** below).

### `test_basic_prompts.py` — examples

Run all configured providers against every case in `prompts.json`:

```bash
python test_basic_prompts.py
```

Run only one provider (name must match a key in `config/APIs.json`):

```bash
python test_basic_prompts.py --api groq
```

Run several providers (repeat the flag or use a comma-separated list):

```bash
python test_basic_prompts.py --api groq --api mistral
python test_basic_prompts.py --api groq,mistral
```

Verbose stderr logs (request settings, `chat.completions.create` arguments, response id / usage / finish reason). Use the flag alone, or pass `true` / `false`:

```bash
python test_basic_prompts.py --verbose
python test_basic_prompts.py --api groq --verbose true
python test_basic_prompts.py --api groq --verbose false
```

Combine filtering and verbose mode:

```bash
python test_basic_prompts.py --api groq,mistral --verbose
```

**Flags**

| Flag | Description |
|------|-------------|
| `--api NAME` | Limit to one or more providers (default: all). Unknown names exit with an error listing valid providers. |
| `--verbose` | Detailed logs on stderr; same as `--verbose true`. |

**Errors**

If a call fails, the script prints **`ERROR: <provider>: <reason>`** on stderr, optionally a full traceback when `--verbose` is on, then continues with the next provider and prompt. A short “skipped” line is still printed on stdout for that attempt.

## Layout

- `.env` — optional project-root file for `{PROVIDER}_API_KEY` values (see `.gitignore`).
- `config/APIs.json` — credentials and parameters per provider (listed in `.gitignore` so keys are less likely to be committed; keep a private copy or restore fields after clone).
- `prompts.json` — test prompt cases.
- `test_basic_prompts.py` — driver script.
- `utils/` — `config_loader`, `prompt_loader`, and `chat_provider` (`complete_chat`).

## Requirements

See `requirements.txt` (`openai`, `python-dotenv`).
