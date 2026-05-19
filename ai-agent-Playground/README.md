# Swiss Real Estate API Services

> When this folder lives inside **llm-innovation-hub**, see the [root README](../README.md) for the full tech stack, monorepo layout, ports, and how paths resolve from the parent repo.

Two independent FastAPI services, each with its own Docker container.

## Services

| Service | Port (host) | Endpoints |
|---------|-------------|-----------|
| **ServiceModelR** | 8001 | `POST /price`, `POST /rent` |
| **AddressValidation** | 8002 | `POST /validate` |

### ServiceModelR

Estimates price or rent for any property type using:

```
value = location_value[ortId] + roomNb × room_multiplier + surfaceLiving × surface_multiplier
```

| Field | Constraints |
|-------|-------------|
| `ortId` | 1–26 (canton id) |
| `roomNb` | integer 1–5 |
| `surfaceLiving` | 80–120 m² |

| Endpoint | `room_multiplier` | `surface_multiplier` |
|----------|-------------------|----------------------|
| `/price` | 40,000 | 10,000 |
| `/rent` | 40 | 1,000 |

`location_value` is a fixed random integer (100–1000) per `ortId`, set at startup.

**Request**

```json
{ "ortId": 2, "roomNb": 3, "surfaceLiving": 80 }
```

**Response**

```json
{ "value": 520000 }
```

### AddressValidation

Maps a Swiss canton code to `ortId` (1–26).

**Request**

```json
{ "canton": "ZH" }
```

**Response**

```json
{ "ortId": 1 }
```

Valid canton codes: `ZH`, `BE`, `LU`, `UR`, `SZ`, `OW`, `NW`, `GL`, `ZG`, `FR`, `SO`, `BS`, `BL`, `SH`, `AR`, `AI`, `SG`, `GR`, `AG`, `TG`, `TI`, `VD`, `VS`, `NE`, `GE`, `JU`.

## Run locally

```bash
# ServiceModelR
cd servicemodelr && pip install -r requirements.txt && uvicorn main:app --reload --port 8001

# AddressValidation
cd addressvalidation && pip install -r requirements.txt && uvicorn main:app --reload --port 8002
```

## Run with Docker Compose

```bash
docker compose up --build
```

- ServiceModelR: http://localhost:8001/docs  
- AddressValidation: http://localhost:8002/docs  

## Run with .NET Aspire (recommended for dev)

Aspire orchestrates both containers, opens the **Aspire Dashboard** (logs, resources, traces), and exposes the same API ports.

```bash
cd aspire/AppHost
dotnet run --launch-profile http
```

On startup, the console prints a dashboard login URL, for example:

`http://localhost:15152/login?t=<token>`

Open that link to use the dashboard. From there you can:

- See **servicemodelr** and **addressvalidation** under Resources
- Stream **console logs** for each container
- Open each service’s HTTP endpoint (ports **8001** and **8002**)
- View **Traces**, **Metrics**, and **Structured logs** exported via OpenTelemetry (OTLP)

Both Python services instrument FastAPI automatically and add custom spans (e.g. `calculate_estimation`, `validate_canton`) with domain attributes such as `realestate.ort_id` and `address.canton_normalized`.

Stop the stack with `Ctrl+C` in the terminal running the AppHost.

> **Note:** Do not run `docker compose up` at the same time — both use ports 8001 and 8002.

### Alternative: Aspire CLI

If you install the [.NET 9 SDK](https://dotnet.microsoft.com/download) (AppHost targets **net9.0**), you can also use:

```bash
cd aspire
aspire run
```

The AppHost project lives at `aspire/AppHost/AppHost.csproj`.

## Example flow

1. Resolve canton → `ortId` via AddressValidation.
2. Pass `ortId`, `roomNb`, and `surfaceLiving` to ServiceModelR `/price` or `/rent`.

```bash
curl -s -X POST http://localhost:8002/validate -H "Content-Type: application/json" -d '{"canton":"BE"}'
curl -s -X POST http://localhost:8001/price -H "Content-Type: application/json" -d '{"ortId":2,"roomNb":3,"surfaceLiving":80}'
```
