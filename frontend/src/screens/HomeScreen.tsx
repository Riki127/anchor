import type { PersonStatus } from "../types";

interface HomeScreenProps {
  status: PersonStatus | null;
  isLoading: boolean;
  onStartNew: () => void;
  onSwitchProfile: () => void;
  onRetry: () => void;
  onViewResult: (id: number) => void;
}

export function HomeScreen({ status, isLoading, onStartNew, onSwitchProfile, onRetry, onViewResult }: HomeScreenProps) {
  return (
    <>
      <p className="mb-6">
        Explore where you stand and what to focus on next, in your current role
        or one you are considering.
      </p>
      <button disabled={isLoading} onClick={onStartNew}>Start a new check-in</button>
      {!status && !isLoading && <button onClick={onRetry}>Retry loading profile</button>}
      <button className="secondary" disabled={isLoading} onClick={onSwitchProfile}>Switch profile</button>
      {status && (
        <section className="mt-10">
          <h2 className="font-serif text-xl mb-4">Your completed check-ins</h2>
          {status.sessions.length === 0 ? <p>No completed check-ins yet.</p> : (
            <ul className="space-y-4">
              {status.sessions.map((session) => (
                <li key={session.id} className="border-t border-ink-muted pt-4">
                  <p>{session.role_title} · {session.selected_tier_name ?? "Level not recorded"}</p>
                  <p className="text-sm">
                    {session.completed_at ? new Date(session.completed_at).toLocaleDateString() : "Date not recorded"}
                    {" · "}
                    {session.verdict ? `${session.verdict} expectations` : "Result not recorded"}
                  </p>
                  <button className="secondary" disabled={isLoading} onClick={() => onViewResult(session.id)}>
                    View result · {session.role_title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}
