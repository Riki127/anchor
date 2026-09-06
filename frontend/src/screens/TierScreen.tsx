import type { Role } from "../types";

interface TierScreenProps {
  role: Role;
  tierId: string;
  onSelect: (id: string) => void;
  onContinue: () => void;
  onBack: () => void;
}

export function TierScreen({ role, tierId, onSelect, onContinue, onBack }: TierScreenProps) {
  return (
    <form onSubmit={(event) => { event.preventDefault(); onContinue(); }}>
      <p className="mb-6">{role.ladder.career_ladder_summary}</p>
      <fieldset>
        <legend className="font-medium mb-3">Level for {role.title}</legend>
        {role.ladder.tiers.map((tier) => (
          <label className="block border border-ink-muted rounded-md p-4 mb-3" key={tier.id}>
            <span className="flex gap-3 items-center">
              <input
                type="radio"
                name="tier"
                required
                value={tier.id}
                checked={tierId === tier.id}
                onChange={() => onSelect(tier.id)}
              />
              <span className="font-medium">{tier.name}</span>
            </span>
            <ul className="list-disc ml-8 mt-2">
              {tier.expectations.map((expectation) => <li key={expectation}>{expectation}</li>)}
            </ul>
          </label>
        ))}
      </fieldset>
      <button>Continue</button>
      <button type="button" className="secondary" onClick={onBack}>Back to role</button>
    </form>
  );
}
