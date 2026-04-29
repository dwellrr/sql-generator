from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService

from app.core.db import get_db

router = APIRouter()


def get_llm_service(db: Session = Depends(get_db)) -> LLMService:
    return LLMService(db=db)


@router.post("/generate-sql", response_class=PlainTextResponse)
def ask(
    question: str,
    max_retries: int = 3,
    service: LLMService = Depends(get_llm_service),
) -> str:
    return service.generate_sql(question, max_retries=max_retries)
