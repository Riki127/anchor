import { useState } from "react";

export interface QAEntry {
  question: string;
  answer: string;
}

interface QuestionScreenProps {
  history: QAEntry[];
  onSubmit: (answer: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function QuestionScreen({ history, onSubmit, isLoading, error }: QuestionScreenProps) {
  const [answer, setAnswer] = useState("");

  return (
    <>
      <p className="mb-4">Question {history.length + 1}</p>
      <form onSubmit={(event) => {
        event.preventDefault();
        if (answer.trim()) onSubmit(answer.trim());
      }}>
        <label htmlFor="answer">Your answer</label>
        <textarea
          id="answer"
          required
          rows={5}
          value={answer}
          disabled={isLoading}
          onChange={(event) => setAnswer(event.target.value)}
          aria-invalid={!!error}
          aria-describedby="form-error"
        />
        <button disabled={isLoading || !answer.trim()}>Continue</button>
      </form>
      {history.length > 0 && (
        <details className="mt-8">
          <summary>Your earlier answers</summary>
          {history.map((entry, index) => (
            <div key={index} className="mt-4">
              <h2 className="font-serif text-lg">{entry.question}</h2>
              <p className="mt-2 whitespace-pre-wrap">{entry.answer}</p>
            </div>
          ))}
        </details>
      )}
    </>
  );
}
