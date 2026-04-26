import logging
from fastapi import APIRouter, UploadFile
from pathlib import Path
import sqlglot
from fastapi import HTTPException
from fastapi.responses import PlainTextResponse

ROOT = Path(__file__).parent.parent.parent
SCHEMA_FILE = ROOT / "schema.sql"

router = APIRouter()


def is_valid_syntax(sql: str) -> bool:
    try:
        sqlglot.parse_one(sql, dialect="postgres")
        return True
    except sqlglot.errors.ParseError:
        return False


def verify_schema(sql: str):
    if not sql.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if not is_valid_syntax(sql):
        raise HTTPException(
            status_code=400, detail="Uploaded file has invalid SQL syntax"
        )


@router.post("/upload")
async def upload_schema(file: UploadFile):
    try:
        content = await file.read()
        sql = content.decode("utf-8")
    except Exception as e:
        logging.error(f"Could not read file: {e}")
        raise HTTPException(status_code=500, detail="Could not read uploaded file")

    verify_schema(sql)

    try:
        SCHEMA_FILE.write_text(sql)
    except Exception as e:
        logging.error(f"Could not write schema file: {e}")
        raise HTTPException(status_code=500, detail="Could not save schema file")

    return {"message": "Successfully saved the schema"}


@router.post("/read")
def read_schema():
    try:
        content = SCHEMA_FILE.read_text()
    except Exception as e:
        logging.error(f"Could not read file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not read the schema file. Are you sure you uploaded one?",
        )

    return PlainTextResponse(content=content)
