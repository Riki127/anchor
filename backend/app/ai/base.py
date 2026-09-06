from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from app.models import AssessmentItemType, AssessmentSession, QAPair, Role
from app.schemas import (
    AdaptiveTurnOutput,
    ContinueTurnOutput,
    StrictOutputModel,
    TierRubric,
)


class RoleLadderResolution(StrictOutputModel):
    matched_role_id: int | None
    ladder: TierRubric


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int
    output_tokens: int
    model: str

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token counts cannot be negative")
        if not self.model.strip():
            raise ValueError("model cannot be blank")


OutputT = TypeVar("OutputT")


@dataclass(frozen=True, slots=True)
class ProviderResult(Generic[OutputT]):
    output: OutputT
    usage: Usage


@dataclass(frozen=True, slots=True)
class AdaptiveAssessmentConstraints:
    minimum_answers: int = 3
    force_evaluate: bool = False
    allowed_item_type: AssessmentItemType = AssessmentItemType.conversation_question

    def __post_init__(self) -> None:
        if self.minimum_answers < 0:
            raise ValueError("minimum_answers cannot be negative")


class AIProvider(Protocol):
    provider_name: str

    def resolve_role_ladder(
        self, title: str, existing_roles: list[Role]
    ) -> ProviderResult[RoleLadderResolution]: ...

    def start_item(
        self, session: AssessmentSession
    ) -> ProviderResult[ContinueTurnOutput]: ...

    def advance_assessment(
        self,
        role: Role,
        snapshot: AssessmentSession,
        history: list[QAPair],
        constraints: AdaptiveAssessmentConstraints,
    ) -> ProviderResult[AdaptiveTurnOutput]: ...
