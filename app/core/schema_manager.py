from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import inspect


from app.core.exceptions import (
    EmptyFileError,
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
            empty_error=EmptyFileError,
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

    def generate_from_db(self, session: Session):
        inspector = inspect(session.bind)
        output = []

        for table_name in inspector.get_table_names(schema="public"):
            columns = inspector.get_columns(table_name, schema="public")
            pk = inspector.get_pk_constraint(table_name, schema="public")
            fks = inspector.get_foreign_keys(table_name, schema="public")

            col_defs = []
            for col in columns:
                nullable = "" if col["nullable"] else " NOT NULL"
                col_defs.append(f'  "{col["name"]}" {col["type"]}{nullable}')

            if pk["constrained_columns"]:
                pk_cols = ", ".join(pk["constrained_columns"])
                col_defs.append(f"  PRIMARY KEY ({pk_cols})")

            for fk in fks:
                local_cols = ", ".join(f'"{c}"' for c in fk["constrained_columns"])
                ref_cols = ", ".join(f'"{c}"' for c in fk["referred_columns"])
                ref_table = fk["referred_table"]
                col_defs.append(
                    f'  FOREIGN KEY ({local_cols}) REFERENCES "{ref_table}" ({ref_cols})'
                )

            output.append(f'CREATE TABLE "{table_name}" (' + ", ".join(col_defs) + ");")

        return "\n\n".join(output)

    def generate_from_db_to_file(self, session: Session):
        content = self.generate_from_db(session=session)
        self._save(content=content)


schema_manager = SchemaManager()
