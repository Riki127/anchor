interface ProfileScreenProps {
  name: string;
  onNameChange: (name: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  error: string;
}

export function ProfileScreen({ name, onNameChange, onSubmit, isLoading, error }: ProfileScreenProps) {
  return (
    <>
      <p className="mb-6">
        An honest conversation and a concrete next step. Your name opens a reusable
        profile on this prototype; it is not a secure sign-in.
      </p>
      <form onSubmit={(event) => { event.preventDefault(); onSubmit(); }}>
        <label htmlFor="name">Your name</label>
        <input
          id="name"
          autoComplete="name"
          required
          disabled={isLoading}
          value={name}
          onChange={(event) => onNameChange(event.target.value)}
          aria-invalid={!!error}
          aria-describedby="form-error"
        />
        <button disabled={isLoading}>Continue</button>
      </form>
    </>
  );
}
