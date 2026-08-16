export type SessionResource = {
  title: string;
  url: string;
  kind: "slides" | "dataset" | "repo" | "reading" | "doc" | "other";
};

export type LiveSessionPhase = "upcoming" | "live" | "ended" | "cancelled";

export type LiveSession = {
  id: string;
  cohort_id: string;
  cohort_name: string;
  cohort_slug: string;
  course_title: string | null;
  title: string;
  week_label: string;
  session_number: number;
  objectives: string[];
  resources: SessionResource[];
  assignment_summary: string | null;
  starts_at: string;
  ends_at: string;
  status: "scheduled" | "live" | "ended" | "cancelled";
  phase: LiveSessionPhase;
  recording_url: string | null;
  can_join: boolean;
  member_role: "student" | "instructor" | "ta" | null;
};

export type ClassroomJoin = {
  session_id: string;
  mode: "live" | "mock";
  auth_token: string | null;
  meeting_id: string | null;
  preset: string;
  display_name: string;
  phase: LiveSessionPhase;
  message: string | null;
};
