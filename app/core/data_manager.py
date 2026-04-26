from pathlib import Path


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


data_manager = DataManager()
