from pathlib import Path
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmptyFileError,
    InvalidSQLError,
)

from .base_sql_manager import BaseSQLManager

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
        inspector = inspect(session.bind)
        output = []

        for table_name in inspector.get_table_names(schema="public"):
            result = session.execute(text(f'SELECT * FROM "{table_name}"'))
            rows = result.fetchall()
            columns = result.keys()

            for row in rows:
                values = ", ".join([f"'{v}'" if v is not None else "NULL" for v in row])
                cols = ", ".join(columns)
                output.append(f'INSERT INTO "{table_name}" ({cols}) VALUES ({values});')

        return "\n".join(output)


data_manager = DataManager()
