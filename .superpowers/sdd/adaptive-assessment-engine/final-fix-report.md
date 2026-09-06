# Final copy fix report

## Change

Updated `frontend/src/api.ts` so a 502 from answer submission says to retry with the same saved answer, while 502s from other requests use generic retry guidance. No API or behavior changes were made.

## Verification

- `npm run lint` — unavailable because the configured global npm launcher references a missing `npm-cli.js`.
- `npm run build` — unavailable for the same npm launcher issue.
- `frontend/node_modules/.bin/oxlint` — passed (exit code 0).
- `frontend/node_modules/.bin/tsc -b` — passed (exit code 0).
- `frontend/node_modules/.bin/vite build` — passed (exit code 0).
