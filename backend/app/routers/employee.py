from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.employees import get_or_seed_employee
from app.models import AssessmentSession, SessionStatus
from app.schemas import EmployeeStatus

router = APIRouter(prefix="/employee", tags=["employee"])


@router.get("/status", response_model=EmployeeStatus)
def get_employee_status(db: Session = Depends(get_session)) -> EmployeeStatus:
    employee = get_or_seed_employee(db)
    last_completed = db.exec(
        select(AssessmentSession)
        .where(AssessmentSession.employee_id == employee.id)
        .where(AssessmentSession.status == SessionStatus.completed)
        .order_by(AssessmentSession.completed_at.desc())
    ).first()

    if last_completed is None:
        return EmployeeStatus(has_completed_session=False)

    return EmployeeStatus(
        has_completed_session=True,
        last_completed_at=last_completed.completed_at,
        last_session_id=last_completed.id,
    )
