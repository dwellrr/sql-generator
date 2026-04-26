import os

from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text

router = APIRouter()
SCHEMA_FILE = Path(__file__).parent.parent.parent / "schema.sql"

load_dotenv()

engine = create_engine(os.getenv("DB_URL"), echo=True)


@router.get("/current")
def get_current_schema():
    """Returns the current tables and columns in the DB."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)
        )
        rows = result.fetchall()

    schema = {}
    for row in rows:
        table = row.table_name
        if table not in schema:
            schema[table] = []
        schema[table].append(
            {
                "column": row.column_name,
                "type": row.data_type,
                "nullable": row.is_nullable == "YES",
            }
        )

    return {"tables": schema}


@router.post("/runquery")
def run_query(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]


@router.post("/apply/full-reset")
def apply_schema_full_reset():
    """
    Drops ALL tables in the public schema and reapplies the uploaded SQL schema.
    Destructive — all data will be lost.
    """
    sql_content = SCHEMA_FILE.read_text()

    with engine.begin() as conn:
        conn.execute(
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

        conn.execute(
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

        conn.execute(text(sql_content))

    return {"status": "success", "message": "Schema fully reset and reapplied"}


@router.post("/apply/incremental")
def apply_schema_incremental():
    """
    Applies schema on top of the existing database.
    Uses IF NOT EXISTS — safe to run multiple times.
    schema SQL must use CREATE TABLE IF NOT EXISTS etc.
    """
    sql_content = SCHEMA_FILE.read_text()

    with engine.begin() as conn:
        try:
            conn.execute(text(sql_content))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Schema apply failed: {str(e)}"
            )

    return {"status": "success", "message": "Schema applied incrementally"}
