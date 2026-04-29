import logging
import os
import re

import sqlglot
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session
from app.services.db_service import VerificationService
from app.core.schema_manager import schema_manager
from sqlalchemy import text
from app.core.exceptions import NoSchemaError


class LLMService:
    def __init__(self, db: Session):
        load_dotenv()
        self.client = OpenAI(
            base_url=os.getenv("LLM_HOST"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        self.db = db
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_db",
                    "description": (
                        "Run a read-only SELECT query to inspect existing data. "
                        "Use this to fetch IDs or sample values before writing your final query."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "A SELECT query. Must be read-only.",
                            }
                        },
                        "required": ["sql"],
                    },
                },
            }
        ]

    def get_verification_service(self):
        return VerificationService(self.db)

    def build_prompt(
        self,
        question: str,
        schema: str | None,
        query_errors: list[tuple[str, str]] | None,
    ) -> str:
        system_prompt = """You are a PostgreSQL SQL assistant. Return ONLY valid PostgreSQL syntax. IMPORTANT: No explanation at all, no markup. 
            If the question cannot be answered with the provided schema, 
            start your response with ERROR: followed by a description of the issue."""
        if schema:
            system_prompt += f"""\n\nAdhere to this schema:\n{schema}\n
            IMPORTANT: You MUST only use tables and columns that exist in the schema above.
            Do NOT invent tables or columns that are not in the schema.\n"""
        if query_errors:
            system_prompt += (
                "\n Here are your attempted queries and their errors for this request:"
            )
            for sql, error in query_errors:
                system_prompt += f"""
                Attempted query:
                {sql}

                Erorr:
                {error}

                """

        logging.warning(f"PROMPT: {system_prompt}")
        return system_prompt

    def ask_llm(self, prompt: str, question: str) -> dict:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]

        for _ in range(5):  # max tool-call rounds
            response = self.client.chat.completions.create(
                model=os.getenv("LLM_MODEL"), messages=messages
            )

            choice = response.choices[0]

            # Log the full choice so we can see what's actually coming back
            logging.warning("Finish reason: %s", choice.finish_reason)
            logging.warning("Raw message: %s", choice.message)
            logging.warning(
                "Content: %r", choice.message.content
            )  # %r shows None explicitly

            if choice.finish_reason == "stop":
                sql = choice.message.content or ""
                if not sql:
                    raise HTTPException(
                        status_code=502, detail="LLM returned empty response"
                    )
                if sql.upper().startswith("ERROR:"):
                    raise HTTPException(status_code=400, detail=sql[6:].strip())
                return self.clean_sql(sql)

            # LLM wants to call a tool
            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)  # append assistant turn with tool_calls

                for tool_call in choice.message.tool_calls:
                    result = self._handle_tool_call(tool_call)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

        sql = choice.message.content

        if sql is None:
            raise HTTPException(
                status_code=502,
                detail=f"LLM returned no content (finish_reason={choice.finish_reason})",
            )

        sql = self.clean_sql(sql)

        if sql.upper().startswith("ERROR:"):
            raise HTTPException(status_code=400, detail=sql[6:].strip())

        logging.warning(f"Generated result: {sql}")
        return sql

    def _handle_tool_call(self, tool_call) -> str:
        import json

        args = json.loads(tool_call.function.arguments)
        sql = args.get("sql", "")

        parsed = sql.strip().upper()
        if not parsed.startswith("SELECT"):
            return "ERROR: Only SELECT queries are allowed for introspection."

        try:
            result = self.db.execute(text(sql))
            rows = result.fetchall()
            return json.dumps([list(r) for r in rows[:50]])
        except Exception as e:
            return f"ERROR: {str(e)}"

    def generate_sql(self, question: str, max_retries: int = 5) -> str:
        failed_attempts: list[tuple[str, str]] = []
        try:
            schema = schema_manager.get_schema()
        except NoSchemaError:
            schema = None

        has_schema = schema is not None
        verification_service = self.get_verification_service() if has_schema else None

        for attempt in range(max_retries):
            if schema:
                prompt = self.build_prompt(question, schema, failed_attempts)
            else:
                prompt = self.build_prompt(question, None, failed_attempts)

            try:
                sql = self.ask_llm(prompt, question)
            except HTTPException:
                raise  # LLM returned ERROR: - no point retrying

            try:
                self.validate_sql(sql)
            except HTTPException as e:
                logging.warning("Attempt %d failed: %s", attempt + 1, e.detail)
                failed_attempts.append((sql, e.detail))

            if not has_schema:
                return sql

            try:
                fits_db, error = verification_service.can_apply_to_db(sql=sql)
            except Exception as e:
                logging.warning("Attempt %d failed: %s", attempt + 1, e.detail)
                failed_attempts.append((sql, e.detail))

            if not fits_db:
                failed_attempts.append((sql, error))
            else:
                return sql

        raise HTTPException(
            status_code=400,
            detail=f"Could not generate a valid query after {max_retries} attempts. "
            f"Last error: {failed_attempts[-1][1] if failed_attempts else 'unknown'}",
        )

    def clean_sql(self, sql: str) -> str:
        sql = sql.replace("```sql", "")
        sql = sql.replace("```", "")
        sql = sql.replace("\n", " ")
        sql = re.sub(r"\s+", " ", sql)
        return sql.strip()

    def is_valid_syntax(self, sql: str) -> bool:
        try:
            sqlglot.parse_one(sql, dialect="postgres")
            return True
        except sqlglot.errors.ParseError:
            return False

    def validate_sql(self, sql: str):
        try:
            sqlglot.parse_one(sql, dialect="postgres")
        except (sqlglot.errors.ParseError, sqlglot.errors.TokenError):
            raise HTTPException(
                status_code=400, detail="Generated query has invalid SQL syntax"
            )
