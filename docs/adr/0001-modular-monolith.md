# ADR 0001: Modular Monolith

## Status

Accepted for Phase 1.

## Decision

Use one Next.js application, one FastAPI application, and Supabase PostgreSQL.
Keep API routes thin and separate domain models, external clients, persistence,
and workflows inside the FastAPI package.

## Consequences

- A small portfolio deployment remains understandable and inexpensive.
- Domain services can be extracted later without changing their contracts.
- Long-running analysis must remain bounded and resumable on serverless hosts.
