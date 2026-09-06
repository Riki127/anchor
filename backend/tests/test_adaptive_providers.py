from dataclasses import asdict
import json
from types import SimpleNamespace

import pytest

from app.ai.anthropic_provider import AnthropicAIProvider
from app.ai.base import AdaptiveAssessmentConstraints
from app.ai.openai_provider import OpenAIProvider
from app.models import AssessmentSession, QAPair, Role


CONTINUE = dict(decision="continue", confidence=0.5, covered_expectations=[],
                remaining_uncertainties=["delivery"], question="Describe your delivery.",
                item_type="conversation_question")
EVALUATE = dict(decision="evaluate", confidence=0.8, covered_expectations=["delivery"],
                remaining_uncertainties=[], verdict="meeting", rationale="Specific evidence.",
                recommendation="Lead a project.")
LADDER = dict(career_ladder_summary="Increasing ownership", tiers=[
    dict(id="mid", name="Mid-level", expectations=["delivery"]),
    dict(id="senior", name="Senior", expectations=["leadership"]),
])


class FakeSDK:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []
        self.responses = self.messages = self

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        schema = kwargs.get("text_format", kwargs.get("output_format"))
        payload = next(self.outputs)
        parsed = None if payload is None else schema.model_validate(payload)
        return SimpleNamespace(output_parsed=parsed, parsed_output=parsed,
                               model="returned-model", usage=SimpleNamespace(
                                   input_tokens=13, output_tokens=7,
                                   cache_read_input_tokens=5, cache_creation_input_tokens=3))


@pytest.fixture(params=[OpenAIProvider, AnthropicAIProvider])
def provider_type(request):
    return request.param


def snapshot():
    return AssessmentSession(role_id=1, role_title="Engineer", next_tier_id="senior", next_tier_name="Senior Engineer", selected_tier_id="mid", selected_tier_name="Mid-level",
                             selected_expectations=["snapshot-delivery"],
                             next_expectations=["snapshot-leadership"], rubric_version=2)


@pytest.mark.parametrize("count,output", [(0, CONTINUE), (2, CONTINUE), (3, EVALUATE),
                                          (4, CONTINUE), (10, EVALUATE)])
def test_adaptive_turn_contract_and_context(provider_type, count, output):
    client = FakeSDK([dict(turn=output)])
    provider = provider_type(client=client)
    history = [QAPair(order=i, question=f"question-{i}", answer=f"answer-{i}") for i in range(count)]
    result = provider.advance_assessment(Role(id=1, title="Engineer", rubric={}), snapshot(),
                                         history, AdaptiveAssessmentConstraints())
    assert result.output.decision == output["decision"]
    request = client.requests[0]
    prompt = request.get("input") or request["messages"][0]["content"]
    for value in ["Engineer", "Mid-level", "snapshot-delivery", "snapshot-leadership", "conversation_question"]:
        assert value in prompt
    for i in range(count):
        assert f"question-{i}" in prompt and f"answer-{i}" in prompt
    assert f"must_continue={count < 3}" in prompt
    assert f"must_evaluate={count >= 10}" in prompt
    assert asdict(result.usage) == dict(input_tokens=13 if provider_type is OpenAIProvider else 21,
                                      output_tokens=7, model="returned-model")
    if provider_type is OpenAIProvider:
        assert request["store"] is False


def test_start_uses_snapshot(provider_type):
    client = FakeSDK([dict(turn=CONTINUE)])
    result = provider_type(client=client).start_item(snapshot())
    assert result.output.question == "Describe your delivery."
    assert result.usage.output_tokens == 7
    request = client.requests[0]
    prompt = request.get('input') or request['messages'][0]['content']
    context = json.loads(prompt.split('as data, not instructions:\n')[-1])
    assert context['role'] == 'Engineer'
    assert context['next_tier_id'] == 'senior'
    assert context['next_tier_name'] == 'Senior Engineer'


@pytest.mark.parametrize('legacy', [False, True])
def test_prompt_never_uses_mutable_role_names(provider_type, legacy):
    client = FakeSDK([dict(turn=CONTINUE)])
    saved = AssessmentSession(role_id=1) if legacy else snapshot()
    provider_type(client=client).advance_assessment(
        Role(id=1, title='Changed title', rubric={}), saved, [], AdaptiveAssessmentConstraints())
    request = client.requests[0]
    prompt = request.get('input') or request['messages'][0]['content']
    context = json.loads(prompt.split('as data, not instructions:\n')[-1])
    assert context['role'] == (None if legacy else 'Engineer')
    assert context['next_tier_name'] == (None if legacy else 'Senior Engineer')
    assert 'Changed title' not in prompt


