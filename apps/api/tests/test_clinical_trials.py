import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from copilot.clients.clinical_trials import (
    ClinicalTrialsClient,
    TrialNotFoundError,
    map_study,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ctgov_study.json"


def test_map_study_preserves_source_and_normalizes_fields() -> None:
    payload = json.loads(FIXTURE.read_text())
    retrieved_at = datetime(2026, 6, 13, tzinfo=UTC)

    trial = map_study(payload, retrieved_at=retrieved_at)

    assert trial.nct_id == "NCT04267848"
    assert trial.phases == ["PHASE2"]
    assert trial.enrollment == 80
    assert trial.biomarker == "PD-L1"
    assert trial.molecule_class == "Checkpoint inhibitor"
    assert trial.target_geographies == ["United States"]
    assert trial.sites[0].state == "Massachusetts"
    assert trial.source.source_version == "2026-06-12"


@pytest.mark.asyncio
@respx.mock
async def test_get_study_maps_not_found() -> None:
    route = respx.get("https://example.test/studies/NCT00000000").mock(
        return_value=httpx.Response(404)
    )
    client = ClinicalTrialsClient("https://example.test", max_attempts=1)

    with pytest.raises(TrialNotFoundError):
        await client.get_study("nct00000000")

    request = route.calls[0].request
    assert request.headers["accept"] == "application/json"
    assert request.headers["user-agent"] == "OncologyTrialFeasibilityCopilot/0.1"


@pytest.mark.asyncio
@respx.mock
async def test_get_study_uses_fallback_after_forbidden_response() -> None:
    payload = json.loads(FIXTURE.read_text())
    direct = respx.get(
        "https://clinicaltrials.example/studies/NCT04267848"
    ).mock(return_value=httpx.Response(403))
    fallback = respx.get(
        "https://relay.example/studies/NCT04267848"
    ).mock(return_value=httpx.Response(200, json=payload))
    client = ClinicalTrialsClient(
        "https://clinicaltrials.example",
        fallback_base_url="https://relay.example",
        max_attempts=1,
    )

    trial = await client.get_study("NCT04267848")

    assert trial.nct_id == "NCT04267848"
    assert direct.called
    assert fallback.called
