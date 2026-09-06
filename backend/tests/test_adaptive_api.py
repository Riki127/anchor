from fastapi.testclient import TestClient
from sqlmodel import select

from app.ai import get_ai_provider
from app.ai.mock import MockAIProvider
from app.db import get_session
from app.main import app
from app.models import AIUsage, QAPair, AssessmentSession, Role, Evaluation
from app.ai.base import ProviderResult
from app.schemas import EvaluateTurnOutput
import pytest


def setup_flow(db_session, provider=None):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_ai_provider] = lambda: provider or MockAIProvider()
    client = TestClient(app)
    person = client.post('/people/resolve', json={'display_name': 'Ada'}).json()
    role = client.post('/roles/resolve', json={'title': 'Software Engineer'}).json()
    start = client.post('/sessions', json={'person_id': person['id'], 'role_id': role['id'], 'tier_id': role['ladder']['tiers'][0]['id']}).json()
    return client, person, role, start


@pytest.mark.parametrize('answer,count', [('x' * 100, 3), ('short', 10)])
def test_bounds_history_and_usage(db_session, answer, count):
    class Spy(MockAIProvider):
        def advance_assessment(self, role, snapshot, history, constraints):
            assert [q.order for q in history] == list(range(len(history)))
            assert all(q.answer == answer for q in history)
            assert constraints.force_evaluate == (len(history) == 10)
            return super().advance_assessment(role, snapshot, history, constraints)
    client, person, role, start = setup_flow(db_session, Spy())
    current = start
    url = f"/sessions/{start['session_id']}/answer"
    first = None
    for i in range(count):
        response = client.post(url, json={'item_id': current['item_id'], 'answer': answer})
        assert response.status_code == 200
        current = response.json()
        first = first or current
        assert current['status'] == ('completed' if i == count - 1 else 'in_progress')
    assert client.post(url, json={'item_id': start['item_id'], 'answer': answer}).json() == first
    history = client.get(f"/people/{person['id']}/status").json()['sessions']
    assert history[0]['id'] == start['session_id']
    other = client.post('/people/resolve', json={'display_name': 'Other'}).json()
    assert client.get(f"/people/{other['id']}/status").json()['sessions'] == []
    detail = client.get(f"/sessions/{start['session_id']}").json()
    assert 'confidence' not in str(detail) and 'turn_decision' not in str(detail)
    assert len(detail['qa_pairs']) == count
    assert len(db_session.exec(select(Evaluation)).all()) == 1
    usages = db_session.exec(select(AIUsage)).all()
    assert len(usages) == count + 2
    assert all(u.provider == 'mock' and u.model and u.input_tokens > 0 and u.output_tokens > 0 for u in usages)


def test_failure_retains_answer_and_retries_once(db_session):
    class Failing(MockAIProvider):
        def advance_assessment(self, *args):
            raise RuntimeError('offline')
    client, _, _, start = setup_flow(db_session, Failing())
    url = f"/sessions/{start['session_id']}/answer"
    payload = {'item_id': start['item_id'], 'answer': 'saved answer'}
    assert client.post(url, json=payload).status_code == 502
    assert db_session.get(QAPair, start['item_id']).answer == 'saved answer'
    app.dependency_overrides[get_ai_provider] = MockAIProvider
    result = client.post(url, json=payload)
    assert result.status_code == 200
    assert client.post(url, json=payload).json() == result.json()
    assert len(db_session.exec(select(QAPair)).all()) == 2


def test_invalid_provider_bounds_retain_answer(db_session):
    class Early(MockAIProvider):
        def advance_assessment(self, *args):
            initial = self.start_item(args[1])
            return ProviderResult(EvaluateTurnOutput(decision='evaluate', confidence=.8,
                covered_expectations=[], remaining_uncertainties=[], verdict='meeting',
                rationale='Good', recommendation='Learn more'), initial.usage)
    client, _, _, start = setup_flow(db_session, Early())
    url = f"/sessions/{start['session_id']}/answer"
    assert client.post(url, json={'item_id': start['item_id'], 'answer': 'saved'}).status_code == 502
    assert db_session.get(QAPair, start['item_id']).answer == 'saved'
    class Endless(MockAIProvider):
        def advance_assessment(self, role, snapshot, *args):
            return self.start_item(snapshot)
    app.dependency_overrides[get_ai_provider] = Endless
    current = start
    for i in range(10):
        result = client.post(url, json={'item_id': current['item_id'], 'answer': 'saved'})
        if i < 9:
            assert result.status_code == 200
            current = result.json()
        else:
            assert result.status_code == 502
    assert len(db_session.exec(select(QAPair)).all()) == 10
    assert not db_session.exec(select(Evaluation)).all()


