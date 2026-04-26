from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    EmptySchemaError,
    InvalidSQLError,
    SchemaError,
    SchemaNotLoadedError,
    NoSchemaError,
)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(EmptySchemaError)
    async def empty_schema_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(InvalidSQLError)
    async def invalid_sql_handler(request, exc):
        return JSONResponse(status_code=422, content={"detail": exc.detail})

    @app.exception_handler(SchemaError)
    async def schema_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SchemaNotLoadedError)
    async def schema_no_loaded_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NoSchemaError)
    async def no_schema_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
