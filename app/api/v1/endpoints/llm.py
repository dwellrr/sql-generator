from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.api.deps import get_llm_service
from app.services.llm_service import LLMService

router = APIRouter()


@router.post("/generate-sql", response_class=PlainTextResponse)
def ask(
    question: str,
    max_retries: int = 3,
    service: LLMService = Depends(get_llm_service),
) -> str:
    return service.generate_sql(question, max_retries=max_retries)
