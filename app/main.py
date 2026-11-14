from fastapi import FastAPI

from .database import Base, engine
from . import models  # noqa: F401  (registers the Link table with Base)
from .routes import router

Base.metadata.create_all(engine)

app = FastAPI(title="URL Shortener")
app.include_router(router)