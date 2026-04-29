import logging
from sqlalchemy import text
from sqlalchemy.orm import Session


class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def can_apply_to_db(self, sql: str) -> tuple[bool, str | None]:
        try:
            savepoint = self.db.begin_nested()
            self.db.execute(text(sql))
            savepoint.rollback()
            logging.warning("Tried applying. Success")
            return True, None
        except Exception as e:
            self.db.rollback()
            logging.warning("Tried applying. No success")
            return False, str(e)
