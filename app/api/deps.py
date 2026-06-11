from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.data_service import DataService, data_service
from app.services.dump_service import DumpService, dump_service
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.services.schema_service import SchemaService, schema_service
from app.services.verification_service import VerificationService


def get_llm_service(db: Session = Depends(get_db)) -> LLMService:
    return LLMService(db=db)


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    return QueryService(db=db)


def get_verification_service(db: Session = Depends(get_db)) -> VerificationService:
    return VerificationService(db=db)


def get_schema_service() -> SchemaService:
    return schema_service


def get_data_service() -> DataService:
    return data_service


def get_dump_service() -> DumpService:
    return dump_service
