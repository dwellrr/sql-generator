from fastapi import APIRouter, UploadFile
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

from fastapi.responses import PlainTextResponse

from app.core.schema_manager import schema_manager

router = APIRouter()


@router.post("/upload")
async def upload_schema(file: UploadFile):
    content = (await file.read()).decode("utf-8")
    schema_manager.upload(content)
    return {"status": "success", "message": "Schema uploaded successfully"}


@router.post("/read")
def read_schema():
    content = schema_manager.get_schema()
    return PlainTextResponse(content=content)


@router.post("/update")
def update_schema_from_db(db: Session = Depends(get_db)):
    schema_manager.generate_from_db_to_file(db)
    return PlainTextResponse("Schema updated sucessfully")
