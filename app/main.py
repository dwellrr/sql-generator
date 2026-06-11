from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.db import engine
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logging.error(f"Couldn't connect to the database! Exception: {e}")
    yield


app = FastAPI(title="NL SQL Query API", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(api_router)
