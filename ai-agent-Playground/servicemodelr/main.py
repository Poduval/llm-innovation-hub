import logging

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from location_values import LOCATION_VALUES
from schemas import EstimationRequest, EstimationResponse
from telemetry import configure_telemetry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ServiceModelR", description="Real estate price and rent estimations")
tracer = configure_telemetry(app, service_name="servicemodelr")
log = logging.getLogger(__name__)


def _estimate(body: EstimationRequest, room_multiplier: int, surface_multiplier: int) -> float:
    with tracer.start_as_current_span("calculate_estimation") as span:
        span.set_attribute("realestate.ort_id", body.ortId)
        span.set_attribute("realestate.room_nb", body.roomNb)
        span.set_attribute("realestate.surface_living", body.surfaceLiving)
        span.set_attribute("realestate.room_multiplier", room_multiplier)
        span.set_attribute("realestate.surface_multiplier", surface_multiplier)

        location_value = LOCATION_VALUES.get(body.ortId)
        if location_value is None:
            span.set_status(Status(StatusCode.ERROR, "Invalid ortId"))
            raise HTTPException(status_code=400, detail="Invalid ortId")

        span.set_attribute("realestate.location_value", location_value)
        room_component = body.roomNb * room_multiplier
        surface_component = body.surfaceLiving * surface_multiplier
        value = location_value + room_component + surface_component

        span.set_attribute("realestate.room_component", room_component)
        span.set_attribute("realestate.surface_component", surface_component)
        span.set_attribute("realestate.estimated_value", value)
        log.info(
            "Estimation computed",
            extra={
                "ort_id": body.ortId,
                "room_nb": body.roomNb,
                "surface_living": body.surfaceLiving,
                "value": value,
            },
        )
        return value


@app.post("/price", response_model=EstimationResponse)
def estimate_price(body: EstimationRequest) -> EstimationResponse:
    with tracer.start_as_current_span("estimate_price") as span:
        span.set_attribute("estimation.type", "price")
        value = _estimate(body, room_multiplier=40_000, surface_multiplier=10_000)
        return EstimationResponse(value=value)


@app.post("/rent", response_model=EstimationResponse)
def estimate_rent(body: EstimationRequest) -> EstimationResponse:
    with tracer.start_as_current_span("estimate_rent") as span:
        span.set_attribute("estimation.type", "rent")
        value = _estimate(body, room_multiplier=40, surface_multiplier=1_000)
        return EstimationResponse(value=value)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
