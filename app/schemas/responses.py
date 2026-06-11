from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str
    message: str


class QueryResultsResponse(BaseModel):
    results: list[dict]
