import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas import AdaptiveTurnOutput


def test_adaptive_continue_output_requires_a_question():
    adapter = TypeAdapter(AdaptiveTurnOutput)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "decision": "continue",
                "confidence": 0.6,
                "covered_expectations": ["delivery"],
                "remaining_uncertainties": ["scope"],
            }
        )


def test_adaptive_continue_output_accepts_a_question():
    adapter = TypeAdapter(AdaptiveTurnOutput)

    output = adapter.validate_python(
        {
            "decision": "continue",
            "confidence": 0.6,
            "covered_expectations": ["delivery"],
            "remaining_uncertainties": ["scope"],
            "question": "What did you deliver?",
        }
    )

    assert output.question == "What did you deliver?"
