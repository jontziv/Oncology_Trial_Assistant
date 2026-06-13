from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from copilot.api.dependencies import (
    CurrentUser,
    get_analysis_repository,
    get_current_user,
)
from copilot.domain.models import (
    Analysis,
    CreateAnalysisRequest,
    UpdateAnalysisRequest,
)
from copilot.persistence.repositories import AnalysisRepository

router = APIRouter(prefix="/v1/analyses", tags=["analyses"])

User = Annotated[CurrentUser, Depends(get_current_user)]
Repository = Annotated[AnalysisRepository, Depends(get_analysis_repository)]


@router.post("", response_model=Analysis, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    payload: CreateAnalysisRequest,
    user: User,
    repository: Repository,
) -> Analysis:
    title = payload.title or f"{payload.trial.nct_id} feasibility review"
    return await repository.create(
        Analysis(owner_id=user.id, title=title, trial=payload.trial)
    )


@router.get("", response_model=list[Analysis])
async def list_analyses(user: User, repository: Repository) -> list[Analysis]:
    return list(await repository.list(user.id))


@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis(
    analysis_id: UUID,
    user: User,
    repository: Repository,
) -> Analysis:
    analysis = await repository.get(analysis_id, user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.patch("/{analysis_id}", response_model=Analysis)
async def update_analysis(
    analysis_id: UUID,
    payload: UpdateAnalysisRequest,
    user: User,
    repository: Repository,
) -> Analysis:
    analysis = await repository.get(analysis_id, user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    changes = payload.model_dump(exclude_none=True)
    changes["updated_at"] = datetime.now(UTC)
    return await repository.update(analysis.model_copy(update=changes))


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    user: User,
    repository: Repository,
) -> None:
    if not await repository.delete(analysis_id, user.id):
        raise HTTPException(status_code=404, detail="Analysis not found")

