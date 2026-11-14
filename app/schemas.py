from pydantic import BaseModel, HttpUrl, Field


class LinkCreate(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9]{3,10}$")
    expires_in_days: int | None = Field(default=None, ge=1, le=365)