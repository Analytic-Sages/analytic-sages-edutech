const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const ACCESS_TOKEN_KEY = "as_access_token";
/** Readable session flag for Next.js proxy (not the JWT). */
export const SESSION_COOKIE = "as_logged_in";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export function getApiBaseUrl() {
  return API_URL;
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

const PUBLIC_LOAD_ERROR = "We're having trouble loading this information. Please try again.";

function networkErrorMessage() {
  if (process.env.NODE_ENV !== "production") {
    console.warn(`API unreachable at ${API_URL}`);
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
        detail = PUBLIC_LOAD_ERROR;
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

export type SelfPacedModuleOutline = {
  id: string;
  title: string;
  description: string;
  order_index: number;
  lessons: SelfPacedLessonOutline[];
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
  last_activity_at: string | null;
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

export function listSelfPacedCourses() {
  return apiFetch<SelfPacedCourseCard[]>("/api/v1/self-paced/courses", { auth: false });
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
  | "other";

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
  lifecycle: EventLifecycle | string;
  registered: boolean;
  can_register: boolean;
  related_course_slug: string | null;
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
  youtube_live_url: string | null;
  recording_url: string | null;
  learn_topics: string[];
  audience: string[];
  prerequisites: string;
  related_course_slug: string | null;
  seo_title: string | null;
  seo_description: string | null;
  published: boolean;
  cancelled: boolean;
  lifecycle: EventLifecycle | string;
  registered_count: number;
  created_at: string;
  updated_at: string;
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
  youtube_live_url?: string | null;
  recording_url?: string | null;
  learn_topics?: string[];
  audience?: string[];
  prerequisites?: string;
  related_course_slug?: string | null;
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
  return apiFetch<EventCardPublic[]>(`/api/v1/events${query ? `?${query}` : ""}`);
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

export function createAdminEvent(payload: EventWritePayload) {
  return apiFetch<EventAdmin>("/api/v1/admin/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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

export type AdminUserRow = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified: boolean;
  is_active: boolean;
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
};

export type AdminCohortDetail = {
  cohort: AdminFeaturedCohort;
  members: AdminCohortMemberRow[];
  payments: AdminPaymentRow[];
};

export function getAdminOverview() {
  return apiFetch<AdminOverview>("/api/v1/admin/overview");
}

export function getAdminUsers(limit = 200) {
  return apiFetch<AdminUserRow[]>(`/api/v1/admin/users?limit=${limit}`);
}

export function getAdminPayments(limit = 200) {
  return apiFetch<AdminPaymentRow[]>(`/api/v1/admin/payments?limit=${limit}`);
}

export function getAdminCohort(slug: string) {
  return apiFetch<AdminCohortDetail>(`/api/v1/admin/cohorts/${encodeURIComponent(slug)}`);
}

export type InviteInstructorResponse = {
  email: string;
  full_name: string | null;
  role: string;
  resent: boolean;
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

export function acceptStaffInvite(token: string, password: string) {
  return apiFetch<{ access_token: string; user: AuthUser }>("/api/v1/auth/accept-invite", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ token, password }),
  });
}
