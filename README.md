# Analytic Sages

Global Blockchain Analytics Learning Platform — **Learn. Build. Get Certified. Get Hired.**

Monorepo for the Analytic Sages MVP: a premium learning platform where students can register, purchase courses, watch lessons, track progress, complete quizzes, and earn certificates.

## Repository Structure

```
analytic-sages-edutech/
├── frontend/          # Next.js app (marketing + student + admin UI)
├── backend/           # FastAPI app (API, webhooks, background jobs)
├── shared/            # Shared types/constants (OpenAPI, etc.)
├── docs/              # Phase 0 artifacts (PRD, schema, API spec)
├── scripts/           # Dev helpers (seed DB, create admin, etc.)
├── infrastructure/    # Docker, CI, deployment config
├── docker-compose.yml # Local Postgres + Redis
└── docker-compose.dev.yml
```

## Prerequisites

- [Docker](https://www.docker.com/) (for Postgres & Redis)
- [Node.js](https://nodejs.org/) 20+ (frontend, coming in Phase 1)
- [Python](https://www.python.org/) 3.11+ (backend, coming in Phase 1)

## Local Development

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL and Redis. See `docker-compose.yml` for ports and credentials (defaults match `.env.example`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — marketing site, student dashboard, course player, admin portal (mock data).

### 3. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

See [backend/README.md](backend/README.md) for auth endpoints, admin seeding, and security details.

**Phase 2 milestone:** register, login, logout, email verification (Resend when configured), password reset, RBAC (admin / instructor / student). Go-live auth checklist in [backend/README.md](backend/README.md).

**Epic D (Payments):** mock Stripe + **live Paystack (NGN/USD)** + **live NOWPayments invoice/IPN** (when keys set) → webhook → enrollment unlock. Seed courses with `python scripts/seed_courses.py`. See [backend/README.md](backend/README.md).

**Classroom V1:** cohorts + live sessions + authorized RealtimeKit join. Seed with `python scripts/seed_classroom.py --email you@example.com`. Bunny Stream remains for recorded premium courses.

**Next phases:** recording → Bunny, attendance webhooks, assignments, live payment keys, admin cohort ops.

## MVP Scope (Phase 1 Launch)

- Public marketing website
- Authentication (email + Google)
- Student dashboard & course player (Bunny Stream)
- Progress tracking, quizzes, downloadable resources
- Payments (Paystack + Stripe)
- Certificates & admin portal

## License

Proprietary — Analytic Sages.
