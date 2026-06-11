from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.api.deps import get_dump_service
from app.services.dump_service import DumpService

router = APIRouter()


@router.post("/get-dump", response_class=PlainTextResponse)
def get_data_from_db(service: DumpService = Depends(get_dump_service)):
    return service.get_dump()
