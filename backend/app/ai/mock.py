import re

from app.ai.base import (
    AdaptiveAssessmentConstraints,
    ProviderResult,
    RoleLadderResolution,
    Usage,
)
from app.models import AssessmentSession, QAPair, Role, Verdict
from app.schemas import (
    ContinueTurnOutput,
    EvaluateTurnOutput,
    EvaluationOutput,
    QuestionOutput,
    RoleMatchResult,
    RoleRubric,
    RoleTier,
    TierRubric,
)

_MODEL = "deterministic-v1"

_SENIORITY_WORDS = frozenset(
    {
        "associate",
        "junior",
        "jr",
        "mid",
        "midlevel",
        "senior",
        "sr",
        "staff",
        "principal",
        "lead",
    }
)
_ROLE_WORD_ALIASES = {"developer": "engineer"}

_GENERIC_RUBRIC = RoleRubric(
    current_tier_expectations=[
        "Delivers assigned tasks independently with minimal guidance",
        "Communicates progress and blockers clearly to the team",
        "Applies core technical/domain skills correctly in day-to-day work",
    ],
    next_tier_expectations=[
        "Leads small initiatives end-to-end with limited oversight",
        "Mentors less experienced teammates",
        "Anticipates risks and proposes solutions proactively",
    ],
    career_ladder_summary="Generic individual-contributor progression from current tier to the next tier.",
)

_QUESTION_POOL = [
    "Describe a recent piece of work you're proud of and what made it successful.",
    "Tell me about a time you had to solve a problem with incomplete information.",
    "How do you prioritize your work when you have multiple competing deadlines?",
    "Describe a time you received difficult feedback. How did you respond?",
    "What's a skill you've been actively developing recently, and why?",
    "Tell me about a time you helped a teammate who was stuck.",
]


class MockAIProvider:
    provider_name = "mock"

    def resolve_role_ladder(
        self, title: str, existing_roles: list[Role]
    ) -> ProviderResult[RoleLadderResolution]:
        matched_role = _find_matching_role(title, existing_roles)
        if matched_role is not None and matched_role.ladder is not None:
            ladder = TierRubric.model_validate(matched_role.ladder)
        else:
            ladder = _build_ladder(title)

        return ProviderResult(
            output=RoleLadderResolution(
                matched_role_id=matched_role.id if matched_role is not None else None,
                ladder=ladder,
            ),
            usage=Usage(input_tokens=24, output_tokens=96, model=_MODEL),
        )

    def start_item(
        self, session: AssessmentSession
    ) -> ProviderResult[ContinueTurnOutput]:
        expectations = list(session.selected_expectations)
        target = expectations[0] if expectations else "your core role responsibilities"
        return ProviderResult(
            output=ContinueTurnOutput(
                decision="continue",
                confidence=0,
                covered_expectations=[],
                remaining_uncertainties=expectations or [target],
                question=_targeted_question(target),
            ),
            usage=Usage(input_tokens=18, output_tokens=32, model=_MODEL),
        )

    def advance_assessment(
        self,
        role: Role,
        snapshot: AssessmentSession,
        history: list[QAPair],
        constraints: AdaptiveAssessmentConstraints,
    ) -> ProviderResult[ContinueTurnOutput | EvaluateTurnOutput]:
        answered = [item for item in history if item.answer is not None]
        expectations = list(snapshot.selected_expectations)
        covered_count = min(len(answered), len(expectations))
        covered = expectations[:covered_count]
        remaining = expectations[covered_count:]
        enough_detail = bool(answered) and all(
            len((item.answer or "").strip()) >= 80 for item in answered
        )

        must_continue = len(answered) < constraints.minimum_answers
        should_evaluate = not must_continue and (
            constraints.force_evaluate or enough_detail
        )

        if should_evaluate:
            average_length = sum(len((item.answer or "").strip()) for item in answered) / len(
                answered
            )
            verdict, rationale, recommendation = _evaluation_for(average_length, role)
            output: ContinueTurnOutput | EvaluateTurnOutput = EvaluateTurnOutput(
                decision="evaluate",
                confidence=0.95 if enough_detail else 0.7,
                covered_expectations=covered,
                remaining_uncertainties=remaining,
                verdict=verdict,
                rationale=rationale,
                recommendation=recommendation,
            )
        else:
            target = _next_target(snapshot, remaining)
            output = ContinueTurnOutput(
                decision="continue",
                confidence=min(0.85, 0.25 + len(answered) * 0.15),
                covered_expectations=covered,
                remaining_uncertainties=remaining or [target],
                question=_targeted_question(target),
            )

        return ProviderResult(
            output=output,
            usage=Usage(input_tokens=48 + len(answered) * 12, output_tokens=44, model=_MODEL),
        )

    # Compatibility methods remain until the session API migrates to the unified contract.
    def match_or_create_role(self, title: str, existing_roles: list[Role]) -> RoleMatchResult:
        matched_role = _find_matching_role(title, existing_roles)
        if matched_role is not None:
            return RoleMatchResult(
                matched_role_id=matched_role.id, rubric=RoleRubric(**matched_role.rubric)
            )
        return RoleMatchResult(matched_role_id=None, rubric=_GENERIC_RUBRIC)

    def generate_next_question(self, role: Role, qa_history: list[QAPair]) -> QuestionOutput:
        index = len(qa_history)
        return QuestionOutput(question=_QUESTION_POOL[index % len(_QUESTION_POOL)])

    def evaluate_session(self, role: Role, qa_history: list[QAPair]) -> EvaluationOutput:
        average_length = sum(len(qa.answer or "") for qa in qa_history) / len(qa_history)
        verdict, rationale, recommendation = _evaluation_for(average_length, role)
        return EvaluationOutput(
            verdict=verdict,
            rationale=rationale,
            recommendation=recommendation,
        )


