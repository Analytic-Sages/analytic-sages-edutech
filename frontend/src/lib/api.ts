const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const ACCESS_TOKEN_KEY = "as_access_token";
/** Readable session flag for Next.js proxy (not the JWT). */
export const SESSION_COOKIE = "as_logged_in";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export function getApiBaseUrl() {
  return API_URL;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function writeSessionCookie(loggedIn: boolean) {
  if (typeof document === "undefined") return;
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  if (loggedIn) {
    document.cookie = `${SESSION_COOKIE}=1; Path=/; SameSite=Lax; Max-Age=${SESSION_MAX_AGE_SECONDS}${secure}`;
  } else {
    document.cookie = `${SESSION_COOKIE}=; Path=/; SameSite=Lax; Max-Age=0${secure}`;
  }
}

export function setAccessToken(token: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  writeSessionCookie(true);
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  writeSessionCookie(false);
}

/** Keep proxy cookie aligned with localStorage token (e.g. after deploy). */
export function syncAuthSession() {
  if (typeof window === "undefined") return;
  writeSessionCookie(Boolean(getAccessToken()));
}

export async function logout() {
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Still clear local session if the API is unreachable.
  } finally {
    clearAccessToken();
  }
}

type ApiOptions = RequestInit & {
  auth?: boolean;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function networkErrorMessage() {
  return `Can't reach the API at ${API_URL}. Start Docker, copy frontend/.env.example to frontend/.env.local, then run the backend on port 8000.`;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      credentials: "include",
    });
  } catch (err) {
    // Browsers often surface CORS/network failures as TypeError when the API returns 500.
    if (err instanceof TypeError) {
      throw new ApiError(0, networkErrorMessage());
    }
    throw err;
  }

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      if (response.status >= 500) {
        detail =
          "Server error while processing your request. Check the backend terminal for details.";
      }
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type PaymentProvider = "paystack" | "nowpayments" | "mock";

export type CheckoutResponse = {
  order_id: string;
  provider: PaymentProvider;
  checkout_url: string;
  amount: number;
  currency: string;
  status: string;
  crypto_currency: string | null;
  crypto_amount: string | null;
  mode: string;
};

export type ApiCourse = {
  id: string;
  slug: string;
  title: string;
  description: string;
  thumbnail: string | null;
  category: string;
  difficulty: string;
  duration: string;
  lessons_count: number;
  price: number;
  currency: string;
  published: boolean;
};

export type PaymentPublic = {
  id: string;
  order_id: string;
  course_id: string | null;
  cohort_id: string | null;
  provider: PaymentProvider;
  amount: number;
  currency: string;
  status: string;
  crypto_currency: string | null;
  crypto_amount: string | null;
  confirmed_at: string | null;
  created_at: string;
};

export type EnrollmentPublic = {
  id: string;
  course_id: string;
  status: "active" | "revoked";
  enrolled_at: string;
  payment_id: string | null;
};

export type AuthUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
};

export type AuthProviders = {
  google: {
    enabled: boolean;
    mode: "live" | "mock" | "disabled";
    start_url: string;
  };
  email_password: boolean;
};

export function getAuthProviders() {
  return apiFetch<AuthProviders>("/api/v1/auth/providers", { auth: false });
}

export function mockGoogleLogin(email: string, fullName?: string) {
  return apiFetch<{ access_token: string }>("/api/v1/auth/google/mock", {
    method: "POST",
    auth: false,
    body: JSON.stringify({
      email,
      full_name: fullName || "Google User",
    }),
  });
}

export function createCheckout(courseId: string, provider: PaymentProvider) {
  return apiFetch<CheckoutResponse>("/api/v1/checkout", {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, provider }),
  });
}

export function createCohortCheckout(cohortId: string, provider: PaymentProvider) {
  return apiFetch<CheckoutResponse>("/api/v1/checkout", {
    method: "POST",
    body: JSON.stringify({ cohort_id: cohortId, provider }),
  });
}

export function getPayment(orderId: string) {
  return apiFetch<PaymentPublic>(`/api/v1/payments/${orderId}`);
}

export function listApiCourses() {
  return apiFetch<ApiCourse[]>("/api/v1/courses", { auth: false });
}

export function getMyEnrollments() {
  return apiFetch<EnrollmentPublic[]>("/api/v1/me/enrollments");
}

export function getMe() {
  return apiFetch<AuthUser>("/api/v1/auth/me");
}

export function confirmMockPayment(orderId: string, status = "confirmed") {
  return apiFetch<{ message: string }>("/api/v1/webhooks/payments/mock/confirm", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ order_id: orderId, status }),
  });
}

export type LiveSessionPublic = {
  id: string;
  cohort_id: string;
  cohort_name: string;
  cohort_slug: string;
  course_title: string | null;
  title: string;
  week_label: string;
  session_number: number;
  objectives: string[];
  resources: Array<{
    title: string;
    url: string;
    kind: "slides" | "dataset" | "repo" | "reading" | "doc" | "other";
  }>;
  assignment_summary: string | null;
  starts_at: string;
  ends_at: string;
  status: "scheduled" | "live" | "ended" | "cancelled";
  phase: "upcoming" | "live" | "ended" | "cancelled";
  recording_url: string | null;
  can_join: boolean;
  member_role: "student" | "instructor" | "ta" | null;
};

export type ClassroomJoinResponse = {
  session_id: string;
  mode: "live" | "mock";
  auth_token: string | null;
  meeting_id: string | null;
  preset: string;
  display_name: string;
  phase: "upcoming" | "live" | "ended" | "cancelled";
  message: string | null;
};

export type PublicCohortCard = {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: "draft" | "open" | "active" | "completed";
  registration_deadline: string | null;
  starts_at: string | null;
  ends_at: string | null;
  price: number;
  currency: string;
  course_title: string | null;
  course_slug: string | null;
  next_session_title: string | null;
  next_session_starts_at: string | null;
  next_session_phase: "upcoming" | "live" | "ended" | "cancelled" | null;
  sessions_count: number;
};

export function listPublicCohorts() {
  return apiFetch<PublicCohortCard[]>("/api/v1/classroom/public/cohorts", { auth: false });
}

export function listClassroomSessions() {
  return apiFetch<LiveSessionPublic[]>("/api/v1/classroom/sessions");
}

export function getClassroomSession(sessionId: string) {
  return apiFetch<LiveSessionPublic>(`/api/v1/classroom/sessions/${sessionId}`);
}

export function joinClassroomSession(sessionId: string) {
  return apiFetch<ClassroomJoinResponse>(`/api/v1/classroom/sessions/${sessionId}/join`, {
    method: "POST",
  });
}
