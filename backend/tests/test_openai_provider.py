from types import SimpleNamespace

from app.ai.openai_provider import OpenAIProvider
from app.models import QAPair, Role, Verdict
from app.schemas import EvaluationOutput, QuestionOutput, RoleRubric


class _FakeResponses:
    def __init__(self, *parsed_outputs: object) -> None:
        self._parsed_outputs = list(parsed_outputs)
        self.requests: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        return SimpleNamespace(output_parsed=self._parsed_outputs.pop(0))


class _FakeClient:
    def __init__(self, *parsed_outputs: object) -> None:
        self.responses = _FakeResponses(*parsed_outputs)


def make_role() -> Role:
    return Role(
        id=1,
        title="Software Engineer",
        rubric={
            "current_tier_expectations": ["ships reliable changes"],
            "next_tier_expectations": ["leads projects"],
            "career_ladder_summary": "increasing technical ownership",
        },
    )


def test_openai_provider_returns_a_generated_question():
    client = _FakeClient(QuestionOutput(question="What trade-off did you make recently?"))
    provider = OpenAIProvider(client=client)

    question = provider.generate_next_question(make_role(), [])

    assert question == QuestionOutput(question="What trade-off did you make recently?")
    assert client.responses.requests[0]["model"] == "gpt-5.6-terra"
    assert client.responses.requests[0]["text_format"] is QuestionOutput
    assert client.responses.requests[0]["store"] is False


def test_openai_provider_returns_a_session_evaluation():
    expected = EvaluationOutput(
        verdict=Verdict.meeting,
        rationale="The answer shows sound ownership.",
        recommendation="Lead a scoped delivery project.",
    )
    client = _FakeClient(expected)
    provider = OpenAIProvider(client=client)
    qa_history = [QAPair(order=0, question="What did you deliver?", answer="A reporting flow.")]

    evaluation = provider.evaluate_session(make_role(), qa_history)

    assert evaluation == expected


def test_openai_provider_creates_a_rubric_for_a_new_role():
    rubric = RoleRubric(
        current_tier_expectations=["delivers customer value"],
        next_tier_expectations=["owns a product area"],
        career_ladder_summary="increasing product scope",
    )
    client = _FakeClient(rubric)
    provider = OpenAIProvider(client=client)

    result = provider.match_or_create_role("Product Manager", [])

    assert result.matched_role_id is None
    assert result.rubric == rubric
