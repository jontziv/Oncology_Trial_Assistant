from fastapi.testclient import TestClient

from copilot.main import app
from copilot.services.protocol_parser import parse_protocol

PROTOCOL = """
Protocol title: Randomized Phase II Study of ABC-123 in EGFR-Mutated NSCLC
Indication: Metastatic non-small cell lung cancer
Investigational product: ABC-123
This is a randomized, open-label, 2-arm tyrosine kinase inhibitor study in the
United States and Canada.
Planned enrollment: 184 patients
Primary endpoint: Progression-Free Survival

Inclusion criteria:
- Histologically confirmed metastatic NSCLC
- EGFR exon 19 deletion or L858R mutation
- ECOG performance status 0 or 1

Exclusion criteria:
- Untreated symptomatic brain metastases
- Prior treatment with ABC-123

Statistical analysis:
The primary analysis will use a stratified log-rank test.
"""


def test_protocol_parser_extracts_core_decision_inputs() -> None:
    result = parse_protocol(PROTOCOL)

    assert result.trial.title.startswith("Randomized Phase II")
    assert result.trial.indication == "Metastatic non-small cell lung cancer"
    assert result.trial.phases == ["PHASE2"]
    assert result.trial.interventions[0].name == "ABC-123"
    assert result.trial.molecule_class == "tyrosine kinase inhibitor"
    assert result.trial.biomarker == "EGFR"
    assert result.trial.target_geographies == ["United States", "Canada"]
    assert result.trial.enrollment == 184
    assert result.trial.primary_endpoints[0].measure == "Progression-Free Survival"
    assert "Untreated symptomatic brain metastases" in result.trial.eligibility_criteria
    assert result.trial.study_design.allocation == "RANDOMIZED"
    assert result.trial.study_design.arm_count == 2
    assert not result.warnings


def test_protocol_parser_returns_review_warnings_for_missing_fields() -> None:
    result = parse_protocol(
        "Early oncology concept protocol\n"
        "This document describes an exploratory solid tumor treatment study "
        "whose operational details remain under development."
    )

    assert result.trial.indication == "Oncology indication to confirm"
    assert result.trial.enrollment == 100
    assert len(result.warnings) >= 5


def test_parse_protocol_api_returns_editable_trial_draft() -> None:
    response = TestClient(app).post("/v1/protocols/parse", json={"text": PROTOCOL})

    assert response.status_code == 200
    payload = response.json()
    assert payload["trial"]["enrollment"] == 184
    assert payload["parser_version"] == "protocol-parser-v1"
