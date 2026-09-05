import { useState } from "react";

interface StartScreenProps {
  onStart: (roleTitle: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function StartScreen({ onStart, isLoading, error }: StartScreenProps) {
  const [roleTitle, setRoleTitle] = useState("");

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-lg">
        <p className="font-sans text-sm text-ink-muted mb-3">Skill assessment</p>
        <p className="font-serif text-3xl leading-snug text-ink mb-8">
          Let's talk through your role. What's your current title?
        </p>
        <label htmlFor="role-title" className="sr-only">
          Your current role
        </label>
        <input
          id="role-title"
          data-testid="role-title-input"
          className="w-full bg-paper-light border border-ink/15 rounded-md px-4 py-3 font-sans text-ink placeholder:text-ink-muted/70 mb-5 focus:outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal"
          value={roleTitle}
          onChange={(e) => setRoleTitle(e.target.value)}
          placeholder="e.g. Software Engineer"
        />
        {error && (
          <p className="font-sans text-sm text-rose mb-5" role="alert">
            {error}
          </p>
        )}
        <button
          data-testid="start-button"
          className="font-sans font-medium text-paper-light bg-teal px-5 py-3 rounded-md disabled:opacity-50 hover:bg-teal/90 transition-colors"
          disabled={isLoading || roleTitle.trim().length === 0}
          onClick={() => onStart(roleTitle.trim())}
        >
          {isLoading ? "Starting..." : "Start the conversation"}
        </button>
      </div>
    </div>
  );
}
