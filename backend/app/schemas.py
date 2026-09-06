from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import AssessmentItemType, TurnDecision, Verdict


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class RoleTier(StrictOutputModel):
    id: NonEmptyString
    name: NonEmptyString
    expectations: list[NonEmptyString] = Field(min_length=1)


class TierRubric(StrictOutputModel):
    career_ladder_summary: NonEmptyString
    tiers: list[RoleTier] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_tiers(self):
        if len({tier.id for tier in self.tiers}) != len(self.tiers):
            raise ValueError("tier IDs must be unique")
        return self


class AdaptiveDecisionOutput(StrictOutputModel):
    confidence: float = Field(ge=0, le=1)
    covered_expectations: list[NonEmptyString]
    remaining_uncertainties: list[NonEmptyString]


class ContinueTurnOutput(AdaptiveDecisionOutput):
    decision: Literal[TurnDecision.continue_assessment]
    item_type: Literal[AssessmentItemType.conversation_question] = (
        AssessmentItemType.conversation_question
    )
    question: NonEmptyString


class EvaluateTurnOutput(AdaptiveDecisionOutput):
    decision: Literal[TurnDecision.evaluate]
    verdict: Verdict
    rationale: NonEmptyString
    recommendation: NonEmptyString


AdaptiveTurnOutput = Annotated[
    ContinueTurnOutput | EvaluateTurnOutput,
    Field(discriminator="decision"),
]


class ResolvePersonRequest(StrictRequestModel):
    display_name: NonEmptyString


class ResolveRoleRequest(StrictRequestModel):
    title: NonEmptyString


class PersonRead(BaseModel):
    id: int
    display_name: str


class CompletedSessionSummary(BaseModel):
    id: int
    role_title: str
    selected_tier_name: str | None
    completed_at: datetime | None
    verdict: Verdict | None


class PersonStatus(PersonRead):
    sessions: list[CompletedSessionSummary]


class RoleRead(BaseModel):
    id: int
    title: str
    rubric_version: int
    ladder: TierRubric


class StartSessionRequest(StrictRequestModel):
    person_id: int = Field(gt=0)
    role_id: int = Field(gt=0)
    tier_id: NonEmptyString


class SessionStartResponse(BaseModel):
    item_id: int
    session_id: int
    role_id: int
    question: str


class AnswerRequest(BaseModel):
    item_id: int | None = Field(default=None, gt=0)
    answer: str


class AnswerResponse(BaseModel):
    item_id: int | None = None
    status: str
    question: str | None = None
    verdict: str | None = None
    rationale: str | None = None
    recommendation: str | None = None


class QAPairRead(BaseModel):
    item_id: int | None = None
    order: int
    question: str
    answer: str | None


class SessionRead(BaseModel):
    person_id: int | None = None
    selected_tier_id: str | None = None
    selected_tier_name: str | None = None
    id: int
    status: str
    role_title: str
    qa_pairs: list[QAPairRead]
    verdict: str | None = None
    rationale: str | None = None
    recommendation: str | None = None
