# Agents

| File | Open WebUI name | Model id |
|------|-----------------|----------|
| `IAZI.Valuation.Agent.py` | **Agent: IAZI Valuation Expert** | `iazi-valuation-expert` |

- **Behavior:** [`AGENTS.md`](AGENTS.md) (loaded as system prompt)
- **Example prompts:** [../README.md](../README.md#example-prompts-iazi-valuation-expert) and [root README](../../README.md#example-prompts-to-test-the-agent)
- **URLs:** [playground README](../README.md#urls)

Add agents: new `Vendor.Capability.Agent.py` + matching `## Agent: …` section in `AGENTS.md`, then `docker compose restart pipelines`.

The repo folder is `agents/`; Docker mounts it to the Pipelines runtime path `/app/pipelines`.
