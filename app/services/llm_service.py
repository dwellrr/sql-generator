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


class LLMService:
    def __init__(self, db: Session):
        load_dotenv()
        self.client = OpenAI(
            base_url=os.getenv("LLM_HOST"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        self.db = db

    def get_verification_service(self):
        return VerificationService(self.db)

    def build_prompt(
        self,
        question: str,
        schema: str | None,
        query_errors: list[tuple[str, str]] | None,
    ) -> str:
        system_prompt = """Return ONLY a valid SQL query. IMPORTANT: No explanation at all, no markup. 
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
        response = self.client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
        )

        choice = response.choices[0]

        # Log the full choice so we can see what's actually coming back
        logging.warning("Finish reason: %s", choice.finish_reason)
        logging.warning("Raw message: %s", choice.message)
        logging.warning(
            "Content: %r", choice.message.content
        )  # %r shows None explicitly

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

    def generate_sql(self, question: str, max_retries: int = 5) -> str:
        failed_attempts: list[tuple[str, str]] = []
        schema = schema_manager.get_schema()
        verification_service = self.get_verification_service()

        for attempt in range(max_retries):
            prompt = self.build_prompt(question, schema, failed_attempts)

            try:
                sql = self.ask_llm(prompt, question)
            except HTTPException:
                raise  # LLM returned ERROR: - no point retrying

            try:
                self.validate_sql(sql)
            except HTTPException as e:
                logging.warning("Attempt %d failed: %s", attempt + 1, e.detail)
                failed_attempts.append((sql, e.detail))

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
        if not self.is_valid_syntax(sql):
            raise HTTPException(
                status_code=400, detail="Generated query has invalid SQL syntax"
            )
