from sqlalchemy import inspect, text
from sqlmodel import Session

from app.db import create_db_and_tables
from app.models import AssessmentSession, Employee, QAPair, Role


def test_role_and_employee_round_trip(db_session: Session):
    role = Role(
        title="Software Engineer",
        rubric={"current_tier_expectations": ["writes clean code"], "next_tier_expectations": ["leads projects"], "career_ladder_summary": "IC ladder"},
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    employee = Employee(name="Jordan Lee")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    assert role.id is not None
    assert employee.id is not None
    assert role.rubric["current_tier_expectations"] == ["writes clean code"]


def test_session_expectation_snapshot_is_independent_of_role_rubric(db_session: Session):
    role = Role(
        title="Software Engineer",
        rubric={},
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

    selected_tier = role.ladder["tiers"][0]
    next_tier = role.ladder["tiers"][1]
    session = AssessmentSession(
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


def test_startup_migrates_legacy_tables_without_rewriting_existing_data(
    db_session: Session,
):
    role = Role(title="Legacy role", rubric={"current_tier_expectations": ["ships"]})
    employee = Employee(name="Legacy employee")
    db_session.add(role)
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(role)
    db_session.refresh(employee)

    session = AssessmentSession(employee_id=employee.id, role_id=role.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    item = QAPair(session_id=session.id, order=0, question="What did you ship?")
    db_session.add(item)
    db_session.commit()

    legacy_columns = {
        "role": ["rubric_version", "ladder"],
        "session": [
            "person_id",
            "rubric_version",
            "selected_tier_id",
            "selected_tier_name",
            "selected_expectations",
            "next_expectations",
        ],
        "qapair": ["item_type", "turn_decision"],
    }
    for table_name, column_names in legacy_columns.items():
        for column_name in column_names:
            db_session.execute(
                text(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"')
            )
    db_session.commit()

    create_db_and_tables(db_session.get_bind())
    db_session.expire_all()

    inspector = inspect(db_session.get_bind())
    for table_name, expected_columns in legacy_columns.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert set(expected_columns) <= actual_columns

    persisted_role = db_session.get(Role, role.id)
    persisted_session = db_session.get(AssessmentSession, session.id)
    persisted_item = db_session.get(QAPair, item.id)
    assert persisted_role.title == "Legacy role"
    assert persisted_role.rubric == {"current_tier_expectations": ["ships"]}
    assert persisted_session.employee_id == employee.id
    assert persisted_item.question == "What did you ship?"
