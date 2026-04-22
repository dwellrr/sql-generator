import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlglot
from fastapi import HTTPException

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_HOST"),
    api_key=os.getenv("LLM_API_KEY"),
)


def ask_llm(question: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": "Return ONLY a valid SQL query. Nothing else.",
            },
            {"role": "user", "content": question},
        ],
    )
    sql = response.choices[0].message.content.strip()
    validate_sql(sql)

    return sql


def is_valid_syntax(sql: str) -> bool:
    try:
        sqlglot.parse_one(sql, dialect="postgres")
        return True
    except sqlglot.errors.ParseError:
        return False


def validate_sql(sql: str):
    if not is_valid_syntax(sql):
        raise HTTPException(
            status_code=400, detail="Generated query has invalid SQL syntax"
        )
