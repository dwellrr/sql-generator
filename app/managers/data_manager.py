from pathlib import Path
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmptyFileError,
    InvalidSQLError,
)
from app.managers.base_sql_manager import BaseSQLManager

ROOT = Path(__file__).parent.parent.parent
DATA_FILE = ROOT / "data.sql"


class DataManager(BaseSQLManager):
    def __init__(self):
        super().__init__(
            file_path=DATA_FILE,
            empty_error=EmptyFileError,
            invalid_error=InvalidSQLError,
        )

    def _validate(self, sql: str):
        pass

    def generate_from_db(self, session: Session):
        inspector = inspect(session.get_bind())
        output = []

        for table_name in inspector.get_table_names(schema="public"):
            result = session.execute(text(f'SELECT * FROM "{table_name}"'))
            rows = result.fetchall()
            keys = result.keys()

            for row in rows:
                cols = ", ".join(f'"{k}"' for k in keys)
                values = ", ".join(self._format_value(v) for v in row)
                output.append(f'INSERT INTO "{table_name}" ({cols}) VALUES ({values});')

        return "\n".join(output)

    def _format_value(self, v) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, (dict, list)):
            import json

            escaped = json.dumps(v).replace("'", "''")
            return f"'{escaped}'::jsonb"
        escaped = str(v).replace("'", "''")
        return f"'{escaped}'"

    def generate_from_db_to_file(self, session: Session):
        content = self.generate_from_db(session=session)
        self._save(content=content)


data_manager = DataManager()
