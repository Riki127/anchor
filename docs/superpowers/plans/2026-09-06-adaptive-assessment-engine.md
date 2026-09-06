# Adaptive Assessment Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Completed steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver a personalized 3–10 prompt, rubric-backed assessment that records auditable decisions and measured provider token usage.

**Architecture:** Replace the seeded employee with a lightweight `Person`; persist a versioned role ladder and immutable per-session tier snapshot. Replace separate next-question/evaluation provider methods with one structured adaptive turn that either continues or completes. The API drives server-enforced limits; React drives profile, role, tier, and conversation screens.

**Tech Stack:** FastAPI, Pydantic, SQLModel/PostgreSQL, OpenAI and Anthropic Python SDKs, React, TypeScript, Tailwind, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-06-adaptive-assessment-engine-design.md`

## Global Constraints

- Use strict Pydantic structured output for every LLM response.
- Include all prior assessment items and answers in each adaptive-turn prompt.
- Do not add dependencies, execute untrusted code, or store prompts/answers in usage records.
- Apply `ACCESSIBILITY.md` to all UI work.
- Keep practical exercises represented only by the item contract; this delivery creates conversational items only.

---

### Task 1: Versioned persistence and API schemas

**Files:** Modify `backend/app/models.py`, `backend/app/schemas.py`, `backend/tests/test_models.py`; create `backend/tests/test_adaptive_schemas.py`.

**Interfaces:** Produces `Person`, `RoleTier`, `AssessmentItemType`, `TurnDecision`, `AIUsage`, `TierRubric`, `AdaptiveTurnOutput`, `ResolvePersonRequest`, `ResolveRoleRequest`, and `StartSessionRequest(person_id, role_id, tier_id)` for all later tasks.

- [x] **Step 1: Write failing schema/model tests.**

```python
from app.models import AssessmentSession
from app.schemas import ContinueTurnOutput

# AdaptiveTurnOutput is a discriminated union: construct a concrete member,
# or validate unknown data with pydantic.TypeAdapter(AdaptiveTurnOutput).
def test_adaptive_turn_requires_question_only_when_continuing():
    assert ContinueTurnOutput(decision="continue", confidence=0.6,
        covered_expectations=["delivery"], remaining_uncertainties=["scope"],
        question="What did you deliver?").question

def test_session_snapshot_is_independent_of_role_rubric():
    session = AssessmentSession(selected_tier_id="mid", selected_expectations=["a"])
    assert session.selected_expectations == ["a"]
