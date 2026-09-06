import { useEffect, useRef, useState } from "react";

import { getPersonStatus, getSession, resolvePerson, resolveRole, startSession, submitAnswer } from "./api";
import { HomeScreen } from "./screens/HomeScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { QuestionScreen, type QAEntry } from "./screens/QuestionScreen";
import { ResultsScreen } from "./screens/ResultsScreen";
import { StartScreen } from "./screens/StartScreen";
import { TierScreen } from "./screens/TierScreen";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import type { Person, PersonStatus, Role, Verdict } from "./types";

type Screen = "profile" | "home" | "role" | "tier" | "welcome" | "question" | "results";

interface ActiveSession {
  id: number;
  item: number;
  question: string;
  history: QAEntry[];
}

interface Result {
  verdict: Verdict;
  rationale: string;
  recommendation: string;
  role: string;
  tier: string;
}

function rememberedPerson(): Person | null {
  try {
    const value: unknown = JSON.parse(localStorage.getItem("anchor.person") ?? "null");
    if (
      value && typeof value === "object" &&
      "id" in value && typeof value.id === "number" &&
      "display_name" in value && typeof value.display_name === "string"
    ) {
      return value as Person;
    }
  } catch {
    // Profiles still work when browser storage is unavailable.
  }
  return null;
}

