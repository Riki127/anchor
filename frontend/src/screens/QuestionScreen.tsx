import { useState } from "react";

export interface QAEntry {
  question: string;
  answer: string;
}

interface QuestionScreenProps {
  question: string;
  history: QAEntry[];
  onSubmit: (answer: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function QuestionScreen({ question, history, onSubmit, isLoading, error }: QuestionScreenProps) {
  const [answer, setAnswer] = useState("");

  return (
    <div className="min-h-screen flex justify-center px-6 py-16">
      <div className="w-full max-w-lg">
        {history.length > 0 && (
          <div className="mb-10 space-y-6 border-l-2 border-ink/10 pl-5">
            {history.map((entry, index) => (
              <div key={index}>
                <p className="font-serif text-base text-ink-muted leading-snug mb-1">{entry.question}</p>
                <p className="font-sans text-sm text-ink-muted/80">{entry.answer}</p>
              </div>
            ))}
          </div>
        )}

        <p data-testid="question-text" className="font-serif text-2xl leading-snug text-ink mb-6">
          {question}
        </p>
        <textarea
          data-testid="answer-input"
          className="w-full bg-paper-light border border-ink/15 rounded-md px-4 py-3 font-sans text-ink placeholder:text-ink-muted/70 mb-5 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal"
          rows={4}
          value={answer}
          disabled={isLoading}
          onChange={(e) => setAnswer(e.target.value)}
        />
        {error && (
          <p className="font-sans text-sm text-rose mb-5" role="alert">
            {error}
          </p>
        )}
        <button
          data-testid="submit-answer-button"
          className="font-sans font-medium text-paper-light bg-teal px-5 py-3 rounded-md disabled:opacity-50 hover:bg-teal/90 transition-colors"
          disabled={isLoading || answer.trim().length === 0}
          onClick={() => onSubmit(answer.trim())}
        >
          {isLoading ? "Sending..." : "Continue"}
        </button>
      </div>
    </div>
  );
}
