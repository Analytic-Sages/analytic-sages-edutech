# Analytic Sages — Frontend

Premium EdTech platform UI built with Next.js 16, React 19, TypeScript, Tailwind CSS v4, and shadcn/ui.

## Quick Start

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Next.js only loads env from this directory. Repo-root `.env` is for Docker/backend (`FRONTEND_URL`, secrets). The browser API origin is same-origin `/api` (Next.js rewrites to `NEXT_PUBLIC_API_URL`).

## Brand

- **Navy:** `#101A8A` — primary actions, sidebar active states
- **Orange:** `#F58220` — CTAs, accents, progress highlights
- **Typography:** Manrope (headings) + Inter (body)
- **Logo:** `public/logo.png`

## Route Map

| Section | Routes |
|---------|--------|
| **Marketing** | `/`, `/about`, `/courses`, `/courses/[slug]`, `/pricing`, `/community`, `/contact` |
| **Auth** | `/login`, `/register`, `/forgot-password`, `/verify-email` |
| **Student** | `/dashboard`, `/my-courses`, `/explore`, `/courses/[slug]/learn/[lessonId]`, `/courses/[slug]/quiz/[quizId]`, `/certificates`, `/profile`, `/settings` |
| **Admin** | `/admin`, `/admin/users`, `/admin/courses`, `/admin/courses/new`, `/admin/payments`, `/admin/certificates`, `/admin/analytics`, `/admin/settings` |
| **Dev** | `/design-system` — living style guide |

## Architecture

```
src/
├── app/              # Next.js App Router (route groups)
├── components/
│   ├── brand/        # Logo
│   ├── layout/       # Marketing header/footer, app shell
│   ├── course/       # CourseCard, LessonSidebar, CertificateCard
│   ├── auth/         # AuthForm
│   ├── shared/       # PageHeader, StatsCard, EmptyState
│   └── ui/           # shadcn/ui primitives
├── config/           # Site config, navigation
├── lib/              # Mock data, fonts, utils
└── types/            # Shared TypeScript types
```

## Mock Data

All pages use mock data from `src/lib/mock-data.ts`. Swap to TanStack Query + FastAPI when the backend is ready.

## Scripts

```bash
npm run dev      # Development server
npm run build    # Production build
npm run start    # Production server
npm run lint     # ESLint
```
