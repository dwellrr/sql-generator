from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text


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
        bind = session.get_bind()
        inspector = inspect(bind)
        # needed to compile types to their string representation
        dialect = bind.dialect
        output = []

        for table_name in inspector.get_table_names(schema="public"):
            columns = inspector.get_columns(table_name, schema="public")
            pk = inspector.get_pk_constraint(table_name, schema="public")
            fks = inspector.get_foreign_keys(table_name, schema="public")
            pk_cols = set(pk.get("constrained_columns", []))
            serial_cols = self._get_serial_columns(session, table_name)

            col_defs = []
            for col in columns:
                name = col["name"]
                # compile the type object to a plain string e.g. VARCHAR(100)
                col_type = col["type"].compile(dialect=dialect)

                if name in serial_cols and name in pk_cols:
                    col_defs.append(f'  "{name}" SERIAL PRIMARY KEY')
                else:
                    nullable = "" if col["nullable"] else " NOT NULL"
                    col_defs.append(f'  "{name}" {col_type}{nullable}')

            # only add a separate PK constraint if it wasn't already inlined above
            non_serial_pks = [c for c in pk_cols if c not in serial_cols]
            if non_serial_pks:
                pk_str = ", ".join(f'"{c}"' for c in non_serial_pks)
                col_defs.append(f"  PRIMARY KEY ({pk_str})")

            for fk in fks:
                local_cols = ", ".join(f'"{c}"' for c in fk["constrained_columns"])
                ref_cols = ", ".join(f'"{c}"' for c in fk["referred_columns"])
                ref_table = fk["referred_table"]
                col_defs.append(
                    f'  FOREIGN KEY ({local_cols}) REFERENCES "{ref_table}" ({ref_cols})'
                )

            col_block = ",\n".join(col_defs)
            output.append(f'CREATE TABLE "{table_name}" (\n{col_block}\n);')

        return "\n\n".join(output)

    def _get_serial_columns(self, session: Session, table_name: str) -> set[str]:
        """Return column names that are backed by an owned sequence (i.e. SERIAL)."""
        result = session.execute(
            text("""
            SELECT a.attname
            FROM pg_class t
            JOIN pg_attribute a ON a.attrelid = t.oid
            JOIN pg_depend d ON d.refobjid = t.oid AND d.refobjsubid = a.attnum
            JOIN pg_class s ON s.oid = d.objid AND s.relkind = 'S'
            WHERE t.relname = :table_name
              AND t.relnamespace = 'public'::regnamespace
              AND d.deptype = 'a'
        """),
            {"table_name": table_name},
        )
        return {row[0] for row in result}

    def generate_from_db_to_file(self, session: Session):
        content = self.generate_from_db(session=session)
        self._save(content=content)


schema_manager = SchemaManager()
