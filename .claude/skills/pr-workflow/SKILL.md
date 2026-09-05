---
name: pr-workflow
description: This project's conventions for finishing work and opening a pull request in Anchor. Use this whenever wrapping up a feature, getting ready to open a PR, or the user says things like "let's do a PR", "let's open a PR", "ready to merge this", "let's wrap this up", "push this up", or similar - even if they don't spell out every convention, since the whole point of this skill is to apply them without being asked each time. Also consult it at the START of new work that's clearly a separate feature/deliverable from whatever is already merged or already has an open PR, since it governs which branch that work should start on.
---

# PR Workflow (Anchor)

Two things this project does differently from the generic default, on top of
whatever `finishing-a-development-branch` already handles (test verification,
the merge/PR/keep-as-is menu, worktree cleanup mechanics - read that skill for
those mechanics; this one is just the project-specific layer on top).

## 1. Claude creates the PR itself, via `gh`

Push the branch, then run `gh pr create --title ... --body ...` and hand back
the resulting URL. This requires the GitHub CLI to be installed and
authenticated on the user's machine (`gh auth login` - their own OAuth flow;
Claude never sees or handles a token). If `gh auth status` shows no active
login, say so and ask the user to run `gh auth login` rather than trying a
workaround (raw API calls with a pasted token, browser automation, etc.).

Every time, before creating it:
- **Propose a title.** Short, imperative, specific to what the branch actually
  contains - not a generic "Update code" or the literal branch name. If the
  branch covers several distinct pieces of work, name the throughline, not
  every sub-item.
- Propose a description covering what changed and why a reviewer would care -
  not a commit-by-commit changelog.

This is a standing authorization from the user - once the title and
description are shown, create the PR without a separate "may I proceed?"
question each time; that's the whole point of the user setting this rule up
once instead of approving it per PR. Still surface the title/description so
they see it, and still stop and ask if something about a given PR is
genuinely ambiguous (e.g. unclear which base branch it targets).

**Exception:** an in-flight PR the user already said they'd create themselves
stays theirs to create, even after this rule is adopted - don't retroactively
take over a PR that was already being handled manually.

## 2. Each new feature/deliverable gets its own fresh branch

Don't keep layering unrelated work onto one long-lived branch/worktree
indefinitely - that produces a PR that's hard to review and hard to revert
as a unit. When starting work that is conceptually a *new* thing (not a
follow-up fix or review-response commit on work still in an open PR), start
it on a new branch:

- Use the native worktree tool (`EnterWorktree`) with a `name` that's
  descriptive of the feature (e.g. `dynamic-question-count`, `ui-redesign`),
  not a generic or timestamp-based name.
- This gives every future PR its own clean, focused commit history and its
  own branch name that reads as a real feature branch - not a worktree that
  happens to have accumulated several unrelated PRs' worth of commits over
  time.

**How to tell "new feature" from "still the same one":** if the work responds
to feedback on an open PR, fixes something in code that hasn't merged yet, or
is a small continuation of what's already there, it belongs on the existing
branch. If it's a new capability discussed as its own next step (a new
brainstorming pass, a new design conversation, "let's move to X next"), it
gets a new branch - ask the user if it's genuinely ambiguous which one an
idea falls into.
