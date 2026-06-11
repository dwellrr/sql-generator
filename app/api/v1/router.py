from fastapi import APIRouter

from app.api.v1.endpoints import data, db, dump, health, llm, schema

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(llm.router, prefix="/query", tags=["NL to SQL"])
api_router.include_router(db.router, prefix="/db", tags=["Database operations"])
api_router.include_router(schema.router, prefix="/schema", tags=["Schema operations"])
api_router.include_router(data.router, prefix="/data", tags=["Data operations"])
api_router.include_router(dump.router, prefix="/dump", tags=["Dump operations"])
