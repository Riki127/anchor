# Claude Code Instructions

Read and follow `AGENTS.md`.

## Claude-specific behavior

- Use the available project skills when relevant.
- Inspect existing code before making architectural decisions.
- Run verification after implementation.
- Before making any real call to the Anthropic API (i.e. running with
  `AI_PROVIDER=anthropic` rather than the mock provider), ask for explicit
  permission every time, even if a similar call was already approved earlier
  in the same session. When approved, keep the call as cost-efficient as
  possible: minimize the number of calls, use reasonable `max_tokens`, and
  prefer testing one thing at a time over a full end-to-end run unless that's
  specifically what's being verified. Real API usage costs real money against
  the user's own account.