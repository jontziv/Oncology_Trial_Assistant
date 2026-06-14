from dataclasses import dataclass
from typing import Annotated, cast
from uuid import UUID

import httpx
from fastapi import Depends, Header, HTTPException, Request, status

from copilot.clients.clinical_trials import ClinicalTrialsClient
from copilot.clients.groq import GroqMemoClient
from copilot.clients.pubmed import PubMedClient
from copilot.config import Settings, get_settings
from copilot.persistence.repositories import (
    AnalysisRepository,
    InMemoryAnalysisRepository,
    SupabaseAnalysisRepository,
)
from copilot.services.feasibility import FeasibilityService

_memory_repository = InMemoryAnalysisRepository()


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    access_token: str | None
    is_demo: bool = False


async def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_demo_user_id: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if settings.auth_disabled:
        return CurrentUser(
            id=UUID(x_demo_user_id or settings.demo_user_id),
            access_token=None,
            is_demo=True,
        )
    if (
        settings.demo_access_enabled
        and x_demo_user_id == settings.demo_user_id
    ):
        return CurrentUser(
            id=UUID(settings.demo_user_id),
            access_token=None,
            is_demo=True,
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    access_token = authorization.split(" ", 1)[1]
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": settings.supabase_publishable_key,
                "authorization": f"Bearer {access_token}",
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return CurrentUser(id=UUID(response.json()["id"]), access_token=access_token)


def get_analysis_repository(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalysisRepository:
    if user.is_demo:
        return _memory_repository
    if not user.access_token or not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistence is not configured",
        )
    return SupabaseAnalysisRepository(
        settings.supabase_url,
        settings.supabase_publishable_key,
        user.access_token,
    )


def get_trials_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClinicalTrialsClient:
    override = getattr(request.app.state, "clinical_trials_client", None)
    if override is not None:
        return cast(ClinicalTrialsClient, override)
    return ClinicalTrialsClient(
        str(settings.clinical_trials_base_url),
        fallback_base_url=(
            str(settings.clinical_trials_fallback_base_url)
            if settings.clinical_trials_fallback_base_url
            else None
        ),
        timeout_seconds=settings.upstream_timeout_seconds,
        max_attempts=settings.upstream_max_attempts,
    )


def get_feasibility_service(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> FeasibilityService:
    override = getattr(request.app.state, "feasibility_service", None)
    if override is not None:
        return cast(FeasibilityService, override)
    trials = get_trials_client(request, settings)
    pubmed = PubMedClient(
        str(settings.ncbi_base_url),
        api_key=settings.ncbi_api_key,
        tool=settings.ncbi_tool,
        email=settings.ncbi_email,
        timeout_seconds=settings.upstream_timeout_seconds,
    )
    memo = GroqMemoClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        fallback_model=settings.groq_fallback_model,
    )
    return FeasibilityService(trials, pubmed, memo)
