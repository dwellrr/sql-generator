import os

import sqlglot
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.schema_manager import schema_manager
from fastapi.responses import PlainTextResponse

load_dotenv()

DB_URL = os.getenv("DB_URL")

router = APIRouter()


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
    """
    Drops ALL tables in the public schema and reapplies the uploaded SQL schema.
    Destructive — all data will be lost.
    """
    sql_content = schema_manager.get_schema()

    db.execute(
        text("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
            ) LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    )
    db.execute(
        text("""
        DO $$ DECLARE
            r RECORD;
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
