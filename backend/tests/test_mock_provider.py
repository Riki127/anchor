from app.ai.base import AdaptiveAssessmentConstraints
from app.ai.mock import MockAIProvider
from app.models import AssessmentSession, QAPair, Role, TurnDecision, Verdict


def make_role(id: int, title: str, rubric: dict | None = None) -> Role:
    return Role(id=id, title=title, rubric=rubric or {"current_tier_expectations": [], "next_tier_expectations": [], "career_ladder_summary": ""})


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


def test_match_or_create_role_reuses_overlapping_title():
    provider = MockAIProvider()
    existing = [make_role(1, "Software Engineer")]

    result = provider.match_or_create_role("Software Developer", existing)

    assert result.matched_role_id == 1


def test_match_or_create_role_creates_new_when_no_overlap():
    provider = MockAIProvider()
    existing = [make_role(1, "Software Engineer")]

    result = provider.match_or_create_role("Product Manager", existing)

    assert result.matched_role_id is None
    assert result.rubric.current_tier_expectations


def test_generate_next_question_is_deterministic_by_history_length():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")

    first = provider.generate_next_question(role, [])
    second = provider.generate_next_question(role, [make_qa(0, "answer")])

    assert first.question != second.question


def test_evaluate_session_below_for_short_answers():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")
    qa_history = [make_qa(i, "short") for i in range(5)]

    result = provider.evaluate_session(role, qa_history)

    assert result.verdict == Verdict.below


def test_evaluate_session_exceeding_for_long_detailed_answers():
    provider = MockAIProvider()
    role = make_role(1, "Software Engineer")
    long_answer = "This is a long and detailed answer. " * 10
    qa_history = [make_qa(i, long_answer) for i in range(5)]

    result = provider.evaluate_session(role, qa_history)

    assert result.verdict == Verdict.exceeding
