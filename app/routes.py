import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Link
from .schemas import LinkCreate
from .utils import generate_code, is_expired

router = APIRouter()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
RESERVED = {"docs", "redoc", "stats", "shorten", "openapi"}


@router.post("/shorten")
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
        "short_url": f"{BASE_URL}/{code}",
        "expires_at": expires_at,
    }


@router.get("/stats/{code}")
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


@router.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    if is_expired(link):
        raise HTTPException(status_code=410, detail="This link has expired")
    link.clicks += 1
    db.commit()
    return RedirectResponse(link.original_url, status_code=302)