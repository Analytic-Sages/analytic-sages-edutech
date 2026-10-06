import { isQaCatalogCourse, isQaPublicEvent } from "@/lib/qa-fixtures";

const BACKEND_ORIGIN = (
  process.env.API_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
).replace(/\/$/, "");

export const ACCESS_TOKEN_KEY = "as_access_token";
/** Readable session flag for Next.js proxy (not the JWT). */
export const SESSION_COOKIE = "as_logged_in";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

/**
 * Browser uses same-origin `/api` so the refresh cookie is first-party.
 * Server-side fetches talk to the backend origin directly.
 */
export function getApiBaseUrl() {
  if (typeof window !== "undefined") return "";
  return BACKEND_ORIGIN;
}

function resolveApiUrl(path: string) {
  const base = getApiBaseUrl();
  return base ? `${base}${path}` : path;
}

const accessTokenListeners = new Set<() => void>();

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function subscribeAccessToken(listener: () => void) {
  accessTokenListeners.add(listener);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", listener);
  }
  return () => {
    accessTokenListeners.delete(listener);
    if (typeof window !== "undefined") {
      window.removeEventListener("storage", listener);
    }
  };
}

function notifyAccessTokenListeners() {
  accessTokenListeners.forEach((listener) => listener());
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
  notifyAccessTokenListeners();
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  writeSessionCookie(false);
  notifyAccessTokenListeners();
}

/** Keep proxy cookie aligned with localStorage token (e.g. after deploy). */
export function syncAuthSession() {
  if (typeof window === "undefined") return;
  writeSessionCookie(Boolean(getAccessToken()));
}

function isAccessTokenFresh(token: string) {
  try {
    const payload = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
    ) as { exp?: number };
    return typeof payload.exp === "number" && payload.exp * 1000 > Date.now() + 15_000;
  } catch {
    return false;
  }
}

let refreshInFlight: Promise<string | null> | null = null;

export async function refreshSession(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const response = await fetch(resolveApiUrl("/api/v1/auth/refresh"), {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) return null;
      const data = (await response.json()) as AuthResponse;
      if (!data.access_token) return null;
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      return null;
    }
  })().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}

export async function ensureSession(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const existing = getAccessToken();
  if (existing && isAccessTokenFresh(existing)) {
    writeSessionCookie(true);
    return existing;
  }
  const refreshed = await refreshSession();
  if (refreshed) return refreshed;
  if (existing) clearAccessToken();
  else writeSessionCookie(false);
  return null;
}

