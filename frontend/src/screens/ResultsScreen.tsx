import type { Verdict } from "../types";

interface ResultsScreenProps {
  verdict: Verdict;
  rationale: string;
  recommendation: string;
}

const VERDICT_LABEL: Record<Verdict, string> = {
  below: "Below expectations",
  meeting: "Meeting expectations",
  exceeding: "Exceeding expectations",
};

export function ResultsScreen({ verdict, rationale, recommendation }: ResultsScreenProps) {
  return (
    <div className="min-h-screen flex justify-center px-6 py-16">
      <div className="w-full max-w-lg">
        <p className="font-sans text-sm text-ink-muted mb-1">Where things stand</p>
        <p data-testid="verdict" className="font-serif text-xl text-ink mb-6">
          {VERDICT_LABEL[verdict]}
        </p>
        <p data-testid="rationale" className="font-sans text-ink-muted leading-relaxed mb-10">
          {rationale}
        </p>

        <div className="bg-gold-light border border-gold/30 rounded-lg px-6 py-6">
          <p className="font-sans text-sm font-medium text-ink mb-2">What to focus on next</p>
          <p data-testid="recommendation" className="font-serif text-lg leading-snug text-ink">
            {recommendation}
          </p>
        </div>
      </div>
    </div>
  );
}
