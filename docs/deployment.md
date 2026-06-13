# Deployment Guide

## Supabase

1. Create a free project.
2. Apply `supabase/migrations`.
3. Enable email magic-link authentication and add the Vercel URL as an allowed
   redirect.
4. Copy the project URL and publishable key. Never expose the service-role key
   to the browser.

## FastAPI on Render

Create a Render Blueprint from the repository-level `render.yaml`, or configure
a Web Service with root directory `apps/api` and these commands:

```text
Build: uv sync --frozen --no-dev --active
Start: python -m uvicorn copilot.main:app --app-dir src --host 0.0.0.0 --port 10000
Health check: /health/ready
```

The `--active` flag tells uv to install into Render's active environment
(`/opt/render/project/src/.venv`) and prevents the virtual-environment mismatch
warning. The start command then uses that environment's Python directly and
binds the service to Render's conventional web-service port.

Configure:

```text
APP_ENV=production
APP_CORS_ORIGINS=["https://your-web-project.vercel.app"]
CLINICAL_TRIALS_BASE_URL=https://clinicaltrials.gov/api/v2
CLINICAL_TRIALS_FALLBACK_BASE_URL=https://your-web-project.vercel.app/api/clinical-trials
AUTH_DISABLED=false
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
NCBI_TOOL=oncology_trial_feasibility_copilot
NCBI_EMAIL=registered-developer@example.com
NCBI_API_KEY=...
GROQ_API_KEY=...
GROQ_MODEL=<account-verified production Llama model>
GROQ_FALLBACK_MODEL=<second account-verified production Llama model>
```

The API uses the caller's Supabase access token for PostgREST requests so RLS
remains authoritative.

The API calls ClinicalTrials.gov directly first. If the official service rejects
Render's shared outbound network with HTTP 403, it automatically retries through
the narrowly scoped Next.js relay. The relay accepts only study search and
NCT-record GET paths and still retrieves data from the official API.

## Next.js on Vercel

Set the root directory to `apps/web` and configure:

```text
API_SERVER_URL=https://oncology-trial-assistant.onrender.com
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
NEXT_PUBLIC_DEMO_MODE=false
```

Production browser requests always use the same-origin `/api/backend` route.
That Vercel route forwards to `API_SERVER_URL` server-to-server, eliminating
browser CORS and stale public API URL problems. Remove `NEXT_PUBLIC_API_URL`
from the Vercel project; it is used only for local development.

Verify the API before redeploying the web app:

```text
https://your-api-service.onrender.com/health/ready
```

It must return `{"status":"ready"}`.

Use Hobby only for this non-commercial portfolio demonstration. Monitor
function duration, database size, and egress before inviting broader traffic.
