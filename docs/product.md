# Anchor

## Problem

Assessing whether an employee's skills are below, meeting, or exceeding
expectations for their role today relies on manual, ad-hoc review — generic
questionnaires that aren't tailored to the role, no consistent record of what
was actually asked or answered, and evaluations that vary by whoever runs
them. This app should replace that with a consistent, role-aware, AI-driven
assessment process that produces a defensible, repeatable evaluation.

Just as important as the evaluation itself: this tool exists to help people
grow, not just to measure them. An employee walking away should feel
encouraged and motivated by a concrete, personal next step — regardless of
verdict — not like they were graded and sent away. That framing should carry
through the whole experience, not just the recommendation text at the end.

## Users

- **Employee** — takes the assessment; answers a dynamic, role-relevant
  questionnaire.
- **Manager** — reviews an employee's evaluation results and rationale.
- **HR / people ops (admin)** — configures roles/tiers, launches assessment
  cycles, and has visibility across employees.

## Core functionality

- Role tiers and their expectations are not hardcoded. On first use of a
  role, an AI agent infers that role's career ladder (e.g. junior → senior
  developer, manager → senior manager) and the skill expectations for the
  employee's current tier and the next tier, using its general knowledge —
  since progression paths differ too much by job family to maintain by
  hand.
  - The inferred rubric is persisted per role and reused for later sessions
    of that role, so results stay consistent and auditable instead of being
    regenerated (and potentially drifting) every session. An admin can
    force a regeneration if a rubric needs updating.
  - Before generating a new rubric, the agent checks whether an existing
    role is effectively the same job (e.g. "Solution Developer" vs.
    "Software Engineer") and reuses that rubric instead of treating similar
    titles as distinct roles. Roles are matched by responsibilities/skills,
    not by title string matching.
  - Matching is LLM-judged: the agent compares the new role against
    existing roles and decides if one is an equivalent match. If the LLM
    isn't confident (ambiguous/borderline match), it falls back to asking
    the admin to confirm or reject the match instead of guessing.
- Before starting an assessment, the employee sees a brief welcome step that
  sets expectations and tone: what this is for (growth and recommendations,
  not a pass/fail exam), roughly what to expect (a short conversation), and
  that it leads to a concrete next step regardless of outcome. This is what
  primes the supportive, coaching framing the rest of the experience is
  built around — the assessment itself shouldn't be the employee's first
  signal of what this tool is for.
- Start an assessment session for an employee against their current role.
- AI agent dynamically generates role-relevant questions for the session,
  adapting based on prior answers within that session.
  - Session length is not fixed. After each answer, the agent decides
    whether it has enough information to reach a confident verdict, or
    whether it needs to probe further — with another question or a more
    hands-on/practical exercise — before it can. The session ends as soon
    as the agent is confident, not on a preset question count.
  - Regardless of how confident the agent is, a session is capped at 50
    questions/exercises. Most people lose focus well before that point, so
    a session that hasn't converged by 50 should end and be evaluated on
    what it has rather than keep probing indefinitely.
- Session context (all QA pairs) is preserved and sent to the evaluation
  agent so the evaluation reflects the full conversation, not just the last
  answer.
- Evaluation agent scores the session and produces a structured verdict:
  below / meeting / exceeding expectations for the role tier, with
  supporting rationale.
- Evaluation agent also produces a learning recommendation tailored to the
  verdict:
  - **Below expectations** — recommend what to learn to close the gap to
    the current role tier's expectations.
  - **Meeting or exceeding expectations** — recommend what to learn to
    reach the next role tier.
- Employees, managers, and admins can view past sessions and their results
  (scoped to what each role is permitted to see).
- Assessment cadence is adaptive per employee, not a fixed company-wide
  cycle — roughly every six months to a year as a default rhythm, but an
  employee who already feels well-placed and is performing well can go
  longer between check-ins, or skip them, without it being flagged as
  overdue. The tool surfaces where someone stands (e.g. "last check-in:
  7 months ago") as an open invitation, never as a compliance deadline.

## Application structure

This tool is used occasionally, not daily, and usage looks different by
role — so it shouldn't be built like a dense, always-on platform (e.g. a
university LMS with a persistent multi-level sidebar for juggling many
concurrent courses). Nothing about this product needs that: employees
don't have many parallel assessments to navigate between, and the core
experience isn't something people check into routinely.

