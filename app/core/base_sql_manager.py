from pathlib import Path
import logging
from abc import ABC, abstractmethod

import sqlglot
from sqlalchemy.orm import Session

from .exceptions import SQLFileIOError


class BaseSQLManager(ABC):
    def __init__(self, file_path: Path, empty_error: type, invalid_error: type):
        self._file_path = file_path
        self._empty_error = empty_error
        self._invalid_error = invalid_error

    @abstractmethod
    def generate_from_db(self, session: Session):
        pass

    def load_from_disk(self) -> str | None:
        if not self._file_path.exists():
            raise self._empty_error()
        return self._file_path.read_text(encoding="utf-8")

    def upload_schema(self, content: str):
        self.validate(content)
        self._save(content)

    def _save(self, content: str):
        try:
            self._file_path.write_text(content)
        except Exception as e:
            logging.error(f"Could not write sql file: {e}")
            raise SQLFileIOError(f"Could not write sql file: {e}")

    def validate(self, content: str):
        if not content.strip():
            raise self._empty_error()

        if not self._is_valid_sql(content):
            raise self._invalid_error()

        self._validate(content)

    def _validate(self, content: str):
        pass

    def _is_valid_sql(self, sql: str) -> bool:
        try:
            sqlglot.parse(sql, dialect="postgres", error_level=sqlglot.ErrorLevel.RAISE)
            return True
        except sqlglot.errors.ParseError:
            return False
