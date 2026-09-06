export type Verdict = "below" | "meeting" | "exceeding";

export interface Person {
  id: number;
  display_name: string;
}

export interface PersonStatus extends Person {
  sessions: {
    id: number;
    role_title: string;
    selected_tier_name: string | null;
    completed_at: string | null;
    verdict: Verdict | null;
  }[];
}

export interface Role {
  id: number;
  title: string;
  rubric_version: number;
  ladder: {
    career_ladder_summary: string;
    tiers: { id: string; name: string; expectations: string[] }[];
  };
}

export interface SessionStartResponse {
  session_id: number;
  role_id: number;
  item_id: number;
  question: string;
}

export interface AnswerResponse {
  status: "in_progress" | "completed";
  item_id: number | null;
  question: string | null;
  verdict: Verdict | null;
  rationale: string | null;
  recommendation: string | null;
}

export interface SessionRead {
  id: number;
  status: "in_progress" | "completed";
  role_title: string;
  person_id: number | null;
  selected_tier_id: string | null;
  selected_tier_name: string | null;
  qa_pairs: {
    item_id: number | null;
    order: number;
    question: string;
    answer: string | null;
  }[];
  verdict: Verdict | null;
  rationale: string | null;
  recommendation: string | null;
}
