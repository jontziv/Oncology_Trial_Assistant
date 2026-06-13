from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from copilot.api.dependencies import (
    CurrentUser,
    get_analysis_repository,
    get_current_user,
    get_feasibility_service,
)
from copilot.clients.clinical_trials import UpstreamUnavailableError
from copilot.domain.models import (
    Analysis,
    AnalysisRun,
    AnalysisStatus,
    CreateAnalysisRequest,
    FeasibilityResult,
    RunAnalysisRequest,
    RunStatus,
    UpdateAnalysisRequest,
)
from copilot.persistence.repositories import AnalysisRepository
from copilot.services.feasibility import FeasibilityService

router = APIRouter(prefix="/v1/analyses", tags=["analyses"])

User = Annotated[CurrentUser, Depends(get_current_user)]
Repository = Annotated[AnalysisRepository, Depends(get_analysis_repository)]
Feasibility = Annotated[FeasibilityService, Depends(get_feasibility_service)]


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
    analyses = list(await repository.list(user.id))
    return [
        item.model_copy(update={"latest_run": await repository.latest_run(item.id, user.id)})
        for item in analyses
    ]


@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis(
    analysis_id: UUID,
    user: User,
    repository: Repository,
) -> Analysis:
    analysis = await repository.get(analysis_id, user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis.model_copy(
        update={"latest_run": await repository.latest_run(analysis_id, user.id)}
    )


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
    changes: dict[str, object] = {}
    if payload.title is not None:
        changes["title"] = payload.title
    if payload.trial is not None:
        changes["trial"] = payload.trial
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


@router.post(
    "/{analysis_id}/runs",
    response_model=AnalysisRun,
    status_code=status.HTTP_201_CREATED,
)
async def run_analysis(
    analysis_id: UUID,
    payload: RunAnalysisRequest,
    user: User,
    repository: Repository,
    feasibility: Feasibility,
) -> AnalysisRun:
    analysis = await repository.get(analysis_id, user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if not payload.force_refresh:
        existing = await repository.latest_run(analysis_id, user.id)
        if existing and existing.status == RunStatus.COMPLETE:
            return existing
    run = await repository.create_run(
        AnalysisRun(
            analysis_id=analysis.id,
            owner_id=user.id,
            status=RunStatus.RUNNING,
        )
    )
    try:
        result = await feasibility.analyze(analysis)
    except UpstreamUnavailableError as exc:
        await repository.update_run(
            run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "error_message": str(exc),
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public evidence source unavailable",
        ) from exc
    except Exception:
        await repository.update_run(
            run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "error_message": "Analysis failed unexpectedly",
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        raise
    completed_at = datetime.now(UTC)
    saved = await repository.update_run(
        run.model_copy(
            update={
                "status": RunStatus.COMPLETE,
                "methodology_version": result.methodology_version,
                "result": result,
                "completed_at": completed_at,
            }
        )
    )
    await repository.update(
        analysis.model_copy(
            update={
                "status": AnalysisStatus.COMPLETE,
                "latest_run": saved,
                "updated_at": completed_at,
            }
        )
    )
    return saved


@router.get("/{analysis_id}/runs/latest", response_model=AnalysisRun)
async def get_latest_run(
    analysis_id: UUID,
    user: User,
    repository: Repository,
) -> AnalysisRun:
    run = await repository.latest_run(analysis_id, user.id)
    if run is None:
        raise HTTPException(status_code=404, detail="No analysis run found")
    return run


@router.get("/{analysis_id}/results", response_model=FeasibilityResult)
async def get_results(
    analysis_id: UUID,
    user: User,
    repository: Repository,
) -> FeasibilityResult:
    run = await repository.latest_run(analysis_id, user.id)
    if run is None or run.result is None:
        raise HTTPException(status_code=404, detail="No analysis result found")
    return run.result
