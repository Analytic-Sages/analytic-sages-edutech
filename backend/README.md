# Backend

FastAPI authentication API for Analytic Sages (Phase 2).

## Prerequisites

- Python 3.11+
- Docker (Postgres + Redis from repo root)

```bash
# From repo root
docker compose up -d
cp .env.example .env   # set SECRET_KEY to a random 32+ char value
```

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

## Create admin user

```bash
ADMIN_EMAIL=admin@analyticsages.com ADMIN_PASSWORD='your-secure-password' python scripts/create_admin.py
```

## Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or: `bash scripts/dev.sh`

- API: http://localhost:8000
- Docs: http://localhost:8000/docs (development only)
- Health: http://localhost:8000/api/v1/health

## Auth endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create student account |
| POST | `/api/v1/auth/login` | Login (sets httpOnly refresh cookie; email must be verified) |
| POST | `/api/v1/auth/refresh` | Rotate session |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET | `/api/v1/auth/me` | Current user (Bearer access token) |
| POST | `/api/v1/auth/verify-email` | Verify email token |
| POST | `/api/v1/auth/resend-verification` | Resend verification email |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |

### Go-live checklist (real users)

1. Set a strong `SECRET_KEY` (32+ chars) and `ENVIRONMENT=production`
2. Set backend `FRONTEND_URL` to the HTTPS site origin (`https://www.analyticsages.io`). Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` (or Vercel) to the HTTPS **API** origin — that value is the rewrite destination. The browser calls same-origin `/api` so the refresh cookie stays first-party.
3. Set `EMAIL_API_KEY` (Resend) + verified `EMAIL_FROM` domain so verification/reset emails send. For Insights subscribe, also set `RESEND_AUDIENCE_ID` (the Audience / Segment ID in Resend). Custom one-off emails are sent from the Resend Broadcasts dashboard to that same list.
4. Optional Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. Add `https://www.analyticsages.io/api/v1/auth/google/callback` in Google Cloud (not the Render URL). Leave `GOOGLE_REDIRECT_URI` unset to derive it from `FRONTEND_URL`.
5. `COOKIE_SECURE` is forced on in production. Refresh cookies use `SameSite=Lax` on the site origin.
6. Smoke test: register → email link → enter dashboard → **refresh the page** → still signed in → close the tab → return still signed in

Without `EMAIL_API_KEY`, links are printed in API logs as `[dev-email]`.

### BDE cohort checkout & tuition plans

Production open registration + installments need seeded data, `BILLING_PLANS_ENABLED=true`, and for real charges `PAYMENT_MODE=live` with provider secrets. Full checklist: [`docs/bde-checkout-ops.md`](../docs/bde-checkout-ops.md).

```bash
python scripts/seed_blockchain_data_engineering.py
python scripts/seed_tuition_plans.py
# Render env: BILLING_PLANS_ENABLED=true, PAYMENT_MODE=live (+ Paystack/NOWPayments keys)
python scripts/verify_bde_checkout.py
```

## RBAC test routes

| Method | Path | Role |
|--------|------|------|
| GET | `/api/v1/admin/ping` | admin |
| GET | `/api/v1/instructor/ping` | instructor or admin |

## Security notes

- Passwords hashed with **Argon2id**
- Short-lived **JWT access tokens** + **httpOnly refresh cookies**
- Auth routes **rate limited** via Redis
- **CORS** restricted to `FRONTEND_URL`
- Verification/reset links logged to console in development when `EMAIL_API_KEY` is unset

## Payments (Epic D — mock providers)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/courses` | Published courses (seeded) |
| POST | `/api/v1/checkout` | Create checkout (auth). Body: `{ course_id \| cohort_id, provider }` |
| GET | `/api/v1/payments/{order_id}` | Payment status for current user |
| GET | `/api/v1/me/enrollments` | Active enrollments |
| POST | `/api/v1/webhooks/payments/{provider}` | Provider webhook (`paystack` \| `nowpayments`) |
| POST | `/api/v1/webhooks/payments/mock/confirm` | Dev-only unlock helper |

Providers: **Paystack**, **NOWPayments**. With empty API keys they return a mock checkout URL. Enrollment unlocks **only** after webhook confirmation — never from the frontend redirect.

```bash
# After migrations
python scripts/seed_courses.py
```

### Mock checkout flow

