from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_schema_service
from app.core.db import get_db
from app.schemas.responses import StatusResponse
from app.services.schema_service import SchemaService

router = APIRouter()


@router.post("/upload", response_model=StatusResponse)
async def upload_schema(
    file: UploadFile,
    service: SchemaService = Depends(get_schema_service),
):
    content = (await file.read()).decode("utf-8")
    service.upload(content)
    return {"status": "success", "message": "Schema uploaded successfully"}


@router.post("/read", response_class=PlainTextResponse)
def read_schema(service: SchemaService = Depends(get_schema_service)):
    return service.read()


@router.post("/update", response_class=PlainTextResponse)
def update_schema_from_db(
    db: Session = Depends(get_db),
    service: SchemaService = Depends(get_schema_service),
):
    service.update_from_db(db)
    return PlainTextResponse("Schema updated sucessfully")
