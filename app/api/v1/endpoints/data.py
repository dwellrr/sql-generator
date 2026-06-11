from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_data_service
from app.core.db import get_db
from app.schemas.responses import StatusResponse
from app.services.data_service import DataService

router = APIRouter()


@router.post("/upload", response_model=StatusResponse)
async def upload_data(
    file: UploadFile,
    service: DataService = Depends(get_data_service),
):
    content = (await file.read()).decode("utf-8")
    service.upload(content)
    return {"status": "success", "message": "Data uploaded successfully"}


@router.post("/read", response_class=PlainTextResponse)
def read_data(service: DataService = Depends(get_data_service)):
    return service.read()


@router.post("/update", response_class=PlainTextResponse)
def update_data_from_db(
    db: Session = Depends(get_db),
    service: DataService = Depends(get_data_service),
):
    service.update_from_db(db)
    return PlainTextResponse("Data updated sucessfully")
