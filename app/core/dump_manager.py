from pathlib import Path


from app.core.exceptions import (
    EmptyFileError,
    InvalidSQLError,
)

from .base_sql_manager import BaseSQLManager

ROOT = Path(__file__).parent.parent.parent
DUMP_FILE = ROOT / "latest.dump"


class DumpManager(BaseSQLManager):
    def __init__(self):
        super().__init__(
            file_path=DUMP_FILE,
            empty_error=EmptyFileError,
            invalid_error=InvalidSQLError,
        )

    def _validate(self, sql: str):
        pass


dump_manager = DumpManager()
