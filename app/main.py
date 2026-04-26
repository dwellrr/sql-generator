from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
from app.routes import db_api, llm, schema_manager
from app.routes.db_api import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logging.error(f"Couldn't connect to the database! Exception: {e}")
    yield


app = FastAPI(title="NL SQL Query API", lifespan=lifespan)

app.include_router(llm.router, prefix="/query", tags=["NL to SQL"])
app.include_router(db_api.router, prefix="/db", tags=["Database operations"])
app.include_router(schema_manager.router, prefix="/schema", tags=["Schema operations"])


class QuestionRequest(BaseModel):
    question: str
    language: str = "english"


@app.get("/ping")
def ping():
    return {"pong": True}
