# Deployment Guide

## Supabase

1. Create a free project.
2. Apply `supabase/migrations`.
3. Enable email magic-link authentication and add the Vercel URL as an allowed
   redirect.
4. Copy the project URL and publishable key. Never expose the service-role key
   to the browser.

## FastAPI on Vercel

Deploy `apps/api` as the Python project and configure:

```text
APP_ENV=production
APP_CORS_ORIGINS=["https://your-web-project.vercel.app"]
AUTH_DISABLED=false
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
```

The API uses the caller's Supabase access token for PostgREST requests so RLS
remains authoritative.

## Next.js on Vercel

Set the root directory to `apps/web` and configure:

```text
NEXT_PUBLIC_API_URL=https://your-api-project.vercel.app
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
NEXT_PUBLIC_DEMO_MODE=false
```

Use Hobby only for this non-commercial portfolio demonstration. Monitor
function duration, database size, and egress before inviting broader traffic.
