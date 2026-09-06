import { useState } from "react";
import type { Role } from "../types";

interface TierScreenProps {
  role: Role;
  tierId: string;
  onSelect: (id: string) => void;
  onContinue: () => void;
  onBack: () => void;
}

export function TierScreen({ role, tierId, onSelect, onContinue, onBack }: TierScreenProps) {
  const [reviewed, setReviewed] = useState(false);
  return (
    <form onSubmit={(event) => { event.preventDefault(); if (reviewed) onContinue(); }}>
      <p id="ladder-source" className="mb-3">These levels and expectations are an AI suggestion, not an employer-approved or verified career framework. Review them before choosing a level. If they do not fit, go back and explore a different role.</p>
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
                onChange={() => { setReviewed(false); onSelect(tier.id); }}
              />
              <span className="font-medium">{tier.name}</span>
            </span>
            <ul className="list-disc ml-8 mt-2">
              {tier.expectations.map((expectation) => <li key={expectation}>{expectation}</li>)}
            </ul>
          </label>
        ))}
      </fieldset>
      <label className="flex items-start gap-3 my-5">
        <input type="checkbox" required checked={reviewed} aria-describedby="ladder-source"
          onChange={(event) => setReviewed(event.target.checked)} />
        <span>I have reviewed this suggested ladder and the selected level, and they fit what I want to explore.</span>
      </label>
      <button>Continue</button>
      <button type="button" className="secondary" onClick={onBack}>Back to role</button>
    </form>
  );
}
