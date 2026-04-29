from pathlib import Path
import os
import subprocess
from dotenv import load_dotenv
from urllib.parse import urlparse


from app.core.exceptions import (
    EmptyFileError,
    InvalidSQLError,
)

from .base_sql_manager import BaseSQLManager

ROOT = Path(__file__).parent.parent.parent
DUMP_FILE = ROOT / "dump.sql"

load_dotenv()


class DumpManager(BaseSQLManager):
    def __init__(self):
        super().__init__(
            file_path=DUMP_FILE,
            empty_error=EmptyFileError,
            invalid_error=InvalidSQLError,
        )
        self._url = urlparse(os.getenv("DB_URL"))

    def _validate(self, sql: str):
        pass

    def generate_from_db(self):
        result = subprocess.run(
            [
                "pg_dump",
                "--host",
                self._url.hostname,
                "--port",
                str(self._url.port),
                "--username",
                self._url.username,
                "--dbname",
                self._url.path[1:],
                "--no-password",
            ],
            env={**os.environ, "PGPASSWORD": self._url.password},
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")

        return result.stdout


dump_manager = DumpManager()
