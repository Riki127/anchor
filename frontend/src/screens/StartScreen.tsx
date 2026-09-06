interface StartScreenProps {
  roleTitle: string;
  onRoleTitleChange: (title: string) => void;
  onStart: () => void;
  isLoading: boolean;
  error: string;
}

export function StartScreen({ roleTitle, onRoleTitleChange, onStart, isLoading, error }: StartScreenProps) {
  return (
    <form onSubmit={(event) => { event.preventDefault(); onStart(); }}>
      <label htmlFor="role-title">Role to explore</label>
      <input
        id="role-title"
        required
        disabled={isLoading}
        value={roleTitle}
        onChange={(event) => onRoleTitleChange(event.target.value)}
        aria-invalid={!!error}
        aria-describedby="form-error"
        placeholder="e.g. Software Engineer"
      />
      <button disabled={isLoading}>Explore role</button>
    </form>
  );
}
