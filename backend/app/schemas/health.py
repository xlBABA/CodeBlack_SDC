"""Health schema per contracts/openapi.yaml#/components/schemas/Health."""
from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str
    version: str
    dependencies: dict[str, str] = Field(default_factory=dict)
