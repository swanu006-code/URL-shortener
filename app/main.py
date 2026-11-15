from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .database import Base, engine
from . import models  # noqa: F401  (registers the Link table with Base)
from .routes import router

Base.metadata.create_all(engine)

app = FastAPI(title="URL Shortener")
app.include_router(router)
@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/docs")