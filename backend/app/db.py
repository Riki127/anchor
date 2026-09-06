from typing import Iterator

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(settings.database_url, echo=False)

_ADAPTIVE_COLUMN_MIGRATIONS = (
    'ALTER TABLE "role" ADD COLUMN IF NOT EXISTS "rubric_version" INTEGER NOT NULL DEFAULT 1',
    'ALTER TABLE "role" ADD COLUMN IF NOT EXISTS "ladder" JSON',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "person_id" INTEGER REFERENCES "person" ("id")',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "rubric_version" INTEGER',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "selected_tier_id" VARCHAR',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "selected_tier_name" VARCHAR',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "role_title" VARCHAR',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "next_tier_id" VARCHAR',
    'ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "next_tier_name" VARCHAR',
    "ALTER TABLE \"session\" ADD COLUMN IF NOT EXISTS \"selected_expectations\" JSON NOT NULL DEFAULT '[]'::json",
    "ALTER TABLE \"session\" ADD COLUMN IF NOT EXISTS \"next_expectations\" JSON NOT NULL DEFAULT '[]'::json",
    'ALTER TABLE "qapair" ADD COLUMN IF NOT EXISTS "item_type" VARCHAR(21) NOT NULL DEFAULT \'conversation_question\'',
    'ALTER TABLE "qapair" ADD COLUMN IF NOT EXISTS "turn_decision" JSON',
    # Retired with the title-only session flow: the separate employee identity
    # and the flat per-role rubric that preceded generated ladders.
    'ALTER TABLE "session" DROP COLUMN IF EXISTS "employee_id"',
    'ALTER TABLE "role" DROP COLUMN IF EXISTS "rubric"',
    'DROP TABLE IF EXISTS "employee"',
)


def create_db_and_tables(db_engine: Engine = engine) -> None:
    SQLModel.metadata.create_all(db_engine)
    with db_engine.begin() as connection:
        for statement in _ADAPTIVE_COLUMN_MIGRATIONS:
            connection.execute(text(statement))


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
