import logging

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from cantons import CANTON_TO_ORT_ID, VALID_CANTONS
from schemas import CantonRequest, OrtIdResponse
from telemetry import configure_telemetry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AddressValidation", description="Validate Swiss canton and return ortId")
tracer = configure_telemetry(app, service_name="addressvalidation")
log = logging.getLogger(__name__)


@app.post("/validate", response_model=OrtIdResponse)
def validate_canton(body: CantonRequest) -> OrtIdResponse:
    with tracer.start_as_current_span("validate_canton") as span:
        code = body.canton.strip().upper()
        span.set_attribute("address.canton_input", body.canton)
        span.set_attribute("address.canton_normalized", code)

        if code not in VALID_CANTONS:
            span.set_status(Status(StatusCode.ERROR, "Invalid canton"))
            span.set_attribute("address.valid", False)
            log.warning("Invalid canton requested", extra={"canton": code})
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canton. Must be one of: {', '.join(sorted(VALID_CANTONS))}",
            )

        ort_id = CANTON_TO_ORT_ID[code]
        span.set_attribute("address.valid", True)
        span.set_attribute("address.ort_id", ort_id)
        log.info("Canton validated", extra={"canton": code, "ort_id": ort_id})
        return OrtIdResponse(ortId=ort_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
