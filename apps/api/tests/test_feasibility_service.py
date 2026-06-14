import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from copilot.clients.clinical_trials import map_study
from copilot.clients.groq import GroqMemoClient
from copilot.domain.models import Analysis
from copilot.services.feasibility import FeasibilityService

FIXTURE = Path(__file__).parent / "fixtures" / "ctgov_study.json"


class FakeTrials:
    def __init__(self, candidates):
        self.candidates = candidates

    async def search_studies(self, query: str, *, limit: int = 40):
        assert query
        assert limit == 60
        return self.candidates


class FakePubMed:
    async def search(self, query: str, *, limit: int = 8):
        assert "lung cancer" in query.lower() or "nsclc" in query.lower()
        return [], []


@pytest.mark.asyncio
async def test_service_builds_complete_reproducible_result() -> None:
    target = map_study(
        json.loads(FIXTURE.read_text()),
        retrieved_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    comparable = target.model_copy(
        update={
            "nct_id": "NCT11111111",
            "overall_status": "COMPLETED",
            "start_date": date(2022, 1, 1),
            "start_date_type": "ACTUAL",
            "primary_completion_date": date(2024, 1, 1),
            "primary_completion_date_type": "ACTUAL",
            "enrollment_type": "ACTUAL",
        },
        deep=True,
    )
    service = FeasibilityService(
        FakeTrials([comparable]),  # type: ignore[arg-type]
        FakePubMed(),  # type: ignore[arg-type]
        GroqMemoClient(api_key="", model=""),
    )

    result = await service.analyze(
        Analysis(
            owner_id=UUID("00000000-0000-0000-0000-000000000001"),
            title="Test",
            trial=target,
        )
    )

    assert result.methodology_version == "oncology-feasibility-v0.3"
    assert len(result.components) == 5
    assert result.similar_trials[0].nct_id == "NCT11111111"
    assert result.memo.generated_by == "Deterministic template"
    assert f"CTGOV:{target.nct_id}" in {source.source_id for source in result.sources}
