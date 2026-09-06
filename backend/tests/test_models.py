from sqlalchemy import inspect, text
from sqlmodel import Session

from app.db import create_db_and_tables
from app.models import AssessmentSession, Person, QAPair, Role


def test_session_expectation_snapshot_is_independent_of_role_ladder_changes(db_session: Session):
    role = Role(
        title="Software Engineer",
        ladder={
            "career_ladder_summary": "IC ladder",
            "tiers": [
                {"id": "mid", "name": "Mid-level", "expectations": ["original"]},
                {"id": "senior", "name": "Senior", "expectations": ["next"]},
            ],
        },
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    person = Person(display_name="Ada Lovelace")
    db_session.add(person)
    db_session.flush()

    selected_tier = role.ladder["tiers"][0]
    next_tier = role.ladder["tiers"][1]
    session = AssessmentSession(
        person_id=person.id,
        role_id=role.id,
        selected_tier_id=selected_tier["id"],
        selected_tier_name=selected_tier["name"],
        selected_expectations=list(selected_tier["expectations"]),
        next_expectations=list(next_tier["expectations"]),
        rubric_version=role.rubric_version,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    role.ladder = {
        **role.ladder,
        "tiers": [
            {**selected_tier, "expectations": ["updated"]},
            next_tier,
        ],
    }
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    db_session.refresh(session)

    assert role.ladder["tiers"][0]["expectations"] == ["updated"]
    assert session.selected_expectations == ["original"]
    assert session.next_expectations == ["next"]


def test_migrations_are_idempotent_and_preserve_data(db_session: Session):
    role = Role(
        title="Backend Engineer",
        ladder={
            "career_ladder_summary": "IC ladder",
            "tiers": [{"id": "mid", "name": "Mid-level", "expectations": ["ships"]}],
        },
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    person = Person(display_name="Ada Lovelace")
    db_session.add(person)
    db_session.flush()
    session = AssessmentSession(person_id=person.id, role_id=role.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    item = QAPair(session_id=session.id, order=0, question="What did you ship?")
    db_session.add(item)
    db_session.commit()

    adaptive_columns = {
        "role": ["rubric_version", "ladder"],
        "session": [
            "person_id",
            "rubric_version",
            "selected_tier_id",
            "selected_tier_name",
            "role_title",
            "next_tier_id",
            "next_tier_name",
            "selected_expectations",
            "next_expectations",
        ],
        "qapair": ["item_type", "turn_decision"],
    }
    for table_name, column_names in adaptive_columns.items():
        for column_name in column_names:
            db_session.execute(
                text(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"')
            )
    db_session.commit()

    create_db_and_tables(db_session.get_bind())
    db_session.expire_all()

    inspector = inspect(db_session.get_bind())
    for table_name, expected_columns in adaptive_columns.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert set(expected_columns) <= actual_columns

    persisted_role = db_session.get(Role, role.id)
    persisted_session = db_session.get(AssessmentSession, session.id)
    persisted_item = db_session.get(QAPair, item.id)
    assert persisted_role.title == "Backend Engineer"
    assert persisted_session.role_id == role.id
    assert persisted_item.question == "What did you ship?"

    # Release the transaction the reads above implicitly opened: the DDL below
    # needs a table lock that this session's own open transaction would block.
    db_session.rollback()
    create_db_and_tables(db_session.get_bind())  # idempotent


def test_migration_drops_the_retired_employee_identity_system(db_session: Session):
    bind = db_session.get_bind()
    db_session.execute(text(
        'CREATE TABLE IF NOT EXISTS "employee" ("id" SERIAL PRIMARY KEY, "name" VARCHAR NOT NULL)'
    ))
    db_session.execute(text('ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "employee_id" INTEGER'))
    db_session.execute(text('ALTER TABLE "role" ADD COLUMN IF NOT EXISTS "rubric" JSON'))
    db_session.commit()

    create_db_and_tables(bind)
    db_session.expire_all()

    inspector = inspect(bind)
    assert "employee" not in inspector.get_table_names()
    assert "employee_id" not in {column["name"] for column in inspector.get_columns("session")}
    assert "rubric" not in {column["name"] for column in inspector.get_columns("role")}
