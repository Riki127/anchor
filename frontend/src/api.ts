import type { AnswerResponse, Person, PersonStatus, Role, SessionRead, SessionStartResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, data?: unknown): Promise<T> {
  const response = await fetch(API_BASE + path, data === undefined ? undefined : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    if (response.status === 502) {
      throw new Error("The coach could not respond. Please retry with the same answer.");
    }
    if (response.status === 409) {
      throw new Error(
        "This answer conflicts with the saved session or the session is complete. " +
        "Retry the original answer, or return home to view saved results.",
      );
    }
    throw new Error(`Could not load or save this information (${response.status}). Please try again.`);
  }
  return response.json() as Promise<T>;
}

export const resolvePerson = (display_name: string) =>
  request<Person>("/people/resolve", { display_name });

export const getPersonStatus = (id: number) =>
  request<PersonStatus>(`/people/${id}/status`);

export const resolveRole = (title: string) =>
  request<Role>("/roles/resolve", { title });

export const startSession = (person_id: number, role_id: number, tier_id: string) =>
  request<SessionStartResponse>("/sessions", { person_id, role_id, tier_id });

export const submitAnswer = (id: number, item_id: number, answer: string) =>
  request<AnswerResponse>(`/sessions/${id}/answer`, { item_id, answer });

export const getSession = (id: number) => request<SessionRead>(`/sessions/${id}`);
