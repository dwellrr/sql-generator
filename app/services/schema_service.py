from sqlalchemy import text
from sqlalchemy.orm import Session

from app.managers.schema_manager import schema_manager


DROP_ALL_TABLES_SQL = """
DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
"""

DROP_ALL_SEQUENCES_SQL = """
DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN (SELECT relname FROM pg_class WHERE relkind = 'S' AND relnamespace = 'public'::regnamespace) LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.relname) || ' CASCADE';
    END LOOP;
END $$;
"""

DROP_ALL_ENUMS_SQL = """
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
"""


class SchemaService:
    def upload(self, content: str) -> None:
        schema_manager.upload(content)

    def read(self) -> str:
        return schema_manager.get_schema()

    def update_from_db(self, session: Session) -> None:
        schema_manager.generate_from_db_to_file(session)

    def generate_from_db(self, session: Session) -> str:
        return schema_manager.generate_from_db(session=session)

    def apply_full_reset(self, session: Session) -> None:
        sql_content = schema_manager.get_schema()

        session.execute(text(DROP_ALL_TABLES_SQL))
        session.execute(text(DROP_ALL_SEQUENCES_SQL))
        session.execute(text(DROP_ALL_ENUMS_SQL))
        session.execute(text(sql_content))
        session.commit()

    def apply_incremental(self, session: Session) -> None:
        sql_content = schema_manager.get_schema()
        try:
            session.execute(text(sql_content))
        except Exception as e:
            raise ValueError(f"Schema apply failed: {str(e)}") from e
        session.commit()


schema_service = SchemaService()
