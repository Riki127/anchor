from app.ai.base import AdaptiveAssessmentConstraints
from app.ai.mock import MockAIProvider
from app.models import AssessmentSession, QAPair, Role, TurnDecision, Verdict


def make_role(id: int, title: str) -> Role:
    return Role(id=id, title=title)


def make_qa(order: int, answer: str) -> QAPair:
    return QAPair(id=order, session_id=1, order=order, question="q", answer=answer)


def make_snapshot(expectations: list[str] | None = None) -> AssessmentSession:
    return AssessmentSession(
        id=1,
        person_id=1,
        role_id=1,
        rubric_version=1,
        selected_tier_id="mid",
        selected_tier_name="Mid-level",
        selected_expectations=expectations
        or ["Own delivery", "Communicate trade-offs", "Support teammates"],
        next_expectations=["Lead cross-team initiatives"],
    )


def test_resolve_role_ladder_returns_stable_ordered_three_tier_ladder_with_usage():
    provider = MockAIProvider()

    first = provider.resolve_role_ladder("Software Engineer", [])
    second = provider.resolve_role_ladder("Software Engineer", [])

    assert [tier.id for tier in first.output.ladder.tiers] == [
        "associate",
        "mid",
        "senior",
    ]
    assert first.output == second.output
    assert first.usage == second.usage
    assert first.usage.input_tokens > 0
    assert first.usage.output_tokens > 0
    assert first.usage.model == "deterministic-v1"


def test_resolve_role_ladder_does_not_match_on_seniority_word_alone():
    provider = MockAIProvider()
    existing = [make_role(1, "Senior Software Engineer")]

    result = provider.resolve_role_ladder("Senior Product Manager", existing)

    assert result.output.matched_role_id is None


def test_start_item_targets_the_first_selected_expectation():
    provider = MockAIProvider()
    snapshot = make_snapshot(["Own production delivery", "Explain trade-offs"])

    result = provider.start_item(snapshot)

    assert result.output.decision == TurnDecision.continue_assessment
    assert "Own production delivery" in result.output.question
    assert result.output.remaining_uncertainties == [
        "Own production delivery",
        "Explain trade-offs",
    ]


def test_advance_assessment_forces_continuation_before_supplied_minimum():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")
    snapshot = make_snapshot()
    detailed_answer = "I owned the release, measured the result, and explained the trade-offs. " * 3
    history = [make_qa(index, detailed_answer) for index in range(2)]

    result = provider.advance_assessment(
        role,
        snapshot,
        history,
        AdaptiveAssessmentConstraints(minimum_answers=3, force_evaluate=True),
    )

    assert result.output.decision == TurnDecision.continue_assessment
    assert snapshot.selected_expectations[2] in result.output.question


def test_advance_assessment_completes_deterministically_after_three_detailed_answers():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")
    snapshot = make_snapshot()
    detailed_answer = "I led the work end to end, measured the outcome, and shared trade-offs with stakeholders. " * 2
    history = [make_qa(index, detailed_answer) for index in range(3)]

    first = provider.advance_assessment(
        role,
        snapshot,
        history,
        AdaptiveAssessmentConstraints(minimum_answers=3),
    )
    second = provider.advance_assessment(
        role,
        snapshot,
        history,
        AdaptiveAssessmentConstraints(minimum_answers=3),
    )

    assert first == second
    assert first.output.decision == TurnDecision.evaluate
    assert first.output.verdict == Verdict.exceeding
    assert first.output.covered_expectations == snapshot.selected_expectations


def test_advance_assessment_evaluates_at_ten_answers_when_forced():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")
    snapshot = make_snapshot()
    history = [make_qa(index, "brief answer") for index in range(10)]

    result = provider.advance_assessment(
        role,
        snapshot,
        history,
        AdaptiveAssessmentConstraints(minimum_answers=3, force_evaluate=True),
    )

    assert result.output.decision == TurnDecision.evaluate
    assert result.output.verdict == Verdict.below


def test_resolve_role_ladder_reuses_canonical_equivalent_title():
    provider = MockAIProvider()
    existing = [make_role(1, "Software Engineer")]

    result = provider.resolve_role_ladder("Software Developer", existing)

    assert result.output.matched_role_id == 1
