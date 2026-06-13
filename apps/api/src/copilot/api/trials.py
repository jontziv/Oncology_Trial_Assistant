from typing import Annotated

from fastapi import APIRouter, Depends, Query

from copilot.api.dependencies import get_trials_client
from copilot.clients.clinical_trials import ClinicalTrialsClient
from copilot.domain.models import TrialDraft, TrialSearchResponse

router = APIRouter(prefix="/v1/trials", tags=["trials"])
TrialsClient = Annotated[ClinicalTrialsClient, Depends(get_trials_client)]


@router.get("", response_model=TrialSearchResponse)
async def search_trials(
    query: Annotated[str, Query(min_length=2, max_length=200)],
    client: TrialsClient,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> TrialSearchResponse:
    return await client.search(query, page_token=cursor, limit=limit)


@router.get("/{nct_id}", response_model=TrialDraft)
async def get_trial(
    nct_id: str,
    client: TrialsClient,
) -> TrialDraft:
    return await client.get_study(nct_id)
