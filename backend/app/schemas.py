from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import AssessmentItemType, TurnDecision, Verdict


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoleTier(StrictOutputModel):
    id: str
    name: str
    expectations: list[str]


class TierRubric(StrictOutputModel):
    career_ladder_summary: str
    tiers: list[RoleTier]


class AdaptiveDecisionOutput(StrictOutputModel):
    confidence: float = Field(ge=0, le=1)
    covered_expectations: list[str]
    remaining_uncertainties: list[str]


class ContinueTurnOutput(AdaptiveDecisionOutput):
    decision: Literal[TurnDecision.continue_assessment]
    item_type: Literal[AssessmentItemType.conversation_question] = (
        AssessmentItemType.conversation_question
    )
    question: str


class EvaluateTurnOutput(AdaptiveDecisionOutput):
    decision: Literal[TurnDecision.evaluate]
    verdict: Verdict
    rationale: str
    recommendation: str


AdaptiveTurnOutput = Annotated[
    ContinueTurnOutput | EvaluateTurnOutput,
    Field(discriminator="decision"),
]


class RoleRubric(BaseModel):
    current_tier_expectations: list[str]
    next_tier_expectations: list[str]
    career_ladder_summary: str


class RoleMatchResult(BaseModel):
    matched_role_id: int | None
    rubric: RoleRubric


class QuestionOutput(BaseModel):
    question: str


class EvaluationOutput(BaseModel):
    verdict: Verdict
    rationale: str
    recommendation: str


class ResolvePersonRequest(BaseModel):
    display_name: str


class ResolveRoleRequest(BaseModel):
    title: str


class StartSessionRequest(BaseModel):
    person_id: int
    role_id: int
    tier_id: str


class SessionStartResponse(BaseModel):
    session_id: int
    role_id: int
    question: str


class AnswerRequest(BaseModel):
    answer: str


class AnswerResponse(BaseModel):
    status: str
    question: str | None = None
    verdict: str | None = None
    rationale: str | None = None
    recommendation: str | None = None


class QAPairRead(BaseModel):
    order: int
    question: str
    answer: str | None


class SessionRead(BaseModel):
    id: int
    status: str
    role_title: str
    qa_pairs: list[QAPairRead]
    verdict: str | None = None
    rationale: str | None = None
    recommendation: str | None = None


class EmployeeStatus(BaseModel):
    has_completed_session: bool
    last_completed_at: datetime | None = None
    last_session_id: int | None = None
