from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.ai import AIProvider, get_ai_provider
from app.db import get_session
from app.models import Evaluation, QAPair, Role, AssessmentSession
from app import adaptive_sessions
from app.schemas import AnswerRequest, AnswerResponse, QAPairRead, SessionRead, SessionStartResponse, StartSessionRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionStartResponse)
def start_session(
    body: StartSessionRequest,
    db: Session = Depends(get_session),
    provider: AIProvider = Depends(get_ai_provider),
) -> SessionStartResponse:
    return adaptive_sessions.start(body, db, provider)


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: int,
    body: AnswerRequest,
    db: Session = Depends(get_session),
    provider: AIProvider = Depends(get_ai_provider),
) -> AnswerResponse:
    if db.get(AssessmentSession, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return adaptive_sessions.answer(session_id, body, db, provider)


@router.get("/{session_id}", response_model=SessionRead)
def get_session_detail(session_id: int, db: Session = Depends(get_session)) -> SessionRead:
    session = db.get(AssessmentSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    role = db.get(Role, session.role_id)
    if role is None:
        raise HTTPException(status_code=500, detail="Role not found for session")

    qa_pairs = list(
        db.exec(select(QAPair).where(QAPair.session_id == session_id).order_by(QAPair.order)).all()
    )
    evaluation = db.exec(select(Evaluation).where(Evaluation.session_id == session_id)).first()

    return SessionRead(
        person_id=session.person_id,
        selected_tier_id=session.selected_tier_id,
        selected_tier_name=session.selected_tier_name,
        id=session.id,
        status=session.status.value,
        role_title=session.role_title or role.title,
        qa_pairs=[QAPairRead(item_id=qa.id, order=qa.order, question=qa.question, answer=qa.answer) for qa in qa_pairs],
        verdict=evaluation.verdict.value if evaluation else None,
        rationale=evaluation.rationale if evaluation else None,
        recommendation=evaluation.recommendation if evaluation else None,
    )