def test_role_reuse_legacy_snapshot_and_invalid_ids(db_session):
    legacy = Role(title='Software Engineer', rubric={'old': 'preserved'})
    db_session.add(legacy)
    db_session.commit()
    client, person, role, start = setup_flow(db_session)
    assert role['id'] == legacy.id
    assert db_session.get(Role, legacy.id).rubric == {'old': 'preserved'}
    assert client.post('/roles/resolve', json={'title': role['title']}).json() == role
    assert len(db_session.exec(select(AIUsage).where(AIUsage.operation == 'resolve_role_ladder')).all()) == 1
    snapshot = db_session.get(AssessmentSession, start['session_id'])
    expected = list(snapshot.selected_expectations)
    legacy.ladder = {**legacy.ladder, 'tiers': [{**legacy.ladder['tiers'][0], 'expectations': ['changed']}]}
    db_session.add(legacy)
    db_session.commit()
    db_session.refresh(snapshot)
    assert snapshot.selected_expectations == expected
    payload = dict(person_id=person['id'], role_id=role['id'], tier_id='associate')
    for changed, code in [({'tier_id': 'unknown'}, 422), ({'person_id': 99999}, 404), ({'role_id': 99999}, 404), ({'role_title': 'mixed'}, 422)]:
        assert client.post('/sessions', json={**payload, **changed}).status_code == code
    assert client.get('/people/99999/status').status_code == 404
    assert client.get('/sessions/99999').status_code == 404
    assert client.post('/sessions/99999/answer', json={'answer': 'x', 'item_id': 1}).status_code == 404
    assert client.post(f"/sessions/{start['session_id']}/answer", json={'answer': 'x', 'item_id': 99999}).status_code == 409


def test_adaptive_role_remains_compatible_with_legacy_start(db_session):
    client, _, role, _ = setup_flow(db_session)
    result = client.post('/sessions', json={'role_title': role['title']})
    assert result.status_code == 200
    assert result.json()['role_id'] == role['id']


def test_concurrent_same_answer_advances_once(db_session):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlmodel import Session

    class Spy(MockAIProvider):
        calls = 0
        def advance_assessment(self, *args):
            self.calls += 1
            return super().advance_assessment(*args)

    provider = Spy()
    client, _, _, start = setup_flow(db_session, provider)
    engine = db_session.get_bind()
    db_session.rollback()

    def independent_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = independent_session
    barrier = Barrier(2)
    def submit():
        barrier.wait(timeout=5)
        return TestClient(app).post(f"/sessions/{start['session_id']}/answer",
            json={'item_id': start['item_id'], 'answer': 'same answer'})
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert all(result.status_code == 200 for result in results)
    assert results[0].json() == results[1].json()
    assert provider.calls == 1
    assert len(db_session.exec(select(QAPair)).all()) == 2


@pytest.mark.parametrize('invalid', ['unknown_match', 'empty_tiers', 'duplicate_ids', 'empty_expectations'])
def test_invalid_ladder_rejected_atomically(db_session, invalid):
    class BadLadder(MockAIProvider):
        def resolve_role_ladder(self, *args):
            result = super().resolve_role_ladder(*args)
            if invalid == 'unknown_match':
                result.output.matched_role_id = 99999
            elif invalid == 'empty_tiers':
                result.output.ladder.tiers = []
            elif invalid == 'duplicate_ids':
                result.output.ladder.tiers[1].id = result.output.ladder.tiers[0].id
            else:
                result.output.ladder.tiers[0].expectations = []
            return result
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_ai_provider] = BadLadder
    assert TestClient(app).post('/roles/resolve', json={'title': 'Engineer'}).status_code == 502
    assert not db_session.exec(select(Role)).all()
    assert not db_session.exec(select(AIUsage)).all()


def test_start_failure_has_no_partial_session(db_session):
    client, person, role, _ = setup_flow(db_session)
    class BadStart(MockAIProvider):
        def start_item(self, *args):
            raise RuntimeError('unavailable')
    before = len(db_session.exec(select(AssessmentSession)).all())
    app.dependency_overrides[get_ai_provider] = BadStart
    assert client.post('/sessions', json={'person_id': person['id'], 'role_id': role['id'],
        'tier_id': role['ladder']['tiers'][0]['id']}).status_code == 502
    assert len(db_session.exec(select(AssessmentSession)).all()) == before


def test_adaptive_flow_and_stale_retry(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_ai_provider] = MockAIProvider
    client = TestClient(app)
    person = client.post('/people/resolve', json={'display_name': '  Ada   Lovelace '}).json()
    assert client.post('/people/resolve', json={'display_name': 'ada lovelace'}).json()['id'] == person['id']
    role = client.post('/roles/resolve', json={'title': 'Software Engineer'}).json()
    start = client.post('/sessions', json={'person_id': person['id'], 'role_id': role['id'], 'tier_id': role['ladder']['tiers'][0]['id']}).json()
    url = f"/sessions/{start['session_id']}/answer"
    original = {'item_id': start['item_id'], 'answer': 'A detailed example of my work'}
    result = client.post(url, json=original)
    assert result.status_code == 200
    assert client.post(url, json=original).json() == result.json()
    assert client.post(url, json={**original, 'answer': 'changed'}).status_code == 409
    assert client.post(url, json={'answer': 'missing ID'}).status_code == 422
    assert len(db_session.exec(select(QAPair)).all()) == 2
    assert len(db_session.exec(select(AIUsage)).all()) == 3
