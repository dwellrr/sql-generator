import os
import re

import sqlglot
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.schema_manager import schema_manager
from app.core.data_manager import data_manager
from fastapi.responses import PlainTextResponse
from app.services.db_service import VerificationService
from sqlalchemy import inspect

load_dotenv()

DB_URL = os.getenv("DB_URL")

router = APIRouter()


def get_verification_service(db: Session = Depends(get_db)) -> VerificationService:
    return VerificationService(db=db)


@router.get("/generate/schema")
def get_current_schema(db: Session = Depends(get_db)):
    """Returns the current tables and columns in the DB."""
    manager = schema_manager
    content = manager.generate_from_db(session=db)
    return PlainTextResponse(content=content)


@router.post("/runquery")
def run_query(sql: str, db: Session = Depends(get_db)):
    statements = sqlglot.parse(sql)
    results = []

    for statement in statements:
        result = db.execute(text(statement.sql(dialect="postgres")))

        if result.returns_rows:
            rows = result.fetchall()
            results.extend([dict(row._mapping) for row in rows])

    db.commit()
    return {"results": results}


@router.post("/apply/full-reset")
def apply_schema_full_reset(db: Session = Depends(get_db)):
    sql_content = schema_manager.get_schema()

    # Drop all tables
    db.execute(
        text("""
        DO $$ DECLARE r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    )

    # Drop all sequences (left behind by SERIAL columns)
    db.execute(
        text("""
        DO $$ DECLARE r RECORD;
        BEGIN
            FOR r IN (SELECT relname FROM pg_class WHERE relkind = 'S' AND relnamespace = 'public'::regnamespace) LOOP
                EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.relname) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    )

    # Drop all enum types
    db.execute(
        text("""
        DO $$ DECLARE r RECORD;
        BEGIN
            FOR r IN (
                SELECT typname FROM pg_type
                JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
                WHERE pg_namespace.nspname = 'public' AND pg_type.typtype = 'e'
            ) LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    )

    db.execute(text(sql_content))
    db.commit()

    return {"status": "success", "message": "Schema fully reset and reapplied"}


@router.post("/apply/incremental")
def apply_schema_incremental(db: Session = Depends(get_db)):
    """
    Applies schema on top of the existing database.
    Uses IF NOT EXISTS — safe to run multiple times.
    schema SQL must use CREATE TABLE IF NOT EXISTS etc.
    """
    sql_content = schema_manager.get_schema()

    try:
        db.execute(text(sql_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Schema apply failed: {str(e)}")
    db.commit()
    return {"status": "success", "message": "Schema applied incrementally"}


@router.post("/apply/full-reset-data")
def reset_and_apply_data(db: Session = Depends(get_db)):
    """Drop all data and reapply from scratch. Order doesn't matter — TRUNCATE handles FK deps."""
    inspector = inspect(db.get_bind())
    table_names = inspector.get_table_names(schema="public")

    if not table_names:
        return

    tables = ", ".join(f'"{t}"' for t in table_names)
    db.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE;"))
    db.execute(text(data_manager.load_from_disk()))
    db.commit()


@router.post("/apply/incremental-data")
def apply_data_incremental(db: Session = Depends(get_db)):
    """Apply data without wiping existing rows. Skips conflicts on PK."""
    statements = [
        s.strip() for s in data_manager.load_from_disk().split(";") if s.strip()
    ]

    for stmt in statements:
        incremental = re.sub(r"^(INSERT INTO\s+)", r"\1", stmt, flags=re.IGNORECASE)
        incremental = f"{incremental} ON CONFLICT DO NOTHING"
        db.execute(text(incremental))

    db.commit()


@router.post("/validatequery")
def validate_query_against_db(sql: str, db: Session = Depends(get_db)):
    """
    Runs a query and rolls it back.
    This is needed to make sure a query is
    valid for running on the database
    """
    valid_for_db, error = get_verification_service().can_apply_to_db(sql, db)
    if not valid_for_db:
        raise HTTPException(
            status_code=400,
            detail=f"Provided query cannot run on the database: {str(error)}",
        )
    return {"status": "success", "message": "The query can be applied"}
