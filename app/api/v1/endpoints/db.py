from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_data_service, get_query_service, get_schema_service
from app.core.db import get_db
from app.schemas.responses import QueryResultsResponse, StatusResponse
from app.services.data_service import DataService
from app.services.query_service import QueryService
from app.services.schema_service import SchemaService

router = APIRouter()


@router.get("/generate/schema", response_class=PlainTextResponse)
def get_current_schema(
    db: Session = Depends(get_db),
    service: SchemaService = Depends(get_schema_service),
):
    """Returns the current tables and columns in the DB."""
    return service.generate_from_db(db)


@router.post("/runquery", response_model=QueryResultsResponse)
def run_query(
    sql: str,
    service: QueryService = Depends(get_query_service),
):
    results = service.run_query(sql)
    return {"results": results}


@router.post("/apply/full-reset", response_model=StatusResponse)
def apply_schema_full_reset(
    db: Session = Depends(get_db),
    service: SchemaService = Depends(get_schema_service),
):
    service.apply_full_reset(db)
    return {
        "status": "success",
        "message": "Schema fully reset and reapplied",
    }


@router.post("/apply/incremental", response_model=StatusResponse)
def apply_schema_incremental(
    db: Session = Depends(get_db),
    service: SchemaService = Depends(get_schema_service),
):
    """
    Applies schema on top of the existing database.
    Uses IF NOT EXISTS — safe to run multiple times.
    schema SQL must use CREATE TABLE IF NOT EXISTS etc.
    """
    try:
        service.apply_incremental(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "message": "Schema applied incrementally"}


@router.post("/apply/full-reset-data")
def reset_and_apply_data(
    db: Session = Depends(get_db),
    service: DataService = Depends(get_data_service),
):
    service.reset_and_apply(db)


@router.post("/apply/incremental-data")
def apply_data_incremental(
    db: Session = Depends(get_db),
    service: DataService = Depends(get_data_service),
):
    service.apply_incremental(db)


@router.post("/validatequery", response_model=StatusResponse)
def validate_query_against_db(
    sql: str,
    service: QueryService = Depends(get_query_service),
):
    """
    Runs a query and rolls it back.
    This is needed to make sure a query is
    valid for running on the database
    """
    try:
        service.validate_query(sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "message": "The query can be applied"}
