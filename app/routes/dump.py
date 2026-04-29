from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

from fastapi.responses import PlainTextResponse

from app.core.dump_manager import dump_manager

router = APIRouter()


@router.post("/get-dump")
def get_data_from_db(db: Session = Depends(get_db)):
    result = dump_manager.generate_from_db()
    return PlainTextResponse(result)
