from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session, select

from app.ai import AIProvider, get_ai_provider
from app.ai.base import RoleLadderResolution
from app.ai.usage import record_usage
from app.db import get_session
from app.models import AssessmentSession, Evaluation, Person, Role, SessionStatus
from app.schemas import (
    CompletedSessionSummary,
    ResolvePersonRequest,
    ResolveRoleRequest,
    TierRubric,
    PersonRead,
    PersonStatus,
    RoleRead,
)

router = APIRouter()


def _resolution_lock(db: Session, key: str) -> None:
    # Stable across processes; transaction locks also release on rollback.
    lock_id = int.from_bytes(sha256(key.encode()).digest()[:8], signed=True)
    db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': lock_id})


@router.post('/people/resolve', response_model=PersonRead)
def resolve_person(
    body: ResolvePersonRequest, db: Session = Depends(get_session)
) -> PersonRead:
    name = ' '.join(body.display_name.split())
    normalized_name = name.casefold()
    _resolution_lock(db, f'anchor:person:{normalized_name}')
    people = db.exec(select(Person).execution_options(populate_existing=True)).all()
    person = next(
        (person for person in people
         if ' '.join(person.display_name.split()).casefold() == normalized_name),
        None,
    )
    if person is None:
        person = Person(display_name=name)
        db.add(person)
        db.flush()
    response = PersonRead(id=person.id, display_name=person.display_name)
    db.commit()
    return response


@router.get('/people/{person_id}/status', response_model=PersonStatus)
def person_status(
    person_id: int, db: Session = Depends(get_session)
) -> PersonStatus:
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(404, 'Person not found')
    sessions = db.exec(
        select(AssessmentSession)
        .where(
            AssessmentSession.person_id == person_id,
            AssessmentSession.status == SessionStatus.completed,
        )
        .order_by(AssessmentSession.completed_at.desc(), AssessmentSession.id.desc())
    ).all()
    history = []
    for session in sessions:
        role = db.get(Role, session.role_id)
        evaluation = db.exec(
            select(Evaluation).where(Evaluation.session_id == session.id)
        ).first()
        history.append(CompletedSessionSummary(
            id=session.id,
            role_title=role.title,
            selected_tier_name=session.selected_tier_name,
            completed_at=session.completed_at,
            verdict=evaluation.verdict if evaluation else None,
        ))
    return PersonStatus(id=person.id, display_name=person.display_name, sessions=history)


def _role_response(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        title=role.title,
        rubric_version=role.rubric_version,
        ladder=TierRubric.model_validate(role.ladder),
    )


@router.post('/roles/resolve', response_model=RoleRead)
def resolve_role(
    body: ResolveRoleRequest,
    db: Session = Depends(get_session),
    provider: AIProvider = Depends(get_ai_provider),
) -> RoleRead:
    try:
        # Provider-defined equivalence requires one lock covering all title aliases.
        _resolution_lock(db, 'anchor:role-resolution')
        roles = list(db.exec(select(Role).execution_options(populate_existing=True)).all())
        exact = next(
            (role for role in roles if role.title.strip().casefold() == body.title.casefold()),
            None,
        )
        if exact and exact.ladder:
            response = _role_response(exact)
            db.commit()
            return response
        result = provider.resolve_role_ladder(body.title, roles)
        output = RoleLadderResolution.model_validate(result.output.model_dump())
        matched = next((r for r in roles if r.id == output.matched_role_id), None)
        if output.matched_role_id is not None and matched is None:
            raise ValueError('Unknown matched role')
        role = exact or matched
        if exact and matched and exact.id != matched.id:
            raise ValueError('Mismatched role')
        if role is None:
            tiers = output.ladder.tiers
            role = Role(
                title=body.title,
                rubric={
                    'current_tier_expectations': tiers[0].expectations,
                    'next_tier_expectations': tiers[1].expectations if len(tiers) > 1 else [],
                    'career_ladder_summary': output.ladder.career_ladder_summary,
                },
                rubric_version=2,
                ladder=output.ladder.model_dump(),
            )
        elif not role.ladder:
            role.ladder = output.ladder.model_dump()
            role.rubric_version = max(2, role.rubric_version + 1)
        db.add(role)
        db.flush()
        record_usage(db, result, provider, 'resolve_role_ladder', role_id=role.id)
        response = _role_response(role)
        db.commit()
        return response
    except Exception as exc:
        db.rollback()
        raise HTTPException(502, 'AI provider failed to resolve role') from exc
