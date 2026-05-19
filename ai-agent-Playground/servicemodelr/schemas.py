from pydantic import BaseModel, Field


class EstimationRequest(BaseModel):
    ortId: int = Field(..., ge=1, le=26, description="Canton town id (1–26)")
    roomNb: int = Field(..., ge=1, le=5, description="Number of rooms")
    surfaceLiving: float = Field(
        ..., ge=80, le=120, description="Living surface in m²"
    )


class EstimationResponse(BaseModel):
    value: float
