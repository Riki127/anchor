import { useEffect, useState } from "react";

import { getEmployeeStatus } from "../api";
import { formatRelativeTime } from "../relativeTime";
import type { EmployeeStatus } from "../types";

interface HomeScreenProps {
  onStartNew: () => void;
  onViewLast: (sessionId: number) => void;
  isLoading: boolean;
  error: string | null;
}

export function HomeScreen({ onStartNew, onViewLast, isLoading, error }: HomeScreenProps) {
  const [status, setStatus] = useState<EmployeeStatus | null>(null);

  useEffect(() => {
    getEmployeeStatus()
      .then(setStatus)
      .catch(() => setStatus({ has_completed_session: false }));
  }, []);

  if (status === null) {
    return <div className="min-h-screen" />;
  }

  if (!status.has_completed_session) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="w-full max-w-lg">
          <p className="font-sans text-sm text-ink-muted mb-3">Welcome</p>
          <p className="font-serif text-3xl leading-snug text-ink mb-4">
            This is a space to check in on how things are going.
          </p>
          <p className="font-sans text-ink-muted leading-relaxed mb-8">
            No grading, no pass or fail — just an honest conversation and a clear, personal next
            step, whenever you're ready for it.
          </p>
          {error && (
            <p className="font-sans text-sm text-rose mb-5" role="alert">
              {error}
            </p>
          )}
          <button
            data-testid="get-started-button"
            className="font-sans font-medium text-paper-light bg-teal px-5 py-3 rounded-md disabled:opacity-50 hover:bg-teal/90 transition-colors"
            disabled={isLoading}
            onClick={onStartNew}
          >
            Get started
          </button>
        </div>
      </div>
    );
  }

  const lastCheckIn = status.last_completed_at ? formatRelativeTime(status.last_completed_at) : null;

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-lg">
        <p className="font-sans text-sm text-ink-muted mb-3">Welcome back</p>
        <p className="font-serif text-3xl leading-snug text-ink mb-4">
          {lastCheckIn ? `Last check-in: ${lastCheckIn}.` : "Ready for another check-in?"}
        </p>
        <p className="font-sans text-ink-muted leading-relaxed mb-8">
          Want to see how things have evolved, or revisit what came out of it last time?
        </p>
        {error && (
          <p className="font-sans text-sm text-rose mb-5" role="alert">
            {error}
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <button
            data-testid="start-new-button"
            className="font-sans font-medium text-paper-light bg-teal px-5 py-3 rounded-md disabled:opacity-50 hover:bg-teal/90 transition-colors"
            disabled={isLoading}
            onClick={onStartNew}
          >
            Start a new check-in
          </button>
          {status.last_session_id !== null && status.last_session_id !== undefined && (
            <button
              data-testid="view-last-button"
              className="font-sans font-medium text-ink border border-ink/20 px-5 py-3 rounded-md disabled:opacity-50 hover:bg-ink/5 transition-colors"
              disabled={isLoading}
              onClick={() => onViewLast(status.last_session_id as number)}
            >
              {isLoading ? "Loading..." : "View my last result"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