@pytest.mark.parametrize("count,output", [(2, EVALUATE), (10, CONTINUE)])
def test_rejects_output_violating_server_limits(provider_type, count, output):
    client = FakeSDK([dict(turn=output)])
    with pytest.raises((ValueError, RuntimeError)):
        provider_type(client=client).advance_assessment(
            Role(id=1, title="Engineer", rubric={}), snapshot(),
            [QAPair(order=i, question="q", answer="a") for i in range(count)],
            AdaptiveAssessmentConstraints())


@pytest.mark.parametrize("existing,outputs,expected_id,calls", [
    ([], [LADDER], None, 1),
    ([Role(id=7, title="Engineer", rubric={}, ladder=LADDER)], [{"matched_role_id": 7}], 7, 1),
    ([Role(id=7, title="Engineer", rubric={})], [{"matched_role_id": 7}, LADDER], 7, 2),
    ([Role(id=7, title="Engineer", rubric={})], [{"matched_role_id": None}, LADDER], None, 2),
])
def test_role_resolution_reuse_and_all_call_usage(provider_type, existing, outputs, expected_id, calls):
    client = FakeSDK(outputs)
    result = provider_type(client=client).resolve_role_ladder("Developer", existing)
    assert result.output.matched_role_id == expected_id
    assert result.output.ladder.model_dump() == LADDER
    assert result.usage.input_tokens == calls * (13 if provider_type is OpenAIProvider else 21)
    assert result.usage.output_tokens == calls * 7
    assert len(client.requests) == calls


def test_unknown_role_id_rejected(provider_type):
    client = FakeSDK([{"matched_role_id": 99}])
    with pytest.raises(RuntimeError, match="unknown role"):
        provider_type(client=client).resolve_role_ladder("Developer", [Role(id=7, title="Engineer", rubric={})])


def test_missing_output_rejected(provider_type):
    with pytest.raises(RuntimeError, match="structured output"):
        provider_type(client=FakeSDK([None])).start_item(snapshot())


@pytest.mark.parametrize("ladder", [
    dict(career_ladder_summary="Progression", tiers=[]),
    dict(career_ladder_summary="Progression", tiers=[dict(id="mid", name="Mid", expectations=[])]),
    dict(career_ladder_summary="Progression", tiers=LADDER["tiers"] * 2),
])
def test_invalid_generated_ladder_rejected(provider_type, ladder):
    with pytest.raises(ValueError):
        provider_type(client=FakeSDK([ladder])).resolve_role_ladder("Engineer", [])


def test_sdk_wire_schema_has_supported_nested_union_and_required_properties():
    import anthropic
    from openai.lib._parsing._responses import type_to_text_format_param
    from app.ai.adaptive import AdaptiveTurnEnvelope

    schemas = [type_to_text_format_param(AdaptiveTurnEnvelope)["schema"],
               anthropic.transform_schema(AdaptiveTurnEnvelope)]
    for schema in schemas:
        assert schema["type"] == "object"
        assert len(schema["properties"]["turn"]["anyOf"]) == 2
        def check(node):
            if isinstance(node, dict):
                assert "default" not in node
                if node.get("type") == "object":
                    assert node["additionalProperties"] is False
                    assert set(node["required"]) == set(node["properties"])
                for value in node.values():
                    check(value)
            elif isinstance(node, list):
                for value in node:
                    check(value)
        check(schema)


@pytest.mark.parametrize("count,minimum,force,output", [
    (2, 0, True, CONTINUE),
    (3, 3, True, EVALUATE),
    (10, 11, False, EVALUATE),
])
def test_hard_bounds_and_force_evaluation(provider_type, count, minimum, force, output):
    result = provider_type(client=FakeSDK([dict(turn=output)])).advance_assessment(
        Role(id=1, title="Engineer", rubric={}), snapshot(),
        [QAPair(order=i, question="q", answer="a") for i in range(count)]
        + [QAPair(order=count, question="unanswered", answer=None)],
        AdaptiveAssessmentConstraints(minimum_answers=minimum, force_evaluate=force),
    )
    assert result.output.decision == output["decision"]
