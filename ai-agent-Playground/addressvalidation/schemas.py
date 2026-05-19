from pydantic import BaseModel, Field


class CantonRequest(BaseModel):
    canton: str = Field(..., min_length=2, max_length=2, description="Two-letter canton code")


class OrtIdResponse(BaseModel):
    ortId: int
