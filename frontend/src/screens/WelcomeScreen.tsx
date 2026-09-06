interface WelcomeScreenProps {
  roleTitle: string;
  tierName: string;
  isLoading: boolean;
  onStart: () => void;
  onBack: () => void;
}

export function WelcomeScreen({ roleTitle, tierName, isLoading, onStart, onBack }: WelcomeScreenProps) {
  return (
    <>
      <p className="font-serif text-xl mb-4">{roleTitle} · {tierName}</p>
      <p className="mb-6">
        Share concrete examples from work, study, or personal projects. The coach
        will adapt as you answer, asking between 3 and 10 questions before suggesting
        your next step.
      </p>
      <button disabled={isLoading} onClick={onStart}>Start the conversation</button>
      <button className="secondary" disabled={isLoading} onClick={onBack}>Back to levels</button>
    </>
  );
}
