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
2. Set `FRONTEND_URL` / `NEXT_PUBLIC_API_URL` to your HTTPS hosts
3. Set `EMAIL_API_KEY` (Resend) + verified `EMAIL_FROM` domain so verification/reset emails send
4. Optional Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
5. `COOKIE_SECURE` is forced on in production
6. Smoke test: register → email link → sign in → cohort checkout

Without `EMAIL_API_KEY`, links are printed in API logs as `[dev-email]`.

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
| POST | `/api/v1/webhooks/payments/{provider}` | Provider webhook (`stripe` \| `paystack` \| `nowpayments`) |
| POST | `/api/v1/webhooks/payments/mock/confirm` | Dev-only unlock helper |

Providers: **Stripe**, **Paystack**, **NOWPayments**. With empty API keys they all return a mock checkout URL. Enrollment unlocks **only** after webhook confirmation — never from the frontend redirect.

```bash
# After migrations
python scripts/seed_courses.py
```

### Mock checkout flow

1. Login → get `access_token`
2. `POST /api/v1/checkout` with `provider: paystack|stripe|nowpayments`
3. Open `checkout_url` (frontend `/checkout/mock`)
4. Click **Simulate success** → calls mock confirm → creates enrollment
5. Check backend logs for receipt + enrollment emails

### When you go live

| Provider | Status | Keys |
|----------|--------|------|
| **NOWPayments** | Live invoice + IPN implemented | `NOWPAYMENTS_API_KEY`, `NOWPAYMENTS_IPN_SECRET`, `PUBLIC_API_URL` |
| **Paystack** | Live initialize + webhook implemented (NGN/USD) | `PAYSTACK_SECRET_KEY`, `PUBLIC_API_URL` |
| Stripe | Mock until live branch is implemented | `STRIPE_SECRET_KEY` |

#### NOWPayments (crypto)

1. Set `NOWPAYMENTS_API_KEY` and `NOWPAYMENTS_IPN_SECRET` (server-side only — never `NEXT_PUBLIC_*`).
2. Set `PUBLIC_API_URL` to the publicly reachable API base (HTTPS in production).
3. In the NOWPayments dashboard, use IPN callback:
   `{PUBLIC_API_URL}/api/v1/webhooks/payments/nowpayments`
4. Checkout creates a hosted **invoice**; enrollment unlocks only when IPN `payment_status` is `finished` (signature verified, amount checked).
5. Localhost cannot receive IPNs — use a tunnel for end-to-end tests.
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

Seed demo cohort + sessions:

```bash
python scripts/seed_classroom.py --email student@example.com
alembic upgrade head   # includes 003_classroom
```

Without Cloudflare keys, join returns `mode: "mock"` and the frontend shows a classroom shell you can walk through. With keys (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `REALTIMEKIT_APP_ID`), join creates/reuses a meeting and returns a participant auth token.

Default presets (must exist on your RealtimeKit app): `group_call_host` (instructor) and `group_call_participant` (student) so cam/mic work in class without a webinar “Join Stage” gate. For lecture-style webinars, switch to `webinar_presenter` / `webinar_viewer`. Override with `REALTIMEKIT_HOST_PRESET` / `REALTIMEKIT_PARTICIPANT_PRESET`.

## Not implemented yet (later phases)

- Attendance webhooks, assignments gradebook, recording → Bunny pipeline
- Full LMS (modules, lessons, Bunny VOD player, quizzes, certificates)
- Live Stripe / Paystack / NOWPayments API calls (adapters stubbed)
- Production email provider integration
