# Task 4 report

Implemented person and role resolution, adaptive sessions with immutable tier snapshots,
parent-row locking and item-specific retry replay, saved answers before provider calls,
atomic decisions/next items/evaluations/usage, and legacy compatibility.

## Frontend endpoint contracts

- `POST /people/resolve {display_name}` -> `{id, display_name}`. Whitespace is collapsed;
  matching is case-insensitive. This is prototype identity, not authentication.
- `GET /people/{id}/status` -> `{id, display_name, sessions: [{id, role_title,
  selected_tier_name, completed_at, verdict}]}`. Only completed sessions, newest first.
- `POST /roles/resolve {title}` -> `{id, title, rubric_version, ladder:
  {career_ladder_summary, tiers: [{id, name, expectations}]}}`.
- `POST /sessions {person_id, role_id, tier_id}` ->
  `{session_id, role_id, item_id, question}`. No mixed/partial legacy and adaptive fields.
- `POST /sessions/{id}/answer {item_id, answer}` -> `{status, item_id, question,
  verdict, rationale, recommendation}`. Continue returns next item_id and question;
  completion returns verdict/rationale/recommendation. Irrelevant fields are null.
  Retry exactly the same item_id and answer after 502. A completed decision replays
  its original response, including the original next item ID even after later completion.
  Changed saved answers and foreign/out-of-order items return 409; missing item_id 422.
- `GET /sessions/{id}` -> `{id, status, role_title, person_id, selected_tier_id,
  selected_tier_name, qa_pairs: [{item_id, order, question, answer}], verdict,
  rationale, recommendation}`. Audit/confidence/uncertainty metadata is omitted.

Legacy `{role_title}` start/answer paths remain fixed-count; completed records remain
readable. Legacy rubrics are preserved when upgraded. Newly generated roles also hold
a compatible first/next-tier legacy rubric so mixed clients continue working.

## Verification

First adaptive API test failed against absent endpoints before implementation.
Final full suite: `python -m pytest -q -p no:cacheprovider` in backend: **96 passed**.
Python used: `G:/repo/anchor/.worktrees/openai-provider/backend/.venv/Scripts/python.exe`.
Only dedicated `employee_eval_test` DB was mutated; no paid/live provider calls.

Coverage includes concurrent identical submissions using independent PostgreSQL
sessions (one provider advancement, one next item); saved-answer failure retry;
stale replay after completion; 3/10 bounds and invalid provider choices; full ordered
answered history; usage fields; history ownership; immutable snapshot; invalid tier,
person, role and item IDs; invalid/mismatched ladders; atomic startup failure; exact
role reuse and legacy role regeneration; and mixed legacy/adaptive role reuse.

Migration test reconstructs old columns with employee_id NOT NULL, runs migration,
checks preserved legacy data, reruns migration for idempotence, and inserts a
person-only session. Production/user DBs were not reset.