1. Login → get `access_token`
2. `POST /api/v1/checkout` with `provider: paystack|nowpayments`
3. Open `checkout_url` (frontend `/checkout/mock`)
4. Click **Simulate success** → calls mock confirm → creates enrollment
5. Check backend logs for receipt + enrollment emails

### When you go live

| Provider | Status | Keys |
|----------|--------|------|
| **NOWPayments** | Live invoice + IPN implemented | `NOWPAYMENTS_API_KEY`, `NOWPAYMENTS_IPN_SECRET`, `PUBLIC_API_URL` |
| **Paystack** | Live initialize + webhook implemented (NGN/USD) | `PAYSTACK_SECRET_KEY`, `PUBLIC_API_URL` |

#### NOWPayments (crypto)

1. Set `NOWPAYMENTS_API_KEY` and `NOWPAYMENTS_IPN_SECRET` (server-side only — never `NEXT_PUBLIC_*`).
2. Set `PUBLIC_API_URL` to the publicly reachable API base (HTTPS in production).
3. In the NOWPayments dashboard, use IPN callback:
   `{PUBLIC_API_URL}/api/v1/webhooks/payments/nowpayments`
4. Checkout creates a hosted **invoice**; enrollment unlocks only when IPN `payment_status` is `finished` (signature verified, amount checked).
5. Localhost cannot receive IPNs — use a tunnel for end-to-end tests.

### Image uploads (Insights articles, event banners)

Uploads go through `StorageService`. With `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` unset, it falls back to local disk (`STORAGE_DIR`, default `var/uploads`) — **only durable if that path is a persistent volume**; plain ephemeral disk is wiped on every deploy on most hosts, silently breaking already-published images.

Two ways to make uploads durable in production — pick one:

