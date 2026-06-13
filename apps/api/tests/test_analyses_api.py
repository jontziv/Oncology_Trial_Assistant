import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from copilot.clients.clinical_trials import UpstreamUnavailableError, map_study
from copilot.domain.models import Analysis
from copilot.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "ctgov_study.json"


def _trial_payload() -> dict[str, object]:
    trial = map_study(
        json.loads(FIXTURE.read_text()),
        retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )
    return trial.model_dump(mode="json")


def test_analysis_crud_is_scoped_to_owner() -> None:
    client = TestClient(app)
    owner = str(uuid4())
    other_user = str(uuid4())

    created = client.post(
        "/v1/analyses",
        headers={"X-Demo-User-Id": owner},
        json={"title": "NSCLC protocol review", "trial": _trial_payload()},
    )

    assert created.status_code == 201
    analysis_id = created.json()["id"]
    assert client.get(
        f"/v1/analyses/{analysis_id}",
        headers={"X-Demo-User-Id": other_user},
    ).status_code == 404

    updated = client.patch(
        f"/v1/analyses/{analysis_id}",
        headers={"X-Demo-User-Id": owner},
        json={"title": "Updated NSCLC review"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated NSCLC review"

    updated_trial = _trial_payload()
    updated_trial["biomarker"] = "PD-L1, EGFR"
    updated_protocol = client.patch(
        f"/v1/analyses/{analysis_id}",
        headers={"X-Demo-User-Id": owner},
        json={"trial": updated_trial},
    )
    assert updated_protocol.status_code == 200
    assert updated_protocol.json()["trial"]["biomarker"] == "PD-L1, EGFR"

    deleted = client.delete(
        f"/v1/analyses/{analysis_id}",
        headers={"X-Demo-User-Id": owner},
    )
    assert deleted.status_code == 204


def test_failed_analysis_run_is_persisted() -> None:
    class FailingFeasibilityService:
        async def analyze(self, analysis: Analysis) -> None:
            raise UpstreamUnavailableError("ClinicalTrials.gov unavailable")

    client = TestClient(app)
    owner = str(uuid4())
    app.state.feasibility_service = FailingFeasibilityService()
    try:
        created = client.post(
            "/v1/analyses",
            headers={"X-Demo-User-Id": owner},
            json={"title": "Failure audit", "trial": _trial_payload()},
        )
        analysis_id = created.json()["id"]

        response = client.post(
            f"/v1/analyses/{analysis_id}/runs",
            headers={"X-Demo-User-Id": owner},
            json={"force_refresh": True},
        )
        latest = client.get(
            f"/v1/analyses/{analysis_id}/runs/latest",
            headers={"X-Demo-User-Id": owner},
        )

        assert response.status_code == 503
        assert latest.status_code == 200
        assert latest.json()["status"] == "failed"
        assert latest.json()["error_message"] == "ClinicalTrials.gov unavailable"
    finally:
        del app.state.feasibility_service
