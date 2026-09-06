from sqlmodel import Session

from app.models import AssessmentSession, Employee, Role


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


def test_session_expectation_snapshot_is_independent_of_role_rubric():
    role = Role(
        title="Software Engineer",
        rubric={"tiers": [{"id": "mid", "expectations": ["original"]}]},
    )
    session = AssessmentSession(
        selected_tier_id="mid",
        selected_tier_name="Mid-level",
        selected_expectations=["original"],
        next_expectations=["next"],
        rubric_version=1,
    )

    role.rubric["tiers"][0]["expectations"] = ["updated"]

    assert session.selected_expectations == ["original"]
    assert session.next_expectations == ["next"]
