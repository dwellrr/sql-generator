from pathlib import Path
import logging

import sqlglot

from app.core.exceptions import (
    EmptySchemaError,
    InvalidSQLError,
    SchemaError,
    NoSchemaError,
)

ROOT = Path(__file__).parent.parent.parent
SCHEMA_FILE = ROOT / "schema.sql"


class SchemaManager:
    def __init__(self):
        self._schema: str | None = None

    def get_schema(self) -> str | None:
        if not self._schema:
            raise NoSchemaError()
        else:
            return self._schema

    def upload_schema(self, content: str):
        self._verify_schema(content)
        self._save(content)

    def _save(self, content: str):
        try:
            SCHEMA_FILE.write_text(content)
            self._schema = content
        except Exception as e:
            logging.error(f"Could not write schema file: {e}")
            raise SchemaError(f"Could not write schema file: {e}")

    def _verify_schema(self, sql: str):
        if not sql.strip():
            raise EmptySchemaError()

        if not self._is_valid_syntax(sql):
            raise InvalidSQLError(detail="Uploaded file has invalid SQL syntax")

    def _is_valid_syntax(self, sql: str) -> bool:
        try:
            sqlglot.parse_one(sql, dialect="postgres")
            return True
        except sqlglot.errors.ParseError:
            return False


schema_manager = SchemaManager()