**Option A — Render Persistent Disk (simplest if you're already on Render)**

1. In the Render dashboard, open the backend service → **Disks** tab → **Add Disk**.
2. Set a mount path, e.g. `/var/data/uploads`, and a size (a few GB is plenty).
3. Set the env var `STORAGE_DIR=/var/data/uploads` on that service.
4. Leave `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` unset.
5. Deploy. New uploads land on the disk and survive future deploys.

Requires a paid Render instance plan (not available on the free tier), and a disk only attaches to **one** service instance — this won't work if you ever scale to multiple replicas.

**Option B — Supabase Storage (works at any scale, needs a Supabase project)**

| Env var | Purpose |
|---------|---------|
| `SUPABASE_URL` | Your Supabase project URL, e.g. `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only — never expose to the frontend) |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name (default `uploads`); create it in the Supabase dashboard and mark it **public** |

Once set, uploads go straight to Supabase Storage and return a permanent `https://.../storage/v1/object/public/...` URL instead of the local `/api/v1/media/...` path.

Once set, uploads go straight to Supabase Storage and return a permanent `https://.../storage/v1/object/public/...` URL instead of the local `/api/v1/media/...` path.
6. Prefer custody → **manual** withdrawals to treasury (ops policy, not code).

#### Paystack (cards / local + USD)

1. Set `PAYSTACK_SECRET_KEY` (server-side only).
2. Set `PUBLIC_API_URL` and register webhook:
   `{PUBLIC_API_URL}/api/v1/webhooks/payments/paystack`
3. Checkout uses **Initialize Transaction**. By default charges **NGN** (`PAYSTACK_CHARGE_CURRENCY`); USD catalog prices convert via `PAYSTACK_USD_TO_NGN_RATE`.
4. On `charge.success`, we verify the signature, call **Verify Transaction**, check charged amount/currency, then unlock enrollment / cohort seat.
5. Localhost needs a tunnel for webhooks.
6. To charge USD on Paystack instead, enable USD on your Paystack business and set `PAYSTACK_CHARGE_CURRENCY=USD`.

## Google login

| Mode | When | Behavior |
|------|------|----------|
| `mock` | Dev, no Google keys | `/api/v1/auth/google` → frontend mock Google page |
| `live` | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` set | Real Google OAuth redirect |
| `disabled` | Production without keys | Google login unavailable |

- `GET /api/v1/auth/providers` — frontend reads Google availability/mode
- `GET /api/v1/auth/google` — start OAuth (or mock redirect)
- `GET /api/v1/auth/google/callback` — live Google callback
- `POST /api/v1/auth/google/mock` — dev-only mock login

## Classroom V1 (RealtimeKit)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/classroom/sessions` | Sessions for the current user's cohorts |
| `GET /api/v1/classroom/sessions/{id}` | Session detail (objectives, resources, phase) |
| `POST /api/v1/classroom/sessions/{id}/join` | Authorize join; returns RealtimeKit token or mock mode |
| `GET /api/v1/classroom/calendar-token` | Personal classroom calendar subscribe URL |
| `GET /api/v1/classroom/calendar.ics` | iCalendar feed (bearer token or `?token=`) with reminders |
| `GET/POST /api/v1/admin/classroom/sessions` | Admin: list / create sessions |
| `PATCH/DELETE /api/v1/admin/classroom/sessions/{id}` | Admin: edit / delete a session |
| `POST /api/v1/admin/classroom/sessions/{id}/cancel` | Admin: cancel a session |
| `POST /api/v1/internal/classroom/sync-schedule` | Ops: re-provision the canonical 40-session schedule (token `CLASSROOM_SYNC_TOKEN` → `OPPORTUNITY_SYNC_TOKEN`) |

Admin staff can create and manage live sessions from **Admin → Live sessions**
(`/admin/classroom`) without a developer: pick a cohort, set title, week label,
session number/type (teaching or office hour), start/end times, objectives and an
assignment summary. Students see new sessions immediately (subject to the usual
phase rules). The cohort filter is applied client-side against one full fetch, and
the list is ordered Week 1 → Week 10 so the table always shows the complete
schedule for the selected cohort.

Seed demo cohort + sessions:

```bash
python scripts/seed_classroom.py --email student@example.com
alembic upgrade head   # includes 003_classroom
```

### Blockchain Data Engineering schedule

`scripts/seed_blockchain_data_engineering.py` seeds the BDE cohort **and** its full
schedule: **40 sessions** = 30 teaching sessions (Mon/Tue/Wed, 18:00–20:00 WAT) plus a
weekly Friday office hour (18:00–19:00 WAT) across 10 weeks, starting Mon 5 Oct 2026.
It is idempotent (keyed on `session_type` + `session_number`) and safe to re-run; pass
`--reset` to wipe and rebuild. Titles/objectives mirror the website curriculum
(`frontend/src/lib/blockchain-data-engineering-program.ts`).

```bash
python scripts/seed_blockchain_data_engineering.py
python scripts/seed_tuition_plans.py
```

Students and instructors can add individual sessions or the whole schedule to Google
Calendar, Outlook, or Apple Calendar (`.ics`). The "subscribe link" from
`/api/v1/classroom/calendar-token` keeps the schedule (and its 15-minute reminders) in
sync as dates change. Feed authorization matches the classroom: students see only their
cohorts, staff see everything.

Without Cloudflare keys, join returns `mode: "mock"` and the frontend shows a classroom shell you can walk through. With keys (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `REALTIMEKIT_APP_ID`), join creates/reuses a meeting and returns a participant auth token.

Default presets (must exist on your RealtimeKit app): `group_call_host` (instructor) and `group_call_participant` (student) so cam/mic work in class without a webinar “Join Stage” gate. For lecture-style webinars, switch to `webinar_presenter` / `webinar_viewer`. Override with `REALTIMEKIT_HOST_PRESET` / `REALTIMEKIT_PARTICIPANT_PRESET`.

## Admin: course authoring (no developer needed)

Staff (admin / operations / instructor) can build a full course from
**Admin → Courses → Create course** (`/admin/courses/new`) then
`/admin/courses/{slug}` (Details · Curriculum · Downloads · Preview):

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/courses/{slug}/detail` | Full course tree (modules + lessons + resources) |
| `POST/PATCH/DELETE /api/v1/admin/courses[/{slug}]` | Create / update / delete a course |
| `POST /api/v1/admin/courses/{slug}/modules` | Add a module |
| `PATCH/DELETE /api/v1/admin/modules/{id}` | Edit / delete a module |
| `POST /api/v1/admin/modules/{id}/lessons` | Add a lesson |
| `PATCH/DELETE /api/v1/admin/lessons/{id}` | Edit / delete a lesson |
| `POST /api/v1/admin/lessons/{id}/resources` | Attach a downloadable resource (by URL) |
| `POST /api/v1/admin/lessons/{id}/resources/upload` | Upload a PDF / slides / dataset / source / zip |
| `POST /api/v1/admin/lessons/{id}/video/direct-upload` | Cloudflare Stream direct upload → sets the lesson UID |
| `GET /api/v1/admin/videos/{uid}` | Cloudflare Stream video status/metadata |

Publishing is a boolean flag; the public self-paced API renders whatever is
published. `lessons_count` is kept in sync automatically.

### Lesson video (Cloudflare Stream)

Recorded lessons use **Cloudflare Stream**, reusing the same `CLOUDFLARE_ACCOUNT_ID`
+ `CLOUDFLARE_API_TOKEN` as the live classroom (one token with `Stream:Edit` +
`Realtime Admin` covers both). Set `CLOUDFLARE_STREAM_CUSTOMER_CODE` (the
`customer-xxxx` subdomain from the Stream dashboard) so playback/thumbnail URLs
resolve, and `NEXT_PUBLIC_CLOUDFLARE_STREAM_CUSTOMER_CODE` on the frontend for the
browser player. Leave the keys empty for mock mode: the upload endpoint returns a
mock UID and the lesson still saves, so authoring works without credentials.
YouTube remains supported (`video_provider="youtube"`).

## Quizzes

Multiple-choice quizzes attach to a course and optionally a module (`module_id`)
or lesson (`lesson_id`). Authoring lives in the course editor under **Quizzes**
(next to Curriculum): create a quiz, then add questions with 2–8 options and tap
the circle to mark the correct answer. Pass score is a 0–100 threshold.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/quizzes?course_slug=` | List quizzes (with attempt + pass-rate stats) |
| `GET /api/v1/admin/quizzes/{id}` | Quiz detail **including answer keys** |
| `POST /api/v1/admin/courses/{slug}/quizzes` | Create a quiz |
| `PATCH/DELETE /api/v1/admin/quizzes/{id}` | Edit / delete a quiz |
| `POST /api/v1/admin/quizzes/{id}/questions` | Add a question (+ options) |
| `PATCH/DELETE /api/v1/admin/quiz-questions/{id}` | Edit / delete a question |

Learner endpoints **never leak the answer key** — the correct option is stripped
and grading happens server-side:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/quizzes/{id}` | Questions + options (no `is_correct`), my best score |
| `POST /api/v1/quizzes/{id}/submit` | Grade answers → score, pass/fail, per-question explanation |
| `GET /api/v1/quizzes/{id}/attempts` | My attempt history |
| `GET /api/v1/quizzes/course/{slug}` | All published quizzes for a course |

Taking a quiz requires an active (or completed) enrollment; staff can preview
without one. Published module quizzes surface as `quiz` on each module in the
self-paced learn outline, so they appear in the lesson sidebar. Analytics on
**Admin → Analytics** now report `quizzes_published`, `quiz_attempts` and
`quiz_pass_rate`.

## Admin: students, collections & reminders

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/students` | Paid / partial / unpaid students with next-due info (filters: `payment_status`, `plan`, `cohort_id`, `has_outstanding`, `q`) |
| `GET /api/v1/admin/installments` | Installment board with buckets: `overdue` / `due_soon` / `upcoming` / `paid` |
| `POST /api/v1/admin/obligations/{id}/remind` | Email one installment reminder |
| `POST /api/v1/admin/installments/remind` | Bulk reminders (`{"scope": "overdue" | "due_soon" | "all"}`) |
| `POST /api/v1/internal/billing/run-reminders` | Token-protected cron/ops hook (`X-Billing-Reminders-Token`) |

**Admin UI:** `/admin/students` (paid vs unpaid filter + CSV export) and
`/admin/collections` (deadlines with per-row + bulk reminder buttons).

**Automated reminders:** set `BILLING_REMINDERS_ENABLED=true` for the in-process
sweep (hourly by default; `BILLING_REMINDER_LEAD_DAYS` controls the due-soon window),
and/or set `BILLING_REMINDERS_TOKEN` + `PUBLIC_API_URL` so the scheduled
`.github/workflows/billing-reminders.yml` job hits the internal endpoint daily. An
obligation is reminded once, then re-nagged every 3 days while it stays overdue.

## Not implemented yet (later phases)

- Attendance webhooks, assignments gradebook, recording → Cloudflare Stream pipeline
- Certificates (Certifier.io), AI lecture assets, assignments, notifications, search, AI tutor, analytics, portfolio
- Production email provider integration
