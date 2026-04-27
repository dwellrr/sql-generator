import os
import re
import logging
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import sqlglot
from fastapi import HTTPException
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

SCHEMA_FILE = Path(__file__).parent.parent.parent / "schema.sql"

router = APIRouter()

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_HOST"),
    api_key=os.getenv("LLM_API_KEY"),
)


@router.post("/ask")
def ask_llm(question: str) -> dict:
    schema = SCHEMA_FILE.read_text() if SCHEMA_FILE.exists() else None

    system_prompt = """Return ONLY a valid SQL query. IMPORTANT: No explanation at all. 
        If the question cannot be answered with the schema, 
        start your response with ERROR: followed by a description of the issue."""
    if schema:
        system_prompt += f"""\n\nAdhere to this schema:\n{schema}\n
        IMPORTANT: You MUST only use tables and columns that exist in the schema above.
        Do NOT invent tables or columns that are not in the schema."""

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    logging.warning(system_prompt)
    sql = response.choices[0].message.content
    sql = clean_sql(sql)

    if sql.upper().startswith("ERROR:"):
        raise HTTPException(status_code=400, detail=sql[6:].strip())

    validate_sql(sql)
    return PlainTextResponse(content=sql)


def clean_sql(sql: str) -> str:
    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.replace("\n", " ")
    sql = re.sub(r"\s+", " ", sql)
    return sql.strip()


def is_valid_syntax(sql: str) -> bool:
    try:
        sqlglot.parse_one(sql, dialect="postgres")
        return True
    except sqlglot.errors.ParseError:
        return False


def validate_sql(sql: str):
    if not is_valid_syntax(sql):
        raise HTTPException(
            status_code=400, detail=f"Generated query has invalid SQL syntax: {sql}"
        )