export async function logout() {
  try {
    await fetch(resolveApiUrl("/api/v1/auth/logout"), {
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
  _retried?: boolean;
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

const PUBLIC_LOAD_ERROR = "We're having trouble loading this information. Please try again.";

type ValidationIssue = {
  type?: string;
  loc?: Array<string | number>;
  msg?: string;
};

const API_FIELD_LABELS: Record<string, string> = {
  slug: "URL slug",
  title: "Title",
  short_description: "Short description",
  description: "Description",
  cover_image: "Cover image",
  starts_at: "Start time",
  ends_at: "End time",
  timezone: "Timezone",
  host_name: "Host name",
  event_type: "Event type",
  email: "Email",
  password: "Password",
};

function apiFieldLabel(loc: Array<string | number> | undefined): string {
  const parts = [...(loc ?? [])].reverse();
  const field = parts.find((part) => typeof part === "string" && part !== "body" && part !== "query");
  if (typeof field !== "string") return "This field";
  return API_FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}

/** Turn FastAPI/Pydantic `detail` into a short message safe to show in the UI. */
export function formatApiDetail(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (!Array.isArray(detail) || detail.length === 0) {
    return "Something went wrong. Please check the form and try again.";
  }

  const messages = detail.map((raw) => {
    const issue = (raw ?? {}) as ValidationIssue;
    const label = apiFieldLabel(issue.loc);
    const field = [...(issue.loc ?? [])].reverse().find((part) => typeof part === "string");

    if (issue.type === "string_pattern_mismatch" && field === "slug") {
      return `${label}: use lowercase letters, numbers, and hyphens only (e.g. data-infrastructure).`;
    }
    if (issue.type === "missing") return `${label} is required.`;
    if (issue.type === "string_too_short") return `${label} is too short.`;
    if (issue.type === "string_too_long") return `${label} is too long.`;
    if (issue.type === "value_error") {
      const msg = (issue.msg || "").replace(/^Value error,\s*/i, "").trim();
      return msg ? `${label}: ${msg}` : `${label} is invalid.`;
    }
    if (issue.msg) {
      const msg = issue.msg
        .replace(/^String should match pattern .+$/i, "has an invalid format")
        .replace(/^Value error,\s*/i, "")
        .trim();
      return `${label}: ${msg}`;
    }
    return `${label} is invalid.`;
  });

  return messages.filter(Boolean).join(" ") || "Please check the form and try again.";
}

function networkErrorMessage() {
  if (process.env.NODE_ENV !== "production") {
    console.warn(`API unreachable at ${getApiBaseUrl() || "same-origin /api"}`);
  }
  return PUBLIC_LOAD_ERROR;
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
    response = await fetch(resolveApiUrl(path), {
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
    if (
      response.status === 401 &&
      options.auth !== false &&
      !options._retried &&
      path !== "/api/v1/auth/refresh"
    ) {
      const token = await refreshSession();
      if (token) {
        return apiFetch<T>(path, { ...options, _retried: true });
      }
      if (getAccessToken()) clearAccessToken();
    }
    let detail = "Request failed";
    try {
      const data = await response.json();
      detail = formatApiDetail(data.detail);
    } catch {
      if (response.status >= 500) {
        detail = PUBLIC_LOAD_ERROR;
      }
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/** Set a first-party refresh cookie from the current access token. */
export async function persistSession(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const existing = getAccessToken();
  if (!existing) return null;
  try {
    const data = await apiFetch<AuthResponse>("/api/v1/auth/session", { method: "POST" });
    if (data.access_token) setAccessToken(data.access_token);
    return data.access_token ?? existing;
  } catch {
    return existing;
  }
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
  status: "active" | "revoked" | "completed";
  enrolled_at: string;
  payment_id: string | null;
};

export type SelfPacedLessonOutline = {
  id: string;
  slug: string;
  title: string;
  subtitle: string | null;
  duration_seconds: number | null;
  order_index: number;
  video_provider: string;
  video_id: string | null;
  completed: boolean;
};

export type SelfPacedModuleQuiz = {
  id: string;
  title: string;
  questions_total: number;
};

export type SelfPacedModuleOutline = {
  id: string;
  title: string;
  description: string;
  order_index: number;
  lessons: SelfPacedLessonOutline[];
  quiz?: SelfPacedModuleQuiz | null;
};

export type SelfPacedCourseCard = {
  id: string;
  slug: string;
  title: string;
  description: string;
  thumbnail: string | null;
  category: string;
  difficulty: string;
  duration: string;
  estimated_minutes: number;
  lessons_count: number;
  price: number;
  currency: string;
  is_free: boolean;
  delivery_type: string;
  certificate_enabled: boolean;
};

export type SelfPacedCoursePublic = SelfPacedCourseCard & {
  long_description: string;
  published: boolean;
  enrolled: boolean;
  completed: boolean;
  progress_percent: number;
  lessons_completed: number;
  resume_lesson_slug: string | null;
  modules: SelfPacedModuleOutline[];
  instructors?: InstructorPublic[];
};

export type SelfPacedLessonDetail = {
  id: string;
  slug: string;
  title: string;
  subtitle: string | null;
  description: string;
  module_id: string;
  module_title: string;
  lesson_number: number;
  lessons_total: number;
  duration_seconds: number | null;
  video_provider: string;
  video_id: string | null;
  what_you_learn: string[];
  key_concepts: string[];
  resources: { label: string; url: string }[];
  completed: boolean;
  prev_slug: string | null;
  next_slug: string | null;
  course_title: string;
  course_slug: string;
  course_completed: boolean;
  progress_percent: number;
  lessons_completed: number;
};

export type SelfPacedEnrollment = {
  id: string;
  course_id: string;
  status: "active" | "revoked" | "completed";
  enrolled_at: string;
  completed_at: string | null;
  last_activity_at: string | null;
  progress_percent: number;
  lessons_completed: number;
  lessons_total: number;
  resume_lesson_slug: string | null;
  last_completed_lesson_title: string | null;
  last_completed_at: string | null;
  course: SelfPacedCourseCard;
};

export type SelfPacedEnrollResponse = {
  enrollment_id: string;
  course_slug: string;
  already_enrolled: boolean;
  resume_lesson_slug: string | null;
  status: string;
};

export type LessonCompleteResponse = {
  lesson_slug: string;
  completed: boolean;
  course_completed: boolean;
  progress_percent: number;
  lessons_completed: number;
  lessons_total: number;
  next_slug: string | null;
};

export type AdminCourseRow = {
  id: string;
  slug: string;
  title: string;
  published: boolean;
  is_free: boolean;
  delivery_type: string;
  price: number;
  currency: string;
  lessons_count: number;
  modules_count: number;
  enrollments_count: number;
  completions_count: number;
  avg_progress_percent: number;
  instructor_count?: number;
  tutor_count?: number;
  last_activity_at: string | null;
};

export type InstructorPublic = {
  id: string;
  name: string;
  title: string;
  photo_url: string | null;
  bullets: string[];
  role_label: string;
  sort_order: number;
};

export type InstructorProfileAdmin = {
  id: string;
  name: string;
  title: string;
  photo_url: string | null;
  bullets: string[];
  course_count: number;
  cohort_count: number;
};

export type InstructorProfileWrite = {
  name: string;
  title?: string;
  photo_url?: string | null;
  bullets?: string[];
};

export type AdminCohortInstructorRow = {
  id: string;
  slug: string;
  name: string;
  status: string;
  instructor_count: number;
  tutor_count?: number;
};

export type AuthUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified: boolean;
  is_active: boolean;
  phone_number?: string | null;
  phone_country_code?: string | null;
  phone_verified?: boolean;
  country_of_residence?: string | null;
  discord_username?: string | null;
  telegram_username?: string | null;
  github_url?: string | null;
  x_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user: AuthUser;
};

export type AuthProviders = {
  google: {
    enabled: boolean;
    mode: "live" | "mock" | "disabled";
    start_url: string;
  };
  email_password: boolean;
};

export function sendContactMessage(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
}) {
  return apiFetch<{ message: string }>("/api/v1/contact", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload),
  });
}

export function getAuthProviders() {
  return apiFetch<AuthProviders>("/api/v1/auth/providers", { auth: false });
}

export function mockGoogleLogin(email: string, fullName?: string) {
  return apiFetch<{ access_token: string; user: AuthUser }>("/api/v1/auth/google/mock", {
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

export function createCohortCheckout(
  cohortId: string,
  provider: PaymentProvider,
  tuitionPlanId?: string,
) {
  return apiFetch<CheckoutResponse>("/api/v1/checkout", {
    method: "POST",
    body: JSON.stringify({
      cohort_id: cohortId,
      provider,
      ...(tuitionPlanId ? { tuition_plan_id: tuitionPlanId } : {}),
    }),
  });
}

export type TuitionPlanSchedule = {
  id: string;
  sequence_number: number;
  label: string | null;
  amount: string;
  due_rule: string;
  due_date: string | null;
  week_number: number | null;
  offset_days: number | null;
};

export type TuitionPlanPublic = {
  id: string;
  course_id: string | null;
  cohort_id: string | null;
  name: string;
  description: string | null;
  plan_type: string;
  base_currency: string;
  base_amount: string;
  number_of_installments: number;
  active: boolean;
  sort_order: number;
  schedules: TuitionPlanSchedule[];
};

export type ObligationPublic = {
  id: string;
  sequence_number: number;
  description: string;
  amount_due: string;
  currency: string;
  due_date: string | null;
  status: string;
  paid_amount: string;
  paid_at: string | null;
};

export type BillingAccountPublic = {
  id: string;
  student_id: string;
  course_id: string | null;
  cohort_id: string | null;
  tuition_plan_id: string;
  currency: string;
  total_amount: string;
  discount_amount: string;
  scholarship_amount: string;
  final_amount_due: string;
  amount_paid: string;
  amount_outstanding: string;
  billing_status: string;
  access_blocked?: boolean;
  created_at: string;
  obligations: ObligationPublic[];
  tuition_plan?: TuitionPlanPublic | null;
  // Derived server-side so admin views can distinguish paid-in-full vs installments.
  plan_name?: string | null;
  plan_type?: string | null;
  installments_total?: number;
  installments_paid?: number;
  installments_remaining?: number;
  is_paid_in_full?: boolean;
  next_due_date?: string | null;
  next_due_amount?: string | null;
  next_due_status?: string | null;
};

export function listBillingPlans(cohortId: string) {
  return apiFetch<TuitionPlanPublic[]>(
    `/api/v1/billing/plans?cohort_id=${encodeURIComponent(cohortId)}`,
    { auth: false },
  );
}

export function getMyBillingAccounts() {
  return apiFetch<BillingAccountPublic[]>("/api/v1/billing/me");
}

export function getMyBillingAccount(accountId: string) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/billing/me/accounts/${encodeURIComponent(accountId)}`,
  );
}

export function payBillingObligation(obligationId: string, provider: PaymentProvider) {
  return apiFetch<CheckoutResponse>(
    `/api/v1/billing/me/obligations/${encodeURIComponent(obligationId)}/pay`,
    {
      method: "POST",
      body: JSON.stringify({ provider }),
    },
  );
}

export function getAdminBillingAccounts(params?: { status?: string; cohortId?: string }) {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.cohortId) qs.set("cohort_id", params.cohortId);
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<BillingAccountPublic[]>(`/api/v1/admin/billing/accounts${suffix}`);
}

export function getAdminBillingAccount(accountId: string) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/accounts/${encodeURIComponent(accountId)}`,
  );
}

export function patchAdminBillingAccount(
  accountId: string,
  payload: { billing_status: string; note?: string },
) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/accounts/${encodeURIComponent(accountId)}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function waiveAdminObligation(obligationId: string, note?: string) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/obligations/${encodeURIComponent(obligationId)}/waive`,
    { method: "POST", body: JSON.stringify({ note }) },
  );
}

export function extendAdminObligation(
  obligationId: string,
  dueDate: string,
  note?: string,
) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/obligations/${encodeURIComponent(obligationId)}/extend`,
    {
      method: "POST",
      body: JSON.stringify({ due_date: dueDate, note }),
    },
  );
}

export function extendAdminNextDue(accountId: string, dueDate: string, note?: string) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/accounts/${encodeURIComponent(accountId)}/extend-next-due`,
    {
      method: "POST",
      body: JSON.stringify({ due_date: dueDate, note }),
    },
  );
}

export function setAdminAccountAccess(
  accountId: string,
  accessBlocked: boolean,
  note?: string,
) {
  return apiFetch<BillingAccountPublic>(
    `/api/v1/admin/billing/accounts/${encodeURIComponent(accountId)}/access`,
    {
      method: "PATCH",
      body: JSON.stringify({ access_blocked: accessBlocked, note }),
    },
  );
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

export function listSelfPacedCourses() {
  return apiFetch<SelfPacedCourseCard[]>("/api/v1/self-paced/courses", { auth: false }).then(
    (rows) => rows.filter((course) => !isQaCatalogCourse(course)),
  );
}

export function getSelfPacedCourse(slug: string) {
  return apiFetch<SelfPacedCoursePublic>(
    `/api/v1/self-paced/courses/${encodeURIComponent(slug)}`
  );
}

export function enrollSelfPacedCourse(slug: string) {
  return apiFetch<SelfPacedEnrollResponse>(
    `/api/v1/self-paced/courses/${encodeURIComponent(slug)}/enroll`,
    { method: "POST" }
  );
}

export function getSelfPacedLearn(slug: string) {
  return apiFetch<SelfPacedCoursePublic>(
    `/api/v1/self-paced/courses/${encodeURIComponent(slug)}/learn`
  );
}

export function getSelfPacedLesson(courseSlug: string, lessonSlug: string) {
  return apiFetch<SelfPacedLessonDetail>(
    `/api/v1/self-paced/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}`
  );
}

export function completeSelfPacedLesson(courseSlug: string, lessonSlug: string) {
  return apiFetch<LessonCompleteResponse>(
    `/api/v1/self-paced/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}/complete`,
    { method: "POST" }
  );
}

export function getMySelfPacedEnrollments() {
  return apiFetch<SelfPacedEnrollment[]>("/api/v1/self-paced/me/enrollments");
}

export function getAdminCourses() {
  return apiFetch<AdminCourseRow[]>("/api/v1/admin/courses");
}

// ---------- Quizzes ----------

export type QuizOptionPublic = {
  id: string;
  label: string;
};

export type QuizQuestionPublic = {
  id: string;
  prompt: string;
  order_index: number;
  options: QuizOptionPublic[];
};

export type QuizPublic = {
  id: string;
  course_id: string;
  module_id: string | null;
  lesson_id: string | null;
  title: string;
  description: string;
  pass_score: number;
  order_index: number;
  questions: QuizQuestionPublic[];
  questions_total: number;
  best_score: number | null;
  passed: boolean;
  attempts_count: number;
  last_attempt_at: string | null;
};

export type QuizQuestionResult = {
  question_id: string;
  prompt: string;
  selected_option_id: string | null;
  correct_option_id: string | null;
  is_correct: boolean;
  explanation: string | null;
};

export type QuizResult = {
  attempt_id: string;
  quiz_id: string;
  score: number;
  passed: boolean;
  correct_count: number;
  total_questions: number;
  pass_score: number;
  completed_at: string;
  results: QuizQuestionResult[];
};

export type QuizAttemptSummary = {
  id: string;
  quiz_id: string;
  score: number;
  passed: boolean;
  correct_count: number;
  total_questions: number;
  completed_at: string | null;
};

export function getQuiz(quizId: string) {
  return apiFetch<QuizPublic>(`/api/v1/quizzes/${encodeURIComponent(quizId)}`);
}

export function submitQuiz(
  quizId: string,
  answers: { question_id: string; option_id: string | null }[],
) {
  return apiFetch<QuizResult>(`/api/v1/quizzes/${encodeURIComponent(quizId)}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function listMyQuizAttempts(quizId: string) {
  return apiFetch<QuizAttemptSummary[]>(
    `/api/v1/quizzes/${encodeURIComponent(quizId)}/attempts`,
  );
}

export function listCourseQuizzes(courseSlug: string) {
  return apiFetch<QuizPublic[]>(
    `/api/v1/quizzes/course/${encodeURIComponent(courseSlug)}`,
  );
}

// ---------- Quiz authoring (admin) ----------

export type AdminQuizOption = {
  id: string;
  label: string;
  is_correct: boolean;
  order_index: number;
};

export type AdminQuizQuestion = {
  id: string;
  prompt: string;
  explanation: string | null;
  order_index: number;
  options: AdminQuizOption[];
};

export type AdminQuizRow = {
  id: string;
  course_id: string;
  course_slug: string;
  module_id: string | null;
  lesson_id: string | null;
  title: string;
  description: string;
  pass_score: number;
  published: boolean;
  order_index: number;
  questions_total: number;
  attempts_count: number;
  pass_rate: number;
};

export type AdminQuizDetail = AdminQuizRow & {
  questions: AdminQuizQuestion[];
};

export type QuizOptionInput = { label: string; is_correct: boolean };

export function getAdminQuizzes(courseSlug?: string) {
  const qs = courseSlug ? `?course_slug=${encodeURIComponent(courseSlug)}` : "";
  return apiFetch<AdminQuizRow[]>(`/api/v1/admin/quizzes${qs}`);
}

export function getAdminQuiz(quizId: string) {
  return apiFetch<AdminQuizDetail>(`/api/v1/admin/quizzes/${encodeURIComponent(quizId)}`);
}

export function createAdminQuiz(
  courseSlug: string,
  payload: {
    title: string;
    description?: string;
    pass_score?: number;
    published?: boolean;
    module_id?: string | null;
    lesson_id?: string | null;
    order_index?: number;
  },
) {
  return apiFetch<AdminQuizDetail>(
    `/api/v1/admin/courses/${encodeURIComponent(courseSlug)}/quizzes`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function updateAdminQuiz(
  quizId: string,
  payload: Partial<{
    title: string;
    description: string;
    pass_score: number;
    published: boolean;
    order_index: number;
  }>,
) {
  return apiFetch<AdminQuizDetail>(`/api/v1/admin/quizzes/${encodeURIComponent(quizId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteAdminQuiz(quizId: string) {
  return apiFetch<void>(`/api/v1/admin/quizzes/${encodeURIComponent(quizId)}`, {
    method: "DELETE",
  });
}

export function addAdminQuizQuestion(
  quizId: string,
  payload: { prompt: string; explanation?: string | null; options: QuizOptionInput[] },
) {
  return apiFetch<AdminQuizDetail>(
    `/api/v1/admin/quizzes/${encodeURIComponent(quizId)}/questions`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function updateAdminQuizQuestion(
  questionId: string,
  payload: { prompt?: string; explanation?: string | null; options?: QuizOptionInput[] },
) {
  return apiFetch<AdminQuizDetail>(
    `/api/v1/admin/quiz-questions/${encodeURIComponent(questionId)}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function deleteAdminQuizQuestion(questionId: string) {
  return apiFetch<AdminQuizDetail>(
    `/api/v1/admin/quiz-questions/${encodeURIComponent(questionId)}`,
    { method: "DELETE" },
  );
}

// ---------- Course authoring (admin) ----------

export type AdminLessonResource = {
  label: string;
  url: string;
  kind: "pdf" | "slides" | "dataset" | "code" | "repo" | "reading" | "doc" | "other";
};

export type AdminLessonRow = {
  id: string;
  module_id: string;
  slug: string;
  title: string;
  subtitle: string | null;
  description: string;
  video_provider: string;
  video_id: string | null;
  duration_seconds: number | null;
  order_index: number;
  published: boolean;
  what_you_learn: string[];
  key_concepts: string[];
  resources: AdminLessonResource[];
};

export type AdminModuleRow = {
  id: string;
  title: string;
  description: string;
  order_index: number;
  lessons: AdminLessonRow[];
};

export type AdminCourseDetail = {
  id: string;
  slug: string;
  title: string;
  description: string;
  long_description: string;
  thumbnail: string | null;
  category: string;
  difficulty: string;
  duration: string;
  lessons_count: number;
  price: number;
  currency: string;
  delivery_type: string;
  is_free: boolean;
  certificate_enabled: boolean;
  published: boolean;
  modules: AdminModuleRow[];
};

export type AdminCourseUpsert = {
  slug: string;
  title: string;
  description?: string;
  long_description?: string;
  thumbnail?: string | null;
  category?: string;
  difficulty?: string;
  duration?: string;
  price?: number;
  currency?: string;
  delivery_type?: string;
  is_free?: boolean;
  certificate_enabled?: boolean;
  published?: boolean;
};

export type AdminLessonUpsert = {
  title: string;
  slug?: string | null;
  subtitle?: string | null;
  description?: string;
  video_provider?: string;
  video_id?: string | null;
  duration_seconds?: number | null;
  order_index?: number | null;
  published?: boolean;
  what_you_learn?: string[];
  key_concepts?: string[];
};

export type AdminVideoUploadResponse = {
  uid: string;
  upload_url: string;
  embed_url: string | null;
  hls_url: string | null;
  thumbnail_url: string | null;
  mode: "live" | "mock";
};

export function getAdminCourseDetail(slug: string) {
  return apiFetch<AdminCourseDetail>(`/api/v1/admin/courses/${encodeURIComponent(slug)}/detail`);
}

export function createAdminCourse(payload: AdminCourseUpsert) {
  return apiFetch<AdminCourseDetail>("/api/v1/admin/courses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminCourse(slug: string, payload: Partial<AdminCourseUpsert>) {
  return apiFetch<AdminCourseDetail>(`/api/v1/admin/courses/${encodeURIComponent(slug)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteAdminCourse(slug: string) {
  return apiFetch<void>(`/api/v1/admin/courses/${encodeURIComponent(slug)}`, {
    method: "DELETE",
  });
}

export function createAdminModule(
  slug: string,
  payload: { title: string; description?: string; order_index?: number | null }
) {
  return apiFetch<AdminModuleRow>(`/api/v1/admin/courses/${encodeURIComponent(slug)}/modules`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminModule(
  moduleId: string,
  payload: { title?: string; description?: string; order_index?: number }
) {
  return apiFetch<AdminModuleRow>(`/api/v1/admin/modules/${encodeURIComponent(moduleId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteAdminModule(moduleId: string) {
  return apiFetch<void>(`/api/v1/admin/modules/${encodeURIComponent(moduleId)}`, {
    method: "DELETE",
  });
}

export function createAdminLesson(moduleId: string, payload: AdminLessonUpsert) {
  return apiFetch<AdminLessonRow>(
    `/api/v1/admin/modules/${encodeURIComponent(moduleId)}/lessons`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export function updateAdminLesson(lessonId: string, payload: Partial<AdminLessonUpsert>) {
  return apiFetch<AdminLessonRow>(`/api/v1/admin/lessons/${encodeURIComponent(lessonId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteAdminLesson(lessonId: string) {
  return apiFetch<void>(`/api/v1/admin/lessons/${encodeURIComponent(lessonId)}`, {
    method: "DELETE",
  });
}

export function addAdminLessonResource(
  lessonId: string,
  payload: { label: string; url: string; kind: string }
) {
  return apiFetch<AdminLessonRow>(
    `/api/v1/admin/lessons/${encodeURIComponent(lessonId)}/resources`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export function uploadAdminLessonResource(
  lessonId: string,
  params: { label: string; kind: string },
  file: File
) {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const body = new FormData();
  body.append("file", file);
  const qs = new URLSearchParams({ label: params.label, kind: params.kind });
  return fetch(
    resolveApiUrl(`/api/v1/admin/lessons/${encodeURIComponent(lessonId)}/resources/upload?${qs}`),
    { method: "POST", headers, credentials: "include", body }
  ).then(async (response) => {
    if (!response.ok) {
      let detail = "Upload failed";
      try {
        detail = (await response.json()).detail ?? detail;
      } catch {
        // keep default
      }
      throw new ApiError(response.status, detail);
    }
    return (await response.json()) as AdminLessonRow;
  });
}

export function createLessonVideoUpload(lessonId: string, maxDurationSeconds?: number) {
  const qs = maxDurationSeconds ? `?max_duration_seconds=${maxDurationSeconds}` : "";
  return apiFetch<AdminVideoUploadResponse>(
    `/api/v1/admin/lessons/${encodeURIComponent(lessonId)}/video/direct-upload${qs}`,
    { method: "POST" }
  );
}

export function listAdminInstructorProfiles() {
  return apiFetch<InstructorProfileAdmin[]>("/api/v1/admin/instructor-profiles");
}

export function createAdminInstructorProfile(payload: InstructorProfileWrite) {
  return apiFetch<InstructorProfileAdmin>("/api/v1/admin/instructor-profiles", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminInstructorProfile(id: string, payload: InstructorProfileWrite) {
  return apiFetch<InstructorProfileAdmin>(
    `/api/v1/admin/instructor-profiles/${encodeURIComponent(id)}`,
    { method: "PATCH", body: JSON.stringify(payload) }
  );
}

export function deleteAdminInstructorProfile(id: string) {
  return apiFetch<{ message: string }>(
    `/api/v1/admin/instructor-profiles/${encodeURIComponent(id)}`,
    { method: "DELETE" }
  );
}

export function listAdminCatalogCohorts() {
  return apiFetch<AdminCohortInstructorRow[]>("/api/v1/admin/catalog/cohorts");
}

export function getAdminCourseInstructors(slug: string) {
  return apiFetch<InstructorPublic[]>(
    `/api/v1/admin/courses/${encodeURIComponent(slug)}/instructors`
  );
}

export function putAdminCourseInstructors(slug: string, items: InstructorPublic[]) {
  return apiFetch<InstructorPublic[]>(
    `/api/v1/admin/courses/${encodeURIComponent(slug)}/instructors`,
    {
      method: "PUT",
      body: JSON.stringify({
        items: items.map((item, index) => ({
          instructor_id: item.id,
          role_label: item.role_label,
          sort_order: index,
        })),
      }),
    }
  );
}

export function getAdminCohortInstructors(slug: string) {
  return apiFetch<InstructorPublic[]>(
    `/api/v1/admin/cohorts/${encodeURIComponent(slug)}/instructors`
  );
}

export function putAdminCohortInstructors(slug: string, items: InstructorPublic[]) {
  return apiFetch<InstructorPublic[]>(
    `/api/v1/admin/cohorts/${encodeURIComponent(slug)}/instructors`,
    {
      method: "PUT",
      body: JSON.stringify({
        items: items.map((item, index) => ({
          instructor_id: item.id,
          role_label: item.role_label,
          sort_order: index,
        })),
      }),
    }
  );
}

export type AdminTutorRow = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  role_label: string;
};

export function getAdminCourseTutors(slug: string) {
  return apiFetch<AdminTutorRow[]>(
    `/api/v1/admin/courses/${encodeURIComponent(slug)}/tutors`
  );
}

export function putAdminCourseTutors(slug: string, userIds: string[]) {
  return apiFetch<AdminTutorRow[]>(
    `/api/v1/admin/courses/${encodeURIComponent(slug)}/tutors`,
    { method: "PUT", body: JSON.stringify({ user_ids: userIds }) }
  );
}

export function getAdminCohortTutors(slug: string) {
  return apiFetch<AdminTutorRow[]>(
    `/api/v1/admin/cohorts/${encodeURIComponent(slug)}/tutors`
  );
}

export function putAdminCohortTutors(slug: string, userIds: string[]) {
  return apiFetch<AdminTutorRow[]>(
    `/api/v1/admin/cohorts/${encodeURIComponent(slug)}/tutors`,
    { method: "PUT", body: JSON.stringify({ user_ids: userIds }) }
  );
}

export type EventLifecycle =
  | "draft"
  | "coming_soon"
  | "upcoming"
  | "registration_closed"
  | "live"
  | "completed"
  | "cancelled";

export type EventType =
  | "workshop"
  | "webinar"
  | "masterclass"
  | "ama"
  | "community"
  | "career"
  | "x_space"
  | "other";

export type EventPlatform = "youtube" | "x_space" | "zoom" | "other";

export type EventCardPublic = {
  id: string;
  slug: string;
  title: string;
  event_type: EventType | string;
  short_description: string;
  cover_image: string | null;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  price: number;
  currency: string;
  is_free: boolean;
  host_name: string | null;
  platform?: EventPlatform | string;
  platform_label?: string | null;
  platform_display?: string;
  lifecycle: EventLifecycle | string;
  registered: boolean;
  can_register: boolean;
  related_course_slug: string | null;
  has_recording?: boolean;
};

export type KeepLearningOffer = {
  kind: "course" | "program";
  slug: string;
};

export type EventPublic = EventCardPublic & {
  description: string;
  learn_topics: string[];
  audience: string[];
  prerequisites: string;
  registration_deadline: string | null;
  capacity: number | null;
  cancelled: boolean;
  can_join: boolean;
  can_watch_recording: boolean;
  youtube_live_url: string | null;
  recording_url: string | null;
  keep_learning?: KeepLearningOffer[];
  seo_title: string | null;
  seo_description: string | null;
};

export type EventRegistrationPublic = {
  id: string;
  status: string;
  registered_at: string;
  join_clicked_at: string | null;
  checked_in_at: string | null;
  event: EventCardPublic;
};

export type EventRegisterResponse = {
  registration_id: string;
  event_slug: string;
  already_registered: boolean;
  status: string;
};

export type EventJoinResponse = {
  youtube_live_url: string;
  join_clicked_at: string;
};

export type EventAdmin = {
  id: string;
  slug: string;
  title: string;
  event_type: EventType | string;
  short_description: string;
  description: string;
  cover_image: string | null;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  price: number;
  currency: string;
  registration_deadline: string | null;
  capacity: number | null;
  host_name: string | null;
  platform: EventPlatform | string;
  platform_label: string | null;
  platform_display: string;
  youtube_live_url: string | null;
  recording_url: string | null;
  learn_topics: string[];
  audience: string[];
  prerequisites: string;
  related_course_slug: string | null;
  keep_learning: KeepLearningOffer[];
  seo_title: string | null;
  seo_description: string | null;
  published: boolean;
  cancelled: boolean;
  lifecycle: EventLifecycle | string;
  registered_count: number;
  created_at: string;
  updated_at: string;
};

export type EventRegistrantAdmin = {
  id: string;
  user_id: string;
  email: string;
  full_name: string | null;
  phone_number: string | null;
  phone_country_code: string | null;
  country_of_residence: string | null;
  status: string;
  registered_at: string;
};

export type EventWritePayload = {
  slug: string;
  title: string;
  event_type: EventType | string;
  short_description: string;
  description: string;
  cover_image?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  timezone: string;
  price?: number;
  currency?: string;
  registration_deadline?: string | null;
  capacity?: number | null;
  host_name?: string | null;
  platform?: EventPlatform | string;
  platform_label?: string | null;
  youtube_live_url?: string | null;
  recording_url?: string | null;
  learn_topics?: string[];
  audience?: string[];
  prerequisites?: string;
  related_course_slug?: string | null;
  keep_learning?: KeepLearningOffer[];
  seo_title?: string | null;
  seo_description?: string | null;
  published?: boolean;
  cancelled?: boolean;
};

export function listPublicEvents(options?: { upcoming?: boolean; limit?: number }) {
  const params = new URLSearchParams();
  if (options?.upcoming) params.set("upcoming", "true");
  if (options?.limit) params.set("limit", String(options.limit));
  const query = params.toString();
  return apiFetch<EventCardPublic[]>(`/api/v1/events${query ? `?${query}` : ""}`).then((rows) =>
    rows.filter((event) => !isQaPublicEvent(event)),
  );
}

export function getPublicEvent(slug: string) {
  return apiFetch<EventPublic>(`/api/v1/events/${encodeURIComponent(slug)}`);
}

export function registerForEvent(slug: string, source?: string) {
  return apiFetch<EventRegisterResponse>(`/api/v1/events/${encodeURIComponent(slug)}/register`, {
    method: "POST",
    body: JSON.stringify({ source: source || null }),
  });
}

export function cancelEventRegistration(slug: string) {
  return apiFetch<{ message: string }>(`/api/v1/events/${encodeURIComponent(slug)}/register`, {
    method: "DELETE",
  });
}

export function joinEvent(slug: string) {
  return apiFetch<EventJoinResponse>(`/api/v1/events/${encodeURIComponent(slug)}/join`, {
    method: "POST",
  });
}

export function checkInEvent(slug: string) {
  return apiFetch<{ checked_in_at: string }>(`/api/v1/events/${encodeURIComponent(slug)}/check-in`, {
    method: "POST",
  });
}

export function getMyEvents() {
  return apiFetch<EventRegistrationPublic[]>("/api/v1/events/me");
}

export function getAdminEvents() {
  return apiFetch<EventAdmin[]>("/api/v1/admin/events");
}

export function getAdminEvent(id: string) {
  return apiFetch<EventAdmin>(`/api/v1/admin/events/${encodeURIComponent(id)}`);
}

export function getAdminEventRegistrants(id: string) {
  return apiFetch<EventRegistrantAdmin[]>(`/api/v1/admin/events/${encodeURIComponent(id)}/registrants`);
}

export async function downloadAdminEventRegistrants(id: string) {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`/api/v1/admin/events/${encodeURIComponent(id)}/registrants.csv`, {
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(response.status, formatApiDetail(data?.detail) || "Download failed");
  }
  return response.blob();
}

export function emailAdminEventRegistrants(
  id: string,
  payload: { recipient_user_ids: string[]; subject: string; message: string; include_event_link: boolean },
) {
  return apiFetch<{ sent: number; failed: number }>(`/api/v1/admin/events/${encodeURIComponent(id)}/registrants/email`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createAdminEvent(payload: EventWritePayload) {
  return apiFetch<EventAdmin>("/api/v1/admin/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadAdminEventImage(file: File) {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/v1/admin/events/uploads", {
    method: "POST",
    headers,
    body,
    credentials: "include",
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(response.status, formatApiDetail(data?.detail) || "Upload failed");
  }
  return response.json() as Promise<{ url: string }>;
}

export function updateAdminEvent(id: string, payload: Partial<EventWritePayload>) {
  return apiFetch<EventAdmin>(`/api/v1/admin/events/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function cancelAdminEvent(id: string) {
  return apiFetch<EventAdmin>(`/api/v1/admin/events/${encodeURIComponent(id)}/cancel`, {
    method: "POST",
  });
}

export function getMe() {
  return apiFetch<AuthUser>("/api/v1/auth/me");
}

export function updateMyProfile(payload: {
  full_name?: string | null;
  phone_number?: string | null;
  phone_country_code?: string | null;
  country_of_residence?: string | null;
  discord_username?: string | null;
  telegram_username?: string | null;
  github_url?: string | null;
  x_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
}) {
  return apiFetch<AuthUser>("/api/v1/auth/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
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
  session_type: "teaching" | "office_hour";
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
  recording_status?: "none" | "processing" | "ready" | "failed";
  recording_watch_url?: string | null;
  can_join: boolean;
  member_role: "student" | "instructor" | "ta" | null;
  access_blocked?: boolean;
  access_blocked_reason?: string | null;
};

export type SessionRecordingPlayback = {
  session_id: string;
  status: "none" | "processing" | "ready" | "failed";
  watch_url: string | null;
  duration_seconds: number | null;
  embed_url: string | null;
  hls_url: string | null;
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
  instructors?: InstructorPublic[];
  waitlist_open?: boolean;
};

export type WaitlistEntry = {
  id: string;
  cohort_id: string;
  created_at: string;
};

export type WaitlistStatus = {
  is_open: boolean;
  is_on_waitlist: boolean;
  missing_fields: string[];
  entry: WaitlistEntry | null;
};

export type AdminWaitlistRow = {
  user_id: string;
  full_name: string | null;
  email: string;
  phone_number: string | null;
  phone_country_code: string | null;
  country_of_residence: string | null;
  discord_username: string | null;
  telegram_username: string | null;
  note: string | null;
  created_at: string;
};

export type AdminWaitlistResponse = {
  cohort_id: string;
  cohort_slug: string;
  cohort_name: string;
  is_open: boolean;
  count: number;
  entries: AdminWaitlistRow[];
};

export function getMyWaitlistStatus(cohortId: string) {
  return apiFetch<WaitlistStatus>(
    `/api/v1/cohorts/${encodeURIComponent(cohortId)}/waitlist/me`,
  );
}

export function joinWaitlist(cohortId: string, note?: string) {
  return apiFetch<WaitlistEntry>(
    `/api/v1/cohorts/${encodeURIComponent(cohortId)}/waitlist`,
    { method: "POST", body: JSON.stringify({ note: note ?? null }) },
  );
}

export function getAdminCohortWaitlist(slug: string) {
  return apiFetch<AdminWaitlistResponse>(
    `/api/v1/admin/cohorts/${encodeURIComponent(slug)}/waitlist`,
  );
}

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

export function getSessionRecording(cohortId: string, sessionId: string) {
  return apiFetch<SessionRecordingPlayback>(
    `/api/v1/cohorts/${encodeURIComponent(cohortId)}/sessions/${encodeURIComponent(sessionId)}/recording`,
  );
}

export type ClassroomCalendarFeed = {
  token: string;
  url: string;
  webcal_url: string;
};

export function getClassroomCalendarToken() {
  return apiFetch<ClassroomCalendarFeed>("/api/v1/classroom/calendar-token");
}

export type ProgrammePublic = {
  id: string;
  slug: string;
  title: string;
  description: string;
  overview: string;
  learning_outcomes: string[];
  duration: string;
  programme_type: string;
  status: string;
  cover_image: string | null;
  requirements: string[];
  certificate_requirements: Record<string, unknown>;
  course_id: string | null;
};

export type ProgrammeCohortPublic = {
  id: string;
  name: string;
  slug: string;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  capacity: number | null;
  price: number;
  currency: string;
  community_links: Record<string, string>;
};

export type ProgrammeDetailPublic = ProgrammePublic & {
  cohorts: ProgrammeCohortPublic[];
};

export type AttendanceSummary = {
  attended: number;
  late: number;
  absent: number;
  total: number;
};

export type AttendanceRecord = {
  session_id: string;
  session_title: string;
  starts_at: string;
  status: "attended" | "late" | "absent";
  recorded_at: string;
  note: string | null;
};

export type MyLiveEnrollment = {
  programme_id: string | null;
  programme_slug: string | null;
  programme_title: string | null;
  cohort_id: string;
  cohort_name: string;
  cohort_slug: string;
  enrollment_status: string;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  progress_percent: number;
  attendance_attended: number;
  attendance_total: number;
  next_session: LiveSessionPublic | null;
  is_preview?: boolean;
};

export type CohortStudentDetail = {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  capacity: number | null;
  community_links: Record<string, string>;
  programme: ProgrammePublic | null;
  progress_percent: number;
  attendance: AttendanceSummary;
  sessions: LiveSessionPublic[];
  is_preview?: boolean;
};

export type InstructorStudentRow = {
  user_id: string;
  email: string;
  full_name: string | null;
  country_of_residence: string | null;
  enrollment_status: string;
  attendance_attended: number;
  attendance_total: number;
  progress_percent: number;
};

export function listProgrammes() {
  return apiFetch<ProgrammePublic[]>("/api/v1/programmes", { auth: false });
}

export function getProgramme(slug: string) {
  return apiFetch<ProgrammeDetailPublic>(`/api/v1/programmes/${encodeURIComponent(slug)}`, {
    auth: false,
  });
}

export function getMyLiveEnrollments() {
  return apiFetch<MyLiveEnrollment[]>("/api/v1/me/live");
}

export function getMyCohort(cohortId: string) {
  return apiFetch<CohortStudentDetail>(`/api/v1/cohorts/${encodeURIComponent(cohortId)}`);
}

export function getMyAttendance(cohortId: string) {
  return apiFetch<AttendanceRecord[]>(
    `/api/v1/cohorts/${encodeURIComponent(cohortId)}/attendance`,
  );
}

export function listInstructorCohorts() {
  return apiFetch<CohortStudentDetail[]>("/api/v1/instructor/cohorts");
}

export function getInstructorStudents(cohortId: string) {
  return apiFetch<InstructorStudentRow[]>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/students`,
  );
}

export function getInstructorAttendance(cohortId: string) {
  return apiFetch<AttendanceRecord[]>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/attendance`,
  );
}

export function putInstructorAttendance(
  cohortId: string,
  items: { user_id: string; session_id: string; status: string; note?: string | null }[],
) {
  return apiFetch<AttendanceRecord[]>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/attendance`,
    { method: "PUT", body: JSON.stringify({ items }) },
  );
}

export type AssignmentResource = {
  title: string;
  url: string;
  kind: string;
};

export type AssignmentPublic = {
  id: string;
  cohort_id: string;
  session_id: string | null;
  title: string;
  description: string;
  instructions: string | null;
  week_label: string;
  due_date: string | null;
  max_score: number;
  passing_score: number | null;
  required_fields: string[];
  resources: AssignmentResource[];
  status: string;
};

export type SubmissionPublic = {
  id: string;
  assignment_id: string;
  user_id: string;
  status: string;
  text_response: string | null;
  github_url: string | null;
  live_url: string | null;
  build_in_public_url: string | null;
  documentation_url: string | null;
  files: Record<string, unknown>[];
  score: number | null;
  feedback: string | null;
  reviewer_name: string | null;
  reviewed_at: string | null;
  submitted_at: string | null;
  updated_at: string;
};

export type AssignmentDetail = AssignmentPublic & {
  my_submission: SubmissionPublic | null;
};

export type AssignmentTracking = AssignmentPublic & {
  student_count: number;
  submitted_count: number;
  missing_count: number;
  reviewed_count: number;
  submissions: Array<{
    submission: SubmissionPublic;
    user_id: string;
    email: string;
    full_name: string | null;
    enrollment_status: string;
  }>;
};

export type SubmissionUpsertPayload = {
  text_response?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  build_in_public_url?: string | null;
  documentation_url?: string | null;
  files?: Record<string, unknown>[];
  status: "draft" | "submitted";
};

export type AssignmentUpsertPayload = {
  cohort_id: string;
  session_id?: string | null;
  title: string;
  description?: string;
  instructions?: string | null;
  week_label?: string;
  due_date?: string | null;
  max_score?: number;
  passing_score?: number | null;
  required_fields?: string[];
  resources?: AssignmentResource[];
  status: string;
};

export function getMyAssignments(cohortId: string) {
  return apiFetch<AssignmentPublic[]>(`/api/v1/cohorts/${encodeURIComponent(cohortId)}/assignments`);
}

export function getAssignment(assignmentId: string) {
  return apiFetch<AssignmentDetail>(`/api/v1/assignments/${encodeURIComponent(assignmentId)}`);
}

export function putMySubmission(assignmentId: string, payload: SubmissionUpsertPayload) {
  return apiFetch<SubmissionPublic>(
    `/api/v1/assignments/${encodeURIComponent(assignmentId)}/submissions/me`,
    { method: "PUT", body: JSON.stringify(payload) },
  );
}

export function listInstructorAssignments(cohortId: string) {
  return apiFetch<AssignmentPublic[]>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/assignments`,
  );
}

export function createInstructorAssignment(payload: AssignmentUpsertPayload) {
  return apiFetch<AssignmentPublic>("/api/v1/instructor/assignments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateInstructorAssignment(
  assignmentId: string,
  payload: AssignmentUpsertPayload,
) {
  return apiFetch<AssignmentPublic>(
    `/api/v1/instructor/assignments/${encodeURIComponent(assignmentId)}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function getAssignmentTracking(assignmentId: string) {
  return apiFetch<AssignmentTracking>(
    `/api/v1/instructor/assignments/${encodeURIComponent(assignmentId)}/tracking`,
  );
}

export function reviewSubmission(
  submissionId: string,
  payload: { score?: number | null; feedback?: string | null; status: string },
) {
  return apiFetch<SubmissionPublic>(
    `/api/v1/instructor/submissions/${encodeURIComponent(submissionId)}/review`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export type ProjectPublic = {
  id: string;
  cohort_id: string;
  user_id: string;
  title: string;
  description: string;
  status: string;
  github_url: string | null;
  live_url: string | null;
  build_in_public_url: string | null;
  documentation_url: string | null;
  cover_image: string | null;
  technologies: string[];
  feedback: string | null;
  reviewer_name: string | null;
  reviewed_at: string | null;
  is_public: boolean;
  updated_at: string;
};

export type ProjectUpsertPayload = {
  title: string;
  description?: string;
  status: string;
  github_url?: string | null;
  live_url?: string | null;
  build_in_public_url?: string | null;
  documentation_url?: string | null;
  cover_image?: string | null;
  technologies?: string[];
  is_public?: boolean;
};

export type InstructorProjectRow = {
  project: ProjectPublic;
  user_id: string;
  email: string;
  full_name: string | null;
};

export type AtRiskStudentRow = {
  user_id: string;
  email: string;
  full_name: string | null;
  missed_sessions: number;
  missing_assignments: number;
  incomplete_projects: number;
  at_risk: boolean;
};

export type GradebookRow = {
  user_id: string;
  full_name: string | null;
  email: string;
  attendance_present: number;
  attendance_total: number;
  assignments_submitted: number;
  assignments_total: number;
  avg_score: number | null;
  projects_completed: number;
  at_risk: boolean;
};

export type CohortReport = {
  cohort_id: string;
  cohort_name: string;
  student_count: number;
  attendance_rate: number;
  assignment_completion_rate: number;
  projects_completed: number;
  at_risk_count: number;
  at_risk: AtRiskStudentRow[];
  gradebook: GradebookRow[];
};

export function getMyProjects(cohortId: string) {
  return apiFetch<ProjectPublic[]>(`/api/v1/cohorts/${encodeURIComponent(cohortId)}/projects`);
}

export function createProject(cohortId: string, payload: ProjectUpsertPayload) {
  return apiFetch<ProjectPublic>(`/api/v1/cohorts/${encodeURIComponent(cohortId)}/projects`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(projectId: string, payload: ProjectUpsertPayload) {
  return apiFetch<ProjectPublic>(`/api/v1/projects/${encodeURIComponent(projectId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function listInstructorProjects(cohortId: string) {
  return apiFetch<InstructorProjectRow[]>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/projects`,
  );
}

export function reviewProject(
  projectId: string,
  payload: { feedback?: string | null; status: string },
) {
  return apiFetch<ProjectPublic>(
    `/api/v1/instructor/projects/${encodeURIComponent(projectId)}/review`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function getCohortReport(cohortId: string) {
  return apiFetch<CohortReport>(
    `/api/v1/instructor/cohorts/${encodeURIComponent(cohortId)}/report`,
  );
}

export type ShowcaseProject = {
  project: ProjectPublic;
  full_name: string | null;
  country_of_residence: string | null;
};

export type CertificateEligibility = {
  cohort_id: string;
  cohort_name: string;
  programme_slug: string | null;
  programme_title: string | null;
  eligible: boolean;
  attendance_percent: number;
  assignments_submitted: number;
  assignments_total: number;
  projects_completed: number;
  requirements: Record<string, unknown>;
};

export type PublicPortfolio = {
  user_id: string;
  full_name: string | null;
  country_of_residence: string | null;
  github_url: string | null;
  x_url: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  projects: ProjectPublic[];
};

export type MyPortfolio = PublicPortfolio & {
  email: string;
  portfolio_public: boolean;
  public_url: string | null;
  certificates: CertificateEligibility[];
};

export type NotificationPublic = {
  id: string;
  type: string;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
};

export function listShowcaseProjects() {
  return apiFetch<ShowcaseProject[]>("/api/v1/showcase/projects", { auth: false });
}

export function getPublicPortfolio(userId: string) {
  return apiFetch<PublicPortfolio>(`/api/v1/portfolio/${encodeURIComponent(userId)}`, {
    auth: false,
  });
}

export function getMyPortfolio() {
  return apiFetch<MyPortfolio>("/api/v1/me/portfolio");
}

export function updateMyPortfolioVisibility(portfolioPublic: boolean) {
  return apiFetch<MyPortfolio>("/api/v1/me/portfolio", {
    method: "PATCH",
    body: JSON.stringify({ portfolio_public: portfolioPublic }),
  });
}

export function getMyCertificateEligibility() {
  return apiFetch<CertificateEligibility[]>("/api/v1/me/certificate-eligibility");
}

export function getMyNotifications() {
  return apiFetch<NotificationPublic[]>("/api/v1/me/notifications");
}

export function markNotificationsRead() {
  return apiFetch<{ unread: number }>("/api/v1/me/notifications/read-all", { method: "POST" });
}

export type AdminUserRow = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified: boolean;
  is_active: boolean;
  phone_number?: string | null;
  phone_country_code?: string | null;
  country_of_residence?: string | null;
  in_featured_cohort: boolean;
  created_at: string;
};

export type AdminPaymentRow = {
  id: string;
  order_id: string;
  status: string;
  provider: string;
  amount: number;
  currency: string;
  user_email: string;
  user_name: string | null;
  cohort_name: string | null;
  course_title: string | null;
  confirmed_at: string | null;
  created_at: string;
  crypto_currency: string | null;
  crypto_expected_amount: string | null;
  crypto_actual_amount: string | null;
  crypto_shortfall: string | null;
};

export type AdminCohortMemberRow = {
  id: string;
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified: boolean;
  joined_at: string;
};

export type AdminFeaturedCohort = {
  id: string;
  name: string;
  slug: string;
  status: string;
  price: number;
  currency: string;
  student_seats: number;
  staff_count: number;
  confirmed_payments: number;
  pending_payments: number;
  registration_deadline: string | null;
  starts_at: string | null;
};

export type AdminOverview = {
  users_total: number;
  students_total: number;
  staff_total?: number;
  users_verified: number;
  signups_24h: number;
  signups_7d: number;
  payments_confirmed: number;
  payments_pending: number;
  revenue_by_currency: Array<{
    currency: string;
    confirmed_amount: number;
    pending_amount: number;
  }>;
  featured_cohort: AdminFeaturedCohort | null;
  recent_signups: AdminUserRow[];
  recent_payments: AdminPaymentRow[];
  staff_users?: AdminUserRow[];
  roles?: AdminNamedCount[];
};

export type AdminCohortDetail = {
  cohort: AdminFeaturedCohort;
  members: AdminCohortMemberRow[];
  payments: AdminPaymentRow[];
};

export function getAdminOverview() {
  return apiFetch<AdminOverview>("/api/v1/admin/overview");
}

export type AdminCountPoint = {
  label: string;
  value: number;
};

export type AdminNamedCount = {
  name: string;
  value: number;
};

export type AdminRecentLearner = {
  user_email: string;
  user_name: string | null;
  course_title: string;
  last_activity_at: string;
};

export type AdminAnalytics = {
  users_total: number;
  students_total: number;
  users_verified: number;
  users_unverified: number;
  signups_24h: number;
  signups_7d: number;
  signups_30d: number;
  enrollments_active: number;
  enrollments_completed: number;
  lessons_completed: number;
  learners_active_7d: number;
  payments_confirmed: number;
  payments_pending: number;
  event_registrations: number;
  published_opportunities: number;
  opportunity_saves: number;
  published_insights: number;
  revenue_by_currency: Array<{
    currency: string;
    confirmed_amount: number;
    pending_amount: number;
  }>;
  featured_cohort: AdminFeaturedCohort | null;
  signups_by_day: AdminCountPoint[];
  enrollments_by_day: AdminCountPoint[];
  roles: AdminNamedCount[];
  countries: AdminNamedCount[];
  courses: AdminNamedCount[];
  opportunity_statuses: AdminNamedCount[];
  recent_learners: AdminRecentLearner[];
  untracked: string[];
};

export function getAdminAnalytics() {
  return apiFetch<AdminAnalytics>("/api/v1/admin/analytics");
}

export function getAdminUsers(limit = 200) {
  return apiFetch<AdminUserRow[]>(`/api/v1/admin/users?limit=${limit}`);
}

/** Active staff accounts only (role != student) — used for tutor access pickers. */
export function getAdminStaffUsers(limit = 500) {
  return apiFetch<AdminUserRow[]>(`/api/v1/admin/users?limit=${limit}&staff_only=true`);
}

export type AdminProfile = AdminUserRow & {
  discord_username?: string | null;
  telegram_username?: string | null;
  github_url?: string | null;
  x_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  portfolio_public?: boolean;
};

export type AdminCourseEnrollment = {
  course_id: string;
  course_title: string;
  course_slug: string;
  status: string;
  enrolled_at: string;
  completed_at: string | null;
};

export type AdminCohortEnrollment = {
  cohort_id: string;
  cohort_name: string;
  cohort_slug: string;
  role: string;
  enrollment_status: string;
  certificate_eligible: boolean;
  joined_at: string;
};

export type AdminBillingAccountSummary = {
  account_id: string;
  plan_name: string | null;
  plan_type: string | null;
  currency: string | null;
  amount_paid: string;
  amount_outstanding: string;
  billing_status: string;
  access_blocked: boolean;
  next_due_date: string | null;
  next_due_amount: string | null;
};

export type AdminUserDetail = {
  profile: AdminProfile;
  courses: AdminCourseEnrollment[];
  cohorts: AdminCohortEnrollment[];
  billing_accounts: AdminBillingAccountSummary[];
  payments: AdminPaymentRow[];
};

export function getAdminUserDetail(userId: string) {
  return apiFetch<AdminUserDetail>(`/api/v1/admin/users/${encodeURIComponent(userId)}`);
}

export function removeAdminStaffAccess(userId: string) {
  return apiFetch<AdminUserRow>(`/api/v1/admin/users/${encodeURIComponent(userId)}/remove-staff-access`, {
    method: "POST",
  });
}

export function getAdminPayments(limit = 200) {
  return apiFetch<AdminPaymentRow[]>(`/api/v1/admin/payments?limit=${limit}`);
}

export function reconcileAdminPayment(orderId: string, paymentId?: string) {
  return apiFetch<AdminPaymentRow>(
    `/api/v1/admin/payments/${encodeURIComponent(orderId)}/reconcile`,
    { method: "POST", body: JSON.stringify({ payment_id: paymentId || null }) }
  );
}

export type ReconcileStaleResult = {
  scanned: number;
  confirmed: number;
  updated: number;
  failed: number;
};

export function reconcileStaleAdminPayments() {
  return apiFetch<ReconcileStaleResult>("/api/v1/admin/payments/reconcile-stale", {
    method: "POST",
  });
}

export type AdminCohortOption = {
  id: string;
  name: string;
  slug: string;
  status: string;
  course_title: string | null;
  sessions_count: number;
};

export type AdminLiveSessionResource = {
  title: string;
  url: string;
  kind: "slides" | "dataset" | "repo" | "reading" | "doc" | "other";
};

export type AdminLiveSessionRow = {
  id: string;
  cohort_id: string;
  cohort_name: string;
  cohort_slug: string;
  title: string;
  week_label: string;
  session_number: number;
  session_type: "teaching" | "office_hour";
  objectives: string[];
  resources: AdminLiveSessionResource[];
  assignment_summary: string | null;
  description?: string | null;
  timezone?: string;
  meeting_url?: string | null;
  instructor_name?: string | null;
  starts_at: string;
  ends_at: string;
  status: "scheduled" | "live" | "ended" | "cancelled";
  phase: "upcoming" | "live" | "ended" | "cancelled";
  recording_url: string | null;
  recording_status?: "none" | "processing" | "ready" | "failed";
  member_count: number;
  created_at: string;
  updated_at: string;
};

export type AdminLiveSessionInput = {
  cohort_id: string;
  title: string;
  week_label?: string;
  session_number: number;
  session_type: "teaching" | "office_hour";
  objectives?: string[];
  resources?: AdminLiveSessionResource[];
  assignment_summary?: string | null;
  description?: string | null;
  timezone?: string;
  meeting_url?: string | null;
  status?: string;
  recording_url?: string | null;
  starts_at: string;
  ends_at: string;
};

export function getAdminClassroomCohorts() {
  return apiFetch<AdminCohortOption[]>("/api/v1/admin/classroom/cohorts");
}

export function getAdminClassroomSessions(cohortId?: string) {
  const suffix = cohortId ? `?cohort_id=${encodeURIComponent(cohortId)}` : "";
  return apiFetch<AdminLiveSessionRow[]>(`/api/v1/admin/classroom/sessions${suffix}`);
}

export function createAdminClassroomSession(payload: AdminLiveSessionInput) {
  return apiFetch<AdminLiveSessionRow>("/api/v1/admin/classroom/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminClassroomSession(
  sessionId: string,
  payload: Partial<AdminLiveSessionInput> & { status?: string; recording_url?: string | null }
) {
  return apiFetch<AdminLiveSessionRow>(
    `/api/v1/admin/classroom/sessions/${encodeURIComponent(sessionId)}`,
    { method: "PATCH", body: JSON.stringify(payload) }
  );
}

export function cancelAdminClassroomSession(sessionId: string) {
  return apiFetch<AdminLiveSessionRow>(
    `/api/v1/admin/classroom/sessions/${encodeURIComponent(sessionId)}/cancel`,
    { method: "POST" }
  );
}

export function deleteAdminClassroomSession(sessionId: string) {
  return apiFetch<void>(`/api/v1/admin/classroom/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}

export type AdminRecordingSyncResult = {
  total: number;
  updated: number;
  skipped: number;
  failed: number;
};

export function syncAdminClassroomRecording(sessionId: string) {
  return apiFetch<AdminLiveSessionRow>(
    `/api/v1/admin/classroom/sessions/${encodeURIComponent(sessionId)}/sync-recording`,
    { method: "POST" }
  );
}

export function syncAdminClassroomRecordings(cohortId?: string) {
  const suffix = cohortId ? `?cohort_id=${encodeURIComponent(cohortId)}` : "";
  return apiFetch<AdminRecordingSyncResult>(`/api/v1/admin/classroom/sync-recordings${suffix}`, {
    method: "POST",
  });
}

export type AdminStudentRow = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  cohorts: string[];
  courses: string[];
  course_ids: string[];
  cohort_ids: string[];
  plan_name: string | null;
  plan_type: string | null;
  payment_status: "paid" | "partial" | "unpaid";
  currency: string | null;
  amount_paid: string;
  amount_outstanding: string;
  installments_total: number;
  installments_paid: number;
  next_due_date: string | null;
  next_due_amount: string | null;
  next_due_status: string | null;
  has_outstanding: boolean;
  access_blocked: boolean;
  billing_account_id: string | null;
  created_at: string;
};

export type AdminStudentList = {
  rows: AdminStudentRow[];
  total: number;
  paid: number;
  partial: number;
  unpaid: number;
};

export type AdminInstallmentRow = {
  obligation_id: string;
  billing_account_id: string;
  user_id: string;
  email: string;
  full_name: string | null;
  cohort_name: string | null;
  course_title: string | null;
  plan_name: string | null;
  sequence_number: number;
  installments_total: number;
  description: string;
  amount_due: string;
  currency: string;
  due_date: string | null;
  status: "upcoming" | "open" | "processing" | "past_due" | "paid" | "waived" | "cancelled";
  bucket: "overdue" | "due_soon" | "upcoming" | "paid";
  days_until_due: number | null;
  reminder_sent_at: string | null;
};

export type ReminderResult = { sent: number; skipped: number; failed: number };

export function getAdminStudents(params?: {
  paymentStatus?: string;
  plan?: string;
  cohortId?: string;
  courseId?: string;
  hasOutstanding?: boolean;
  q?: string;
}) {
  const qs = new URLSearchParams();
  if (params?.paymentStatus && params.paymentStatus !== "all")
    qs.set("payment_status", params.paymentStatus);
  if (params?.plan && params.plan !== "all") qs.set("plan", params.plan);
  if (params?.cohortId) qs.set("cohort_id", params.cohortId);
  if (params?.courseId) qs.set("course_id", params.courseId);
  if (params?.hasOutstanding) qs.set("has_outstanding", "true");
  if (params?.q) qs.set("q", params.q);
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<AdminStudentList>(`/api/v1/admin/students${suffix}`);
}

export function getAdminInstallments(params?: { status?: string; cohortId?: string }) {
  const qs = new URLSearchParams();
  if (params?.status && params.status !== "all") qs.set("status", params.status);
  if (params?.cohortId) qs.set("cohort_id", params.cohortId);
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<AdminInstallmentRow[]>(`/api/v1/admin/installments${suffix}`);
}

export function remindAdminObligation(obligationId: string) {
  return apiFetch<ReminderResult>(
    `/api/v1/admin/obligations/${encodeURIComponent(obligationId)}/remind`,
    { method: "POST" }
  );
}

export function remindAdminInstallments(payload: { scope: string; cohort_id?: string | null }) {
  return apiFetch<ReminderResult>("/api/v1/admin/installments/remind", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAdminCohort(slug: string) {
  return apiFetch<AdminCohortDetail>(`/api/v1/admin/cohorts/${encodeURIComponent(slug)}`);
}

export type InviteInstructorResponse = {
  email: string;
  full_name: string | null;
  role: string;
  resent: boolean;
  promoted?: boolean;
  message: string;
};

export function inviteInstructor(email: string, fullName?: string) {
  return apiFetch<InviteInstructorResponse>("/api/v1/admin/instructors", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName || null,
    }),
  });
}

export function inviteOperations(email: string, fullName?: string) {
  return apiFetch<InviteInstructorResponse>("/api/v1/admin/operations", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName || null,
    }),
  });
}

export function invitePartnerships(email: string, fullName?: string) {
  return apiFetch<InviteInstructorResponse>("/api/v1/admin/partnerships", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName || null,
    }),
  });
}

export function inviteEditor(email: string, fullName?: string) {
  return apiFetch<InviteInstructorResponse>("/api/v1/admin/editors", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName || null,
    }),
  });
}

export function inviteAuthor(email: string, fullName?: string) {
  return apiFetch<InviteInstructorResponse>("/api/v1/admin/authors", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName || null,
    }),
  });
}

export function acceptStaffInvite(token: string, password: string) {
  return apiFetch<{ access_token: string; user: AuthUser }>("/api/v1/auth/accept-invite", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ token, password }),
  });
}

/* --- Referral Partner Program --- */

export type PartnerPublic = {
  id: string;
  status: "pending" | "active" | "suspended" | "rejected";
  referral_code: string | null;
  display_name: string;
  social_handle: string | null;
  promotion_channels: string | null;
  created_at: string;
  approved_at: string | null;
};

export type CurrencyBalanceRow = {
  currency: string;
  pending_commission: string;
  available_balance: string;
  total_paid_out: string;
  minimum_payout: string;
  estimated_usd_pending: string | null;
  estimated_usd_available: string | null;
  estimated_usd_paid_out: string | null;
};

export type PartnerDashboard = {
  clicks: number;
  registrations: number;
  paid_enrollments: number;
  conversion_rate: number;
  pending_commission: string;
  available_balance: string;
  total_paid_out: string;
  currency: string;
  referral_code: string | null;
  status: string;
  display_name: string;
  minimum_payout: string;
  commission_rate: string;
  hold_days: number;
  referral_link: string | null;
  balances_by_currency: CurrencyBalanceRow[];
  reporting_currency: string;
  estimated_usd_pending: string | null;
  estimated_usd_available: string | null;
  estimated_usd_paid_out: string | null;
  estimated_usd_portfolio: string | null;
  minimum_payout_thresholds: Record<string, string>;
};

export type PartnerConversionRow = {
  id: string;
  programme: string;
  learner_label: string;
  eligible_amount: string;
  commission_amount: string;
  currency: string;
  status: string;
  created_at: string;
  reporting_usd_equivalent: string | null;
};

export type PartnerPayoutRow = {
  id: string;
  amount: string;
  currency: string;
  status: string;
  requested_at: string;
  processed_at: string | null;
  admin_note: string | null;
};

export type AdminReferralOverview = {
  total_partners: number;
  active_partners: number;
  pending_applications: number;
  total_clicks: number;
  total_registrations: number;
  total_paid_enrollments: number;
  commission_pending: string;
  commission_available: string;
  commission_paid: string;
  currency: string;
  balances_by_currency: CurrencyBalanceRow[];
  reporting_currency: string;
  estimated_usd_pending: string | null;
  estimated_usd_available: string | null;
  estimated_usd_paid_out: string | null;
  estimated_usd_portfolio: string | null;
};

export type AdminConversionRow = {
  id: string;
  partner_name: string;
  learner_email: string;
  programme: string;
  payment_id: string;
  eligible_amount: string;
  commission_amount: string;
  currency: string;
  status: string;
  fraud_status: string;
  created_at: string;
  reporting_usd_equivalent: string | null;
};

export type LeaderboardEntry = {
  rank: number;
  display_name: string;
  successful_enrollments: number;
};

export function trackReferral(code: string, landingPath?: string, destination?: string) {
  return apiFetch<{ ok: boolean; redirect_path: string; anonymous_visitor_id: string }>(
    "/api/v1/referrals/track",
    {
      method: "POST",
      auth: false,
      body: JSON.stringify({
        code,
        landing_path: landingPath || null,
        destination: destination || null,
      }),
    }
  );
}

export function getReferralLeaderboard(period: "all" | "monthly" = "all") {
  return apiFetch<{ period: string; entries: LeaderboardEntry[] }>(
    `/api/v1/referrals/leaderboard?period=${period}`,
    { auth: false }
  );
}

export function applyReferralPartner(payload: {
  display_name: string;
  social_handle?: string;
  promotion_channels?: string;
  terms_accepted: boolean;
}) {
  return apiFetch<PartnerPublic>("/api/v1/partners/apply", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMyPartnerProfile() {
  return apiFetch<PartnerPublic | null>("/api/v1/partner/me");
}

export function getPartnerDashboard() {
  return apiFetch<PartnerDashboard>("/api/v1/partner/dashboard");
}

export function getPartnerConversions() {
  return apiFetch<PartnerConversionRow[]>("/api/v1/partner/conversions");
}

export function getPartnerPayouts() {
  return apiFetch<PartnerPayoutRow[]>("/api/v1/partner/payouts");
}

export function requestPartnerPayout(amount: string, currency = "USD", details?: string) {
  return apiFetch<PartnerPayoutRow>("/api/v1/partner/payouts", {
    method: "POST",
    body: JSON.stringify({
      amount,
      currency,
      payment_details_reference: details || null,
    }),
  });
}

export function getAdminReferralOverview() {
  return apiFetch<AdminReferralOverview>("/api/v1/admin/referrals/overview");
}

export function getAdminReferralPartners(status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<PartnerPublic[]>(`/api/v1/admin/referrals/partners${q}`);
}

export function patchAdminReferralPartner(
  partnerId: string,
  payload: { status?: string; note?: string; regenerate_code?: boolean }
) {
  return apiFetch<PartnerPublic>(`/api/v1/admin/referrals/partners/${partnerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getAdminReferralConversions(status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<AdminConversionRow[]>(`/api/v1/admin/referrals/conversions${q}`);
}

export function getAdminReferralPayouts(status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<PartnerPayoutRow[]>(`/api/v1/admin/referrals/payouts${q}`);
}

export function patchAdminReferralPayout(payoutId: string, status: string, note?: string) {
  return apiFetch<PartnerPayoutRow>(`/api/v1/admin/referrals/payouts/${payoutId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, note: note || null }),
  });
}

export function getAdminReferralReviewQueue() {
  return apiFetch<AdminConversionRow[]>("/api/v1/admin/referrals/review-queue");
}