def _find_matching_role(title: str, existing_roles: list[Role]) -> Role | None:
    canonical_title = _canonical_role_title(title)
    for role in existing_roles:
        if canonical_title and canonical_title == _canonical_role_title(role.title):
            return role
    return None


def _canonical_role_title(title: str) -> tuple[str, ...]:
    words = re.findall(r"[a-z0-9]+", title.casefold().replace("mid-level", "midlevel"))
    return tuple(
        _ROLE_WORD_ALIASES.get(word, word)
        for word in words
        if word not in _SENIORITY_WORDS
    )


def _build_ladder(title: str) -> TierRubric:
    role_title = title.strip() or "this role"
    return TierRubric(
        career_ladder_summary=f"A three-tier progression for {role_title} from supported delivery to broad leadership.",
        tiers=[
            RoleTier(
                id="associate",
                name="Associate",
                expectations=[
                    "Delivers scoped work with guidance",
                    "Builds fluency in the role's core skills",
                ],
            ),
            RoleTier(
                id="mid",
                name="Mid-level",
                expectations=[
                    "Owns outcomes independently",
                    "Communicates decisions and trade-offs clearly",
                ],
            ),
            RoleTier(
                id="senior",
                name="Senior",
                expectations=[
                    "Leads ambiguous initiatives across teams",
                    "Raises the effectiveness of other people",
                ],
            ),
        ],
    )


def _next_target(snapshot: AssessmentSession, remaining: list[str]) -> str:
    if remaining:
        return remaining[0]
    if snapshot.next_expectations:
        return snapshot.next_expectations[0]
    return "another concrete example of impact in your role"


def _targeted_question(target: str) -> str:
    return f'Tell me about a specific example that demonstrates "{target}". What did you do and what changed?'


def _evaluation_for(average_length: float, role: Role) -> tuple[Verdict, str, str]:
    if average_length < 40:
        return (
            Verdict.below,
            "Answers were brief and lacked concrete detail relative to role expectations.",
            "Practice giving specific, detailed examples (STAR format) for common work scenarios.",
        )
    if average_length < 120:
        return (
            Verdict.meeting,
            f"Answers showed solid, specific examples matching expectations for {role.title}.",
            "Look for opportunities to lead a small initiative end-to-end to build toward the next tier.",
        )
    return (
        Verdict.exceeding,
        f"Answers consistently showed depth and initiative beyond expectations for {role.title}.",
        "Seek out mentoring opportunities and larger-scope initiatives to formalize readiness for the next tier.",
    )
