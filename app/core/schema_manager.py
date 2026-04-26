from pathlib import Path


from app.core.exceptions import (
    EmptySchemaError,
    InvalidSQLError,
    NoSchemaError,
)

from .base_sql_manager import BaseSQLManager

ROOT = Path(__file__).parent.parent.parent
SCHEMA_FILE = ROOT / "schema.sql"


class SchemaManager(BaseSQLManager):
    def __init__(self):
        super().__init__(
            file_path=SCHEMA_FILE,
            empty_error=EmptySchemaError,
            invalid_error=InvalidSQLError,
        )
        self._schema: str | None = None

    def get_schema(self) -> str | None:
        if not self._schema:
            raise NoSchemaError()
        else:
            return self._schema

    def load_from_disk(self) -> str | None:
        self._schema = super().load_from_disk()

    def _save(self, content: str):
        super()._save(content=content)
        self._schema = content

    def _validate(self, sql: str):
        pass


schema_manager = SchemaManager()
