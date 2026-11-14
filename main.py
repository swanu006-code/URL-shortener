from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
import secrets
import string
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, select, String, DateTime
from sqlalchemy.orm import (
    sessionmaker, DeclarativeBase, Mapped, mapped_column, Session
)

# --- Database setup ---
DATABASE_URL = "sqlite:///./shortener.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
        DateTime, default=lambda: datetime.now(timezone.utc)
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


# --- API ---
app = FastAPI(title="URL Shortener")


class LinkCreate(BaseModel):
    url: HttpUrl


@app.post("/shorten")
def shorten(payload: LinkCreate, db: Session = Depends(get_db)):
    code = generate_code()
    while db.scalar(select(Link).where(Link.code == code)):
        code = generate_code()  # collision: try again

    link = Link(code=code, original_url=str(payload.url))
    db.add(link)
    db.commit()

    return {"code": code, "short_url": f"http://localhost:8000/{code}"}
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
    }


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    link.clicks += 1
    db.commit()
    return RedirectResponse(link.original_url, status_code=302)