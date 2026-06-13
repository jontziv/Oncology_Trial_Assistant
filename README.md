# Oncology Trial Feasibility & Enrollment Risk Copilot

Portfolio-grade decision support for exploring public clinical-trial evidence.

> Illustrative methodology only. This application is not a validated prediction,
> clinical decision, regulatory, or site-selection system. Do not enter patient
> data, protected health information, or confidential protocol content.

## Phase 1

The current implementation scope is the authenticated trial workspace:

- Search ClinicalTrials.gov and import a study by NCT ID.
- Review normalized source fields in an editable analysis form.
- Save, reopen, update, and delete analyses.
- Preserve source provenance and distinguish imported values from user edits.
- Enforce per-user access with Supabase Row Level Security.

Scoring, PubMed, geography, Groq, and memo generation begin only after the
Phase 1 acceptance gate.

## Repository

```text
apps/web/             Next.js user interface
apps/api/             FastAPI service and domain logic
packages/api-client/  Generated TypeScript API contract
supabase/migrations/  PostgreSQL schema and RLS policies
docs/                 Product, architecture, and methodology records
```

## Local Setup

Requirements: Node 24+, pnpm 10+, uv, and Supabase CLI.

```bash
pnpm install
uv sync --project apps/api --all-extras
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
```

Start the applications in separate terminals:

```bash
pnpm --filter @oncology/web dev
uv run --project apps/api uvicorn copilot.main:app --app-dir apps/api/src --reload
```

Run checks:

```bash
pnpm lint
pnpm typecheck
pnpm test
uv run --project apps/api ruff check apps/api
uv run --project apps/api mypy apps/api/src
uv run --project apps/api pytest apps/api
```

## Data Sources

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)
- [Supabase](https://supabase.com/docs)

ClinicalTrials.gov records are sponsor-submitted and can be incomplete or out
of date. The application records retrieval time and source locators so users
can inspect where imported values originated.
