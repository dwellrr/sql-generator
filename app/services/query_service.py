import logging

import sqlglot
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.verification_service import VerificationService


class QueryService:
    def __init__(self, db: Session):
        self.db = db
        self.verification = VerificationService(db)

    def run_query(self, sql: str) -> list[dict]:
        statements = sqlglot.parse(sql)
        results = []

        for statement in statements:
            result = self.db.execute(text(statement.sql(dialect="postgres")))

            if result.returns_rows:
                rows = result.fetchall()
                results.extend([dict(row._mapping) for row in rows])

        self.db.commit()
        return results

    def validate_query(self, sql: str) -> None:
        valid_for_db, error = self.verification.can_apply_to_db(sql)
        if not valid_for_db:
            logging.warning("Query validation failed: %s", error)
            raise ValueError(f"Provided query cannot run on the database: {error}")
