"""Keyword search API schemas."""

from pydantic import BaseModel, Field


class KeywordSearchRequest(BaseModel):
    """Request body for keyword search."""

    keyword: str = Field(
        min_length=1,
        max_length=200,
        description="Search keyword",
        examples=["dropshipping"],
    )
    country: str = Field(
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
        examples=["US", "FR", "DE"],
    )
    language: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 639-1 language code (optional)",
        examples=["en", "fr"],
    )
    limit: int = Field(
        default=1000,
        ge=1,
        le=5000,
        description="Maximum number of ads to fetch",
    )


class KeywordSearchResponse(BaseModel):
    """Response for keyword search."""

    scan_id: str = Field(description="Unique scan identifier (UUID)")
    keyword: str = Field(description="Searched keyword")
    country: str = Field(description="Country code used")
    ads_found: int = Field(description="Total number of ads found")
    pages_found: int = Field(description="Number of unique pages found")
    new_pages: int = Field(description="Number of pages not previously seen")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                    "keyword": "dropshipping",
                    "country": "US",
                    "ads_found": 150,
                    "pages_found": 45,
                    "new_pages": 12,
                }
            ]
        }
    }
