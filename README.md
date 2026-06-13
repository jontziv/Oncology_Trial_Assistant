# Oncology Trial Feasibility & Enrollment Risk Copilot

Portfolio-grade decision support for exploring public clinical-trial evidence.

> Illustrative methodology only. This application is not a validated prediction,
> clinical decision, regulatory, or site-selection system. Do not enter patient
> data, protected health information, or confidential protocol content.

## Implemented MVP

The current implementation includes:

- Search ClinicalTrials.gov and import a study by NCT ID.
- Review normalized source fields in an editable analysis form.
- Save, reopen, update, and delete analyses.
- Preserve source provenance and distinguish imported values from user edits.
- Enforce per-user access with Supabase Row Level Security.
- Run a versioned, deterministic feasibility analysis.
- Rank a transparent comparable-trial cohort.
- Compute eligibility burden, active competition, timeline proxy, endpoint
  comparability, state/country opportunity, overall risk, confidence, and
  sensitivity.
- Retrieve related PubMed records through NCBI E-utilities.
- Generate evidence-linked protocol recommendations and a deterministic memo.
- Use Groq only when a production Llama model has been explicitly verified and
  configured; otherwise show the deterministic memo.

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

USCS state disease-burden values are intentionally not bundled until a reviewed
SEER\*Stat export is supplied. The results screen identifies that missing input
and reduces geography confidence rather than inventing rates.