- **Employee experience** — minimal chrome. A simple home screen shows
  where they stand (their own check-in status/history, framed as an
  invitation rather than a deadline) and leads into the assessment
  conversation itself, which stays a focused, full-screen, distraction-free
  experience — closer to a conversational survey tool than a page inside a
  larger app shell.
- **Manager/admin experience** — closer to a conventional lightweight
  dashboard: a list/table of their team, or of role configuration,
  sortable by things like time since last check-in, so a manager can
  notice who might be due without the system forcing a cycle on anyone.
- Global navigation stays minimal across the whole app (a slim top bar,
  not a dense persistent sidebar) — this product doesn't have the "many
  concurrent things to juggle" problem that heavier navigation exists to
  solve.

## User flows

1. **Take an assessment** — Employee opens the tool and sees a brief welcome
   step (what this is, why it exists, what to expect) → starts a session
   for their role → AI asks a question → employee answers → AI asks the
   next role-relevant question (or hands-on exercise) using prior context
   → ... → the agent decides it has enough information (or the
   50-question/exercise cap is reached) → session ends → evaluation agent
   scores the full session → result and learning recommendation are stored
   and shown.
2. **Review results** — Manager/admin opens a completed session → sees the
   verdict (below/meeting/exceeding), rationale, learning recommendation,
   and the underlying QA transcript.
3. **Configure roles** — Admin enters a role title (e.g. from a new
   employee's job title) → agent checks for an existing, effectively-equal
   role and reuses its rubric, or infers a new career ladder and tier
   rubric for it → admin can review and force regeneration if needed.

## Future direction

Not yet designed or scheduled — noted here so it shapes decisions along the
way (e.g. not building anything that would make this harder later), not as
a commitment to build it next.

- **Role-fit assessment.** Today's assessment always evaluates an employee
  against the role they say they currently hold. At some point, this should
  extend to a different question: given what an employee has demonstrated
  and cares about, which role might actually be the most fitting, rewarding
  place for them — not necessarily the one they're in today. This is a
  career-pathing / internal-mobility capability, distinct from "how are you
  doing in your current role," meant to inform a discussion between the
  employee and their manager, not to hand down an automated verdict.

  The goal is a rounded picture of fit, not a single score, drawn from
  established, well-evidenced frameworks rather than pop-psychology
  instruments — and surfaced through the same kind of ongoing coaching
  conversation the rest of this tool uses, not a battery of separate
  formal tests:
  - **Person-job fit** — already covered by the existing skill assessment.
  - **Person-vocation fit** — what kind of work energizes this person at
    all, drawing on Holland's RIASEC interest model (well-validated,
    already standard in career counseling) and Schein's Career Anchors
    (what someone would never trade away in a career — autonomy, technical
    mastery, stability, managing people, pure challenge, service to a
    cause, and so on). Schein's own method for surfacing anchors is a
    structured interview, which maps directly onto a coaching conversation.
  - **Motivation** — grounded in Self-Determination Theory (autonomy,
    competence, relatedness), the strongest evidence base for what makes
    work intrinsically motivating for a specific person. This fits the
    tool's actual goal (encourage and motivate) better than personality
    typing does.
  - **Work style**, if it's included at all — Big Five (OCEAN), inferred
    from how someone talks about their work across the conversation rather
    than a forced-choice quiz. Not MBTI: it's popular but has weak
    test-retest reliability and doesn't reliably predict job or role
    performance in the actual research.

  Deliberately excluded: any clinical or licensed psychometric instrument,
  and anything about an employee's personal life or circumstances (family
  status, health, life stage) — several of those are protected categories
  in most jurisdictions, and using them to inform role/job decisions is
  real discrimination-liability territory even if unintentional. Logistics
  preferences (remote/on-site, travel, shift flexibility) are fine; a
  person's life circumstances are not.

## Out of scope

- Payroll, compensation, or promotion decisions (this tool informs, not
  decides, those processes).
- Peer or 360-degree feedback collection.
- Real-time proctoring or anti-cheating enforcement during a session.

## Success criteria

- An employee can complete a full assessment session end-to-end without
  manual intervention.
- Evaluation verdicts are consistent for similar answers across sessions
  (same rubric applied reliably).
- Managers/admins can find and understand a past evaluation's rationale
  without needing to re-read the raw transcript.
