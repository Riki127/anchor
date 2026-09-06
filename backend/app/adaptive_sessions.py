from datetime import datetime

from fastapi import HTTPException
from pydantic import TypeAdapter
from sqlmodel import Session, select

from app.ai.base import AIProvider, AdaptiveAssessmentConstraints
from app.ai.usage import record_usage
from app.models import AssessmentSession, Evaluation, Person, QAPair, Role, SessionStatus
from app.schemas import AdaptiveTurnOutput, AnswerRequest, AnswerResponse, ContinueTurnOutput, SessionStartResponse, StartSessionRequest, TierRubric


def start(body: StartSessionRequest, db: Session, provider: AIProvider) -> SessionStartResponse:
    if db.get(Person, body.person_id) is None:
        raise HTTPException(404, 'Person not found')
    role = db.get(Role, body.role_id)
    if role is None:
        raise HTTPException(404, 'Role not found')
    if not role.ladder:
        raise HTTPException(409, 'Resolve role ladder before starting')
    tiers = TierRubric.model_validate(role.ladder).tiers
    index = next((i for i, tier in enumerate(tiers) if tier.id == body.tier_id), None)
    if index is None:
        raise HTTPException(422, 'Unknown tier')
    tier = tiers[index]
    next_tier = tiers[index + 1] if index + 1 < len(tiers) else None
    session = AssessmentSession(person_id=body.person_id, role_id=role.id,
        role_title=role.title, next_tier_id=next_tier.id if next_tier else None,
        next_tier_name=next_tier.name if next_tier else None,
        rubric_version=role.rubric_version, selected_tier_id=tier.id, selected_tier_name=tier.name,
        selected_expectations=list(tier.expectations),
        next_expectations=list(next_tier.expectations) if next_tier else [])
    try:
        result = provider.start_item(session)
        output = ContinueTurnOutput.model_validate(result.output.model_dump())
        db.add(session)
        db.flush()
        item = QAPair(session_id=session.id, order=0, question=output.question)
        db.add(item)
        record_usage(db, result, provider, 'start_item', session_id=session.id, role_id=role.id)
        db.commit()
        db.refresh(item)
    except Exception as exc:
        db.rollback()
        raise HTTPException(502, 'AI provider failed to start assessment') from exc
    return SessionStartResponse(session_id=session.id, role_id=role.id, item_id=item.id, question=item.question)


def answer(session_id: int, body: AnswerRequest, db: Session, provider: AIProvider) -> AnswerResponse:
    if body.item_id is None:
        raise HTTPException(422, 'item_id is required for adaptive sessions')

    def locked_state() -> tuple[AssessmentSession, list[QAPair], QAPair, AnswerResponse | None]:
        session = db.exec(select(AssessmentSession).where(AssessmentSession.id == session_id)
            .with_for_update().execution_options(populate_existing=True)).one()
        items = list(db.exec(select(QAPair).where(QAPair.session_id == session_id)
            .order_by(QAPair.order).execution_options(populate_existing=True)).all())
        item = next((i for i in items if i.id == body.item_id), None)
        if item is None:
            raise HTTPException(409, 'Item does not belong to this session')
        if item.answer is not None and item.answer != body.answer:
            raise HTTPException(409, 'Item already has a different answer')
        if item.turn_decision:
            return session, items, item, AnswerResponse.model_validate(item.turn_decision['response'])
        if item.id != items[-1].id or session.status == SessionStatus.completed:
            raise HTTPException(409, 'Item is not the current unanswered item')
        return session, items, item, None

    session, items, item, replay = locked_state()
    if replay:
        db.rollback()
        return replay
    item.answer = body.answer
    db.add(item)
    db.commit()  # The answer survives provider failure; advancement takes a fresh lock.
    session, items, item, replay = locked_state()
    if replay:
        db.rollback()
        return replay
    try:
        result = provider.advance_assessment(db.get(Role, session.role_id), session, items,
            AdaptiveAssessmentConstraints(force_evaluate=len(items) >= 10))
        output = TypeAdapter(AdaptiveTurnOutput).validate_python(result.output.model_dump())
        continuing = isinstance(output, ContinueTurnOutput)
        if (len(items) < 3 and not continuing) or (len(items) >= 10 and continuing):
            raise ValueError('Provider violated assessment bounds')
        if continuing:
            next_item = QAPair(session_id=session.id, order=len(items), question=output.question)
            db.add(next_item)
            db.flush()
            response = AnswerResponse(status='in_progress', item_id=next_item.id, question=next_item.question)
        else:
            db.add(Evaluation(session_id=session.id, verdict=output.verdict,
                rationale=output.rationale, recommendation=output.recommendation))
            session.status = SessionStatus.completed
            session.completed_at = datetime.utcnow()
            db.add(session)
            response = AnswerResponse(status='completed', verdict=output.verdict.value,
                rationale=output.rationale, recommendation=output.recommendation)
        item.turn_decision = {**output.model_dump(mode='json'), 'response': response.model_dump()}
        db.add(item)
        record_usage(db, result, provider, 'advance_assessment', session_id=session.id, role_id=session.role_id)
        db.commit()
        return response
    except Exception as exc:
        db.rollback()
        raise HTTPException(502, 'AI provider failed to advance assessment; retry the saved answer') from exc