```

- [x] **Step 2: Run the targeted tests and confirm they fail.**

Run: `pytest tests/test_adaptive_schemas.py -v`
Expected: import/validation failure because the adaptive types do not exist.

- [x] **Step 3: Add minimal models and schemas.** Use a `Person` table, a `Role.rubric_version` plus JSON ladder, session `person_id`, selected-tier fields and expectation snapshots; add item `item_type` and JSON `turn_decision`; add `AIUsage` with only identifiers, operation, model, input/output tokens, and timestamp. Define a discriminated Pydantic union for `continue` (question required) and `evaluate` (evaluation required).

- [x] **Step 4: Run targeted tests.**

Run: `pytest tests/test_models.py tests/test_adaptive_schemas.py -v`
Expected: PASS.

- [x] **Step 5: Commit.**

```bash
git add backend/app/models.py backend/app/schemas.py backend/tests/test_models.py backend/tests/test_adaptive_schemas.py
git commit -m "feat: add adaptive assessment data contracts"
```

### Task 2: Unified provider contract and deterministic mock

**Files:** Modify `backend/app/ai/base.py`, `backend/app/ai/mock.py`, `backend/tests/test_mock_provider.py`.

**Interfaces:** Consumes Task 1 schemas. Produces `resolve_role_ladder(title, existing_roles)`, `start_item(session)`, and `advance_assessment(role, snapshot, history, constraints) -> AdaptiveTurnOutput`.

- [x] **Step 1: Add failing mock tests** for a generated ordered ladder, forced continuation with fewer than three answers, deterministic completion at three detailed answers, and evaluation at ten answers.
- [x] **Step 2: Run:** `pytest tests/test_mock_provider.py -v` — expect failures for missing methods.
- [x] **Step 3: Implement the protocol and mock.** Make the mock return a stable three-tier ladder, target uncovered expectations in its question text, and return token counts with each operation. Its `advance_assessment` must never return evaluate before the supplied minimum and must evaluate when supplied `force_evaluate=True`.
- [x] **Step 4: Run:** `pytest tests/test_mock_provider.py -v` — expect PASS.
- [x] **Step 5: Commit** with message `feat: add adaptive AI provider contract`.

### Task 3: OpenAI and Anthropic adaptive turns with usage

**Files:** Modify `backend/app/ai/openai_provider.py`, `backend/app/ai/anthropic_provider.py`, `backend/tests/test_openai_provider.py`, `backend/tests/test_anthropic_provider.py`.

**Interfaces:** Consumes Task 2 protocol; produces provider responses that include parsed `AdaptiveTurnOutput` and normalized `Usage(input_tokens, output_tokens, model)`.

- [x] **Step 1: Add failing fake-client tests.** Assert both providers parse `AdaptiveTurnOutput`, receive the full transcript and selected-tier snapshot, and map returned token usage without retaining prompt text.
- [x] **Step 2: Run:** `pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -v` — expect failures.
- [x] **Step 3: Implement minimal prompts and parsing.** The prompt must state the selected tier, next-tier target, full transcript, allowed item type, and server `must_continue`/`must_evaluate` constraint. Keep `store=False` for OpenAI.
- [x] **Step 4: Run:** `pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -v` — expect PASS.
- [x] **Step 5: Commit** with message `feat: support adaptive turns in real providers`.

### Task 4: Person, ladder-selection, and safe session API

**Files:** Modify `backend/app/routers/sessions.py`, `backend/app/routers/employee.py`, `backend/app/employees.py`, `backend/tests/test_sessions_api.py`, `backend/tests/test_employee_status.py`; create `backend/tests/test_people_api.py`.

**Interfaces:** Expose `POST /people/resolve`, `POST /roles/resolve`, `POST /sessions`, `POST /sessions/{id}/answer`, and `GET /people/{id}/status`. Return a saved-answer retry state when an adaptive turn fails.

- [x] **Step 1: Write failing API tests** covering same-name profile reuse, role ladder response, tier-required session creation, completed result at answer three, continued result before the cap, forced result at answer ten, one evaluation after retry, immutable snapshots, and persisted usage rows.
- [x] **Step 2: Run:** `pytest tests/test_people_api.py tests/test_sessions_api.py tests/test_employee_status.py -v` — expect failures.
- [x] **Step 3: Implement routes transactionally.** Save the answer first; if no turn result exists for that item, request and persist exactly one adaptive decision plus usage. On retry, reuse a persisted decision/evaluation rather than calling the provider again. Regenerate a legacy role ladder before exposing tiers.
- [x] **Step 4: Run:** `pytest tests/test_people_api.py tests/test_sessions_api.py tests/test_employee_status.py -v` — expect PASS.
- [x] **Step 5: Commit** with message `feat: add adaptive assessment session API`.

### Task 5: Accessible personalized assessment UI

**Files:** Modify `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/types.ts`, `frontend/src/screens/HomeScreen.tsx`, `frontend/src/screens/StartScreen.tsx`, `frontend/src/screens/QuestionScreen.tsx`; create `frontend/src/screens/TierScreen.tsx`; modify `frontend/e2e/helpers.ts`, `frontend/e2e/golden-path.spec.ts`; create `frontend/e2e/profile-history.spec.ts`.

**Interfaces:** Consumes Task 4 APIs. `TierScreen` accepts `tiers`, selected tier id, `onSelect`, loading, and error. The question screen receives answered count and renders the public “short, adaptive conversation” progress copy only.

- [x] **Step 1: Write failing Playwright tests.** Cover entering a display name, selecting a generated tier, completing after the mock's third answer, revisiting that named profile's result, and keyboard selection/error announcements.
- [x] **Step 2: Run:** `npm run test:e2e -- golden-path.spec.ts profile-history.spec.ts` — expect failures.
- [x] **Step 3: Implement the smallest accessible flow.** Use labelled inputs and native buttons/radio controls; maintain focus after screen changes; use `role="alert"` for API errors. Do not display confidence, uncertainty, or internal decision metadata.
- [x] **Step 4: Run:** `npm run build` then `npm run test:e2e -- golden-path.spec.ts profile-history.spec.ts` — expect PASS.
- [x] **Step 5: Commit** with message `feat: add personalized adaptive assessment flow`.

### Task 6: End-to-end verification and operational documentation

**Files:** Modify `README.md`, `backend/tests/test_health.py` only if configuration assertions require it.

- [x] **Step 1: Add README documentation** for display-name prototype identity, 3–10 prompt behavior, provider token usage records, and the fact that no practical tests execute in this release.
- [x] **Step 2: Run backend suite:** `pytest tests/ -v` — expected PASS.
- [x] **Step 3: Run frontend verification:** `npm run build` and `npm run test:e2e` — expected PASS with backend/frontend/Postgres running.
- [x] **Step 4: Inspect:** `git diff --check` and `git status --short` — expected no whitespace errors and only intended changes.
- [x] **Step 5: Commit** with message `docs: explain adaptive assessment behavior`.

## Integrated verification (2026-09-06)

All six tasks are complete. The full backend suite passed (101 tests), and the
real-stack mock E2E suite passed (11 tests) with isolated backend port 18000 and
`anchor_adaptive_e2e`. TypeScript, production build, and lint passed. Backend
fixtures use the separate `employee_eval_test` database. Provider SDK tests use
fake clients; no paid AI calls were made. See README for reproducible commands.
