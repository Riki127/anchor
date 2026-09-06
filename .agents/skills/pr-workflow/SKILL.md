---
name: pr-workflow
description: Apply Anchor's conventions when finishing a feature, preparing a pull request, merging, pushing, or starting a separate deliverable. Use for requests such as "open a PR", "ready to merge", "wrap this up", or "push this up"; also consult it before starting a clearly separate feature.
---

# PR Workflow (Anchor)

Use this skill together with the standard branch-finishing workflow. This skill
adds Anchor's project conventions for pull requests and feature branches.

## Creating pull requests

When the user chooses to create a PR, push the branch and create the PR with
the GitHub CLI (`gh pr create --title ... --body ...`). Confirm the GitHub CLI
is authenticated with `gh auth status` first. If no active login exists, ask
the user to run `gh auth login`; do not request a token or work around the
authentication flow.

Before creating a PR, surface a short, imperative, specific title and a
reviewer-oriented description explaining what changed and why it matters. This
project grants standing authorization to create the PR once those are shown;
do not ask for a second approval unless the correct base branch or intended PR
scope is genuinely unclear.

If the user has already said they will create a particular in-flight PR, leave
that PR for them to create.

## Feature branches

Start each conceptually separate feature or deliverable on a fresh, descriptive
branch and isolated worktree. Follow the available worktree workflow for the
environment, using a branch name that describes the feature.

Continue using the existing branch for review feedback, fixes to unmerged work,
or a small continuation of the same deliverable. If it is genuinely ambiguous
whether work belongs to an open branch or a new feature, ask the user.
