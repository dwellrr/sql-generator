from fastapi import FastAPI
from pydantic import BaseModel
from llm import ask_llm

app = FastAPI(title="NL SQL Query API")


class QuestionRequest(BaseModel):
    question: str
    language: str = "english"


@app.get("/")
def root():
    return {"message": "hello world"}


@app.get("/ping")
def ping():
    return {"pong": True}


@app.post("/ask")
def ask(req: QuestionRequest):
    sql = ask_llm(req.question)
    return {"sql": sql}
