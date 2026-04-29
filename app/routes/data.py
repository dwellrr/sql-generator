from fastapi import APIRouter, UploadFile
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

from fastapi.responses import PlainTextResponse

from app.core.data_manager import data_manager

router = APIRouter()


@router.post("/upload")
async def upload_data(file: UploadFile):
    content = (await file.read()).decode("utf-8")
    data_manager.upload(content)
    return {"status": "success", "message": "Data uploaded successfully"}


@router.post("/read")
def read_data():
    content = data_manager.load_from_disk()
    return PlainTextResponse(content=content)


@router.post("/update")
def update_data_from_db(db: Session = Depends(get_db)):
    data_manager.generate_from_db_to_file(db)
    return PlainTextResponse("Data updated sucessfully")
