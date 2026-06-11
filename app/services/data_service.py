import re

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.managers.data_manager import data_manager


class DataService:
    def upload(self, content: str) -> None:
        data_manager.upload(content)

    def read(self) -> str:
        return data_manager.load_from_disk()

    def update_from_db(self, session: Session) -> None:
        data_manager.generate_from_db_to_file(session)

    def reset_and_apply(self, session: Session) -> None:
        """Drop all data and reapply from scratch. Order doesn't matter — TRUNCATE handles FK deps."""
        inspector = inspect(session.get_bind())
        table_names = inspector.get_table_names(schema="public")

        if not table_names:
            return

        tables = ", ".join(f'"{t}"' for t in table_names)
        session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE;"))
        session.execute(text(data_manager.load_from_disk()))
        session.commit()

    def apply_incremental(self, session: Session) -> None:
        """Apply data without wiping existing rows. Skips conflicts on PK."""
        statements = [
            s.strip() for s in data_manager.load_from_disk().split(";") if s.strip()
        ]

        for stmt in statements:
            incremental = re.sub(r"^(INSERT INTO\s+)", r"\1", stmt, flags=re.IGNORECASE)
            incremental = f"{incremental} ON CONFLICT DO NOTHING"
            session.execute(text(incremental))

        session.commit()


data_service = DataService()
