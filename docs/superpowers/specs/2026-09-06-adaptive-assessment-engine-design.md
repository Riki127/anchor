# Adaptive, Rubric-Backed Assessment Engine

**Status:** Approved for implementation planning
**Date:** 2026-09-06

## Purpose

Evolve Anchor from a fixed five-question proof of concept into an employee-led,
personalized coaching assessment. A person identifies themselves with a
lightweight display-name profile, chooses a role and its applicable career tier,
then completes a short adaptive conversation. Anchor asks only the questions
needed to reach a useful, auditable result.

The assessment must also work for people who are not currently employed and want
to understand their readiness for a role.

## Goals

- Persist a reusable AI-generated career ladder for each role.
- Let a person select the tier assessed for each session.
- Adapt from three through ten answered items, ending on sufficient evidence or
  at the ten-item cap.
- Record compact, structured evidence coverage, uncertainty, and confidence;
  never expose private model reasoning in the UI.
- Record token usage by operation to measure cost from real use.
- Preserve a stable rubric snapshot for every session and completed result.
- Make assessment items ready for future practical exercises while shipping
  conversational questions only.

## Non-goals

- Authentication, organization membership, and account recovery.
- Manager-initiated sessions, manager-selected tiers, and admin role management.
- Exercise delivery or grading, code execution, file uploads, and spreadsheets.

## User flow

1. A person enters a display name. Anchor creates or reuses a lightweight local
   profile and shows that person's session history.
2. The person enters a role title. Anchor reuses an equivalent stored role or
   creates a role with an AI-generated career ladder.
3. Anchor presents the ladder; the person selects a tier for this session.
4. A welcome explains the coaching purpose and that the conversation normally
   takes three to ten prompts.
5. Anchor asks the first conversational item. Each answer advances one
   structured adaptive turn.
6. From three answers onward, the AI can continue with a targeted question or
   finish with a verdict, rationale, and concrete learning recommendation. At
   ten answers, completion is required.
7. The result is stored and visible in the person's history.

## Data model

### Person

Replace the seeded single-employee assumption with `Person(id, display_name,
created_at, updated_at)`. This is deliberately a prototype identity layer. A
later verified identity system can attach to a person without changing session
ownership.

### Role and career ladder

Store a versioned role rubric containing a career-ladder summary and ordered
tiers. Each tier has a stable identifier, display name, and expectations.

The existing two-list rubric (`current_tier_expectations` and
`next_tier_expectations`) is legacy because it cannot support tier selection.
When a legacy role is used for a new assessment, regenerate its complete ladder
before a session can start.

### Assessment session

Each session references a person and role and stores:

- selected tier identifier and display name;
- snapshot of selected-tier expectations and immediate next-tier expectations,
  when a next tier exists;
- rubric version; and
- existing status and timestamps.

Snapshots ensure a rubric refresh never changes the meaning of completed work.

### Assessment item and decision

The current question/answer record becomes an assessment item. This milestone
creates only `conversation_question`, but the contract reserves
`practical_exercise` for future work.

Each answered item persists a compact decision: `continue` or `evaluate`,
confidence, covered expectations, remaining uncertainties, and either a next
item or final evaluation. It does not store hidden reasoning or chain-of-thought.

### AI usage

Persist session or role reference, operation type, provider/model, input tokens,
output tokens, and timestamp. Usage records do not duplicate prompts or answers.

## Provider contract and guardrails

The provider interface gains an adaptive-turn operation. It receives the role,
session rubric snapshot, complete item/answer history, and server constraints.
It returns one discriminated result:

- **Continue:** decision metadata and the next conversational question.
- **Evaluate:** decision metadata and verdict, rationale, and recommendation.

The terminal evaluation is part of the same response; Anchor makes no separate
stop-decision or final-evaluation request. This is intentionally cost-efficient
and reduces failure coordination.

The server independently enforces limits:

- 0–2 answered items: continuation required;
- 3–9: provider may continue or evaluate;
- 10: evaluation required.

The deterministic mock, Anthropic, and OpenAI providers share this Pydantic
structured-output contract.

## Failure handling and UI

The server commits an answer before requesting an adaptive turn. If a provider
request fails, the saved answer can be retried safely: no duplicate next items
or evaluations may be created. The UI explains that the conversation is short
and adaptive, but does not reveal confidence values, uncertainty lists, or model
reasoning. Accessibility requirements continue to apply to errors and controls.

## Future practical exercises

The item type makes future role-specific exercises possible: code, written,
file, or spreadsheet responses can target the same tier expectations as a
conversation item. They are deferred to dedicated vertical slices. Code must run
in isolated infrastructure with strict resource limits and no access to Anchor's
application or database. Accounting/spreadsheet exercises need accessible
alternatives and reviewed scoring criteria. Anchor must not freely invent
high-stakes practical tests without reviewed templates and rubrics.

## Migration and verification

Existing completed POC sessions remain readable and are never silently rewritten.
Legacy roles receive a new ladder before their next session; new sessions always
save snapshots.

- Test ladder generation/reuse and tier selection.
- Test mock completion at three items, continued probing, and forced completion
  at ten.
- Test immutable snapshots, persisted decisions, retry safety, and exactly one
  terminal evaluation.
- Test usage metadata without storing prompt or answer copies.
- Test frontend profile, ladder selection, adaptive progress, and accessible
  error paths.
- Validate OpenAI and Anthropic against the shared output contract.

## Cost expectation

Adaptive metadata is combined with the existing next-item operation rather than
added as a second request. At `gpt-5.6-terra` pricing, the richer metadata is
expected to add less than one cent to a short assessment and roughly one to two
cents at the ten-item cap. Persisted usage replaces this estimate with observed
pilot data.
