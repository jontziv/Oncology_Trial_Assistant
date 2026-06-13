import json
from datetime import UTC, date, datetime
from pathlib import Path

from copilot.clients.clinical_trials import map_study
from copilot.services.methodology import (
    competition_analysis,
    eligibility_burden,
    endpoint_comparability,
    risk_band,
    score_components,
    select_similar_trials,
    timeline_benchmark,
)
from copilot.services.reference_data import load_disease_burden

FIXTURE = Path(__file__).parent / "fixtures" / "ctgov_study.json"


def _trial():
    return map_study(
        json.loads(FIXTURE.read_text()),
        retrieved_at=datetime(2026, 6, 13, tzinfo=UTC),
    )


def test_similarity_and_benchmarks_are_explainable() -> None:
    target = _trial()
    comparable = target.model_copy(
        update={
            "nct_id": "NCT11111111",
            "overall_status": "COMPLETED",
            "start_date": date(2022, 1, 1),
            "start_date_type": "ACTUAL",
            "primary_completion_date": date(2024, 1, 1),
            "primary_completion_date_type": "ACTUAL",
        },
        deep=True,
    )
    competing = target.model_copy(
        update={"nct_id": "NCT22222222", "overall_status": "RECRUITING"},
        deep=True,
    )

    similar = select_similar_trials(target, [comparable, competing])
    timeline = timeline_benchmark(target, [comparable, competing])
    competition = competition_analysis(target, [comparable, competing])
    endpoints = endpoint_comparability(target, [comparable, competing])

    assert len(similar) == 2
    assert similar[0].similarity_score > 80
    assert "phase" in similar[0].matched_features
    assert timeline.cohort_size == 1
    assert 23 < (timeline.median_months or 0) < 25
    assert competition.active_trial_count == 1
    assert endpoints.comparable_count == 2


def test_overall_score_exposes_weighted_components_and_sensitivity() -> None:
    target = _trial()
    eligibility = eligibility_burden(target)
    timeline = timeline_benchmark(target, [])
    competition = competition_analysis(target, [])
    endpoints = endpoint_comparability(target, [])
    components, overall, confidence, low, high = score_components(
        target,
        eligibility,
        timeline,
        competition,
        [],
        endpoints,
    )

    assert len(components) == 5
    assert round(sum(item.weight for item in components), 2) == 1
    assert 0 <= overall <= 100
    assert 0 <= confidence <= 1
    assert low <= overall <= high
    assert risk_band(overall).value in {"low", "moderate", "high"}


def test_uscs_boundary_does_not_invent_state_rates() -> None:
    burden = load_disease_burden()

    assert burden.dataset == "U.S. Cancer Statistics Public Use Database"
    assert burden.rates_per_100k == {}
    assert "SEER*Stat" in burden.limitation
