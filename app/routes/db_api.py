import os

from dotenv import load_dotenv
from fastapi import APIRouter
from sqlalchemy import create_engine, text

router = APIRouter()

load_dotenv()

engine = create_engine(os.getenv("DB_URL"), echo=True)


@router.post("/runquery")
def run_query(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]