export default function App() {
  const [person, setPerson] = useState<Person | null>(rememberedPerson);
  const [screen, setScreen] = useState<Screen>(() => rememberedPerson() ? "home" : "profile");
  const [status, setStatus] = useState<PersonStatus | null>(null);
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [role, setRole] = useState<Role | null>(null);
  const [tier, setTier] = useState("");
  const [session, setSession] = useState<ActiveSession | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(() => rememberedPerson() !== null);
  const [error, setError] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  const selected = role?.ladder.tiers.find((candidate) => candidate.id === tier);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!person) return;
    let active = true;
    getPersonStatus(person.id)
      .then((loaded) => { if (active) setStatus(loaded); })
      .catch((failure: unknown) => {
        if (active) {
          setError(failure instanceof Error ? failure.message : "Could not restore profile. Please retry.");
        }
      })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [person]);

  useEffect(() => {
    heading.current?.focus();
  }, [screen, session?.item]);

  function go(next: Screen) {
    setError("");
    setScreen(next);
  }

  function refreshProfile() {
    if (person) void run(async () => setStatus(await getPersonStatus(person.id)));
  }

  function home() {
    setStatus(null);
    go("home");
    refreshProfile();
  }

  function switchProfile() {
    try {
      localStorage.removeItem("anchor.person");
    } catch {
      // Browser storage is optional.
    }
    setPerson(null);
    setStatus(null);
    setName("");
    setRole(null);
    setTitle("");
    setTier("");
    setSession(null);
    setResult(null);
    go("profile");
  }

  function enterProfile() {
    if (!name.trim()) {
      setError("Enter your name.");
      document.getElementById("name")?.focus();
      return;
    }
    void run(async () => {
      const resolved = await resolvePerson(name.trim());
      // Load history before entering home so keyboard users can use its first action immediately.
      const loaded = await getPersonStatus(resolved.id);
      try {
        localStorage.setItem("anchor.person", JSON.stringify(resolved));
      } catch {
        // Continue without persistence when storage is unavailable.
      }
      setStatus(loaded);
      setPerson(resolved);
      go("home");
    });
  }

  function exploreRole() {
    if (!title.trim()) {
      setError("Enter a role to explore.");
      document.getElementById("role-title")?.focus();
      return;
    }
    void run(async () => {
      if (role?.title.toLowerCase() !== title.trim().toLowerCase()) {
        const resolved = await resolveRole(title.trim());
        // Preserve the selected tier when an alias resolves to the same role.
        if (resolved.id !== role?.id) setTier("");
        setRole(resolved);
      }
      go("tier");
    });
  }

  function beginSession() {
    if (!person || !role || !selected) return;
    void run(async () => {
      const started = await startSession(person.id, role.id, selected.id);
      setSession({ id: started.session_id, item: started.item_id, question: started.question, history: [] });
      go("question");
    });
  }

  function answerQuestion(answer: string) {
    if (!session || !role || !selected) return;
    void run(async () => {
      const response = await submitAnswer(session.id, session.item, answer);
      if (response.status === "completed" && response.verdict && response.rationale && response.recommendation) {
        setResult({
          verdict: response.verdict,
          rationale: response.rationale,
          recommendation: response.recommendation,
          role: role.title,
          tier: selected.name,
        });
        go("results");
      } else if (response.question && response.item_id) {
        setSession({
          ...session,
          item: response.item_id,
          question: response.question,
          history: [...session.history, { question: session.question, answer }],
        });
      } else {
        throw new Error("The coach returned an incomplete response. Please retry.");
      }
    });
  }

  function viewResult(id: number) {
    void run(async () => {
      const saved = await getSession(id);
      if (!saved.verdict || !saved.rationale || !saved.recommendation) {
        throw new Error("This check-in does not have a completed result yet.");
      }
      setResult({
        verdict: saved.verdict,
        rationale: saved.rationale,
        recommendation: saved.recommendation,
        role: saved.role_title,
        tier: saved.selected_tier_name ?? "Legacy check-in",
      });
      go("results");
    });
  }

  const headings: Record<Screen, string> = {
    profile: "A space for your next step",
    home: `Welcome, ${status?.display_name ?? person?.display_name ?? ""}`,
    role: "Which role would you like to explore?",
    tier: "Choose a level to explore",
    welcome: "A conversation about your growth",
    question: session?.question ?? "",
    results: "Where things stand",
  };

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <main id="main-content" tabIndex={-1} className="min-h-screen flex justify-center px-6 py-12 sm:py-16">
        <div className="w-full max-w-lg">
          <p className="font-sans text-sm text-ink-muted mb-4">Anchor · A personal check-in</p>
          <h1
            ref={heading}
            tabIndex={-1}
            data-testid={screen === "question" ? "question-text" : undefined}
            className="font-serif text-3xl leading-snug mb-6"
          >
            {headings[screen]}
          </h1>
          <div id="form-error" role="status" className="text-red-800 mb-4">{error}</div>
          <div role="status" className="text-ink-muted">{busy ? "Please wait…" : ""}</div>
          {screen === "profile" && (
            <ProfileScreen name={name} onNameChange={setName} onSubmit={enterProfile} isLoading={busy} error={error} />
          )}
          {screen === "home" && (
            <HomeScreen
              status={status}
              isLoading={busy}
              onStartNew={() => go("role")}
              onSwitchProfile={switchProfile}
              onRetry={refreshProfile}
              onViewResult={viewResult}
            />
          )}
          {screen === "role" && (
            <StartScreen roleTitle={title} onRoleTitleChange={setTitle} onStart={exploreRole} isLoading={busy} error={error} />
          )}
          {screen === "tier" && role && (
            <TierScreen role={role} tierId={tier} onSelect={setTier} onContinue={() => go("welcome")} onBack={() => go("role")} />
          )}
          {screen === "welcome" && role && selected && (
            <WelcomeScreen roleTitle={role.title} tierName={selected.name} isLoading={busy} onStart={beginSession} onBack={() => go("tier")} />
          )}
          {screen === "question" && session && (
            <QuestionScreen key={session.item} history={session.history} isLoading={busy} error={error} onSubmit={answerQuestion} />
          )}
          {screen === "results" && result && (
            <>
              <p className="mb-5">{result.role} · {result.tier}</p>
              <ResultsScreen verdict={result.verdict} rationale={result.rationale} recommendation={result.recommendation} />
            </>
          )}
          {screen !== "home" && screen !== "profile" && (
            <button className="secondary mt-8" disabled={busy} onClick={home}>Back to home</button>
          )}
        </div>
      </main>
    </>
  );
}
