import os
from dotenv import load_dotenv
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import create_engine, select, String, DateTime
from sqlalchemy.orm import (
    sessionmaker, DeclarativeBase, Mapped, mapped_column, Session
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shortener.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    original_url: Mapped[str] = mapped_column(String)
    clicks: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Helpers ---
def generate_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def is_expired(link: Link) -> bool:
    if link.expires_at is None:
        return False
    expires = link.expires_at
    if expires.tzinfo is None:  # SQLite returns naive datetimes
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires


# --- API ---
app = FastAPI(title="URL Shortener")

RESERVED = {"docs", "redoc", "stats", "shorten", "openapi"}


class LinkCreate(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9]{3,10}$")
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


@app.post("/shorten")
def shorten(payload: LinkCreate, db: Session = Depends(get_db)):
    if payload.alias:
        if payload.alias.lower() in RESERVED:
            raise HTTPException(status_code=400, detail="That alias is reserved")
        if db.scalar(select(Link).where(Link.code == payload.alias)):
            raise HTTPException(status_code=409, detail="Alias already taken")
        code = payload.alias
    else:
        code = generate_code()
        while db.scalar(select(Link).where(Link.code == code)):
            code = generate_code()

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    link = Link(code=code, original_url=str(payload.url), expires_at=expires_at)
    db.add(link)
    db.commit()

    return {
        "code": code,
        "short_url": f"http://localhost:8000/{code}",
        "expires_at": expires_at,
    }


@app.get("/stats/{code}")
def stats(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return {
        "code": link.code,
        "original_url": link.original_url,
        "clicks": link.clicks,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    if is_expired(link):
        raise HTTPException(status_code=410, detail="This link has expired")
    link.clicks += 1
    db.commit()
    return RedirectResponse(link.original_url, status_code=302)