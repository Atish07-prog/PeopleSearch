from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.person import Person


class HealthResponse(BaseModel):
    status: Literal["ok"]


class PersonSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        min_length=1,
        max_length=200,
        description="Person name search query.",
    )
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized


class PersonSearchResponse(BaseModel):
    query: str
    results: list[Person]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
