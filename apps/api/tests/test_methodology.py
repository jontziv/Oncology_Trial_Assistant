import json
from datetime import UTC, date, datetime
from pathlib import Path

from copilot.clients.clinical_trials import map_study
from copilot.services.methodology import (
    competition_analysis,
    eligibility_burden,
    endpoint_comparability,
    geography_recommendations,
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
            "enrollment_type": "ACTUAL",
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
    assert timeline.median_enrollment == 80
    assert 3 < (timeline.median_participants_per_month or 0) < 4
    assert 23 < (timeline.projected_enrollment_months or 0) < 25
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


def test_uscs_reference_data_is_indication_specific() -> None:
    burden = load_disease_burden("metastatic non-small cell lung cancer")

    assert burden.dataset == "NCI/CDC State Cancer Profiles (NPCR + SEER)"
    assert burden.cancer_site == "Lung & Bronchus"
    assert len(burden.rates_per_100k) >= 50
    assert burden.rates_per_100k["Kentucky"] == 83.7

    unmatched = load_disease_burden("multiple myeloma")
    assert unmatched.rates_per_100k == {}
    assert "omitted" in unmatched.limitation


def test_uscs_reference_data_matches_lung_carcinoma_wording() -> None:
    burden = load_disease_burden("Lung Non-Small Cell Carcinoma")

    assert burden.cancer_site == "Lung & Bronchus"
    assert burden.rates_per_100k


def test_requested_non_us_country_is_ranked_without_history() -> None:
    target = _trial().model_copy(
        update={"target_geographies": ["Germany"], "sites": []},
        deep=True,
    )
    burden = load_disease_burden(target.indication)
    competition = competition_analysis(target, [])

    geography = geography_recommendations(target, [], competition, burden)

    assert [item.region for item in geography] == ["Germany"]
    assert geography[0].level == "country"
    assert geography[0].historical_trial_count == 0
