from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["bluesentra-api"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["dev"])


class ReadinessResponse(BaseModel):
    status: str = Field(..., examples=["ready"])
    database: str = Field(..., examples=["connected"])
