from datetime import UTC, datetime

from copilot.clients.clinical_trials import (
    ClinicalTrialsClient,
    UpstreamUnavailableError,
)
from copilot.clients.groq import GroqMemoClient
from copilot.clients.pubmed import PubMedClient
from copilot.domain.models import (
    Analysis,
    EvidenceSource,
    FeasibilityMemo,
    FeasibilityResult,
    ProtocolRecommendation,
    PublicationEvidence,
    ScoreComponent,
    TrialDraft,
)
from copilot.services.methodology import (
    METHODOLOGY_VERSION,
    competition_analysis,
    eligibility_burden,
    endpoint_comparability,
    geography_recommendations,
    protocol_recommendations,
    risk_band,
    score_components,
    select_similar_trials,
    timeline_benchmark,
)
from copilot.services.reference_data import load_disease_burden


class FeasibilityService:
    def __init__(
        self,
        trials: ClinicalTrialsClient,
        pubmed: PubMedClient,
        memo_client: GroqMemoClient,
    ) -> None:
        self._trials = trials
        self._pubmed = pubmed
        self._memo_client = memo_client

    async def analyze(self, analysis: Analysis) -> FeasibilityResult:
        target = analysis.trial
        warnings: list[str] = []
        candidates = await self._trials.search_studies(
            _trial_search_query(target),
            limit=60,
        )
        similar = select_similar_trials(target, candidates)
        selected_ids = {item.nct_id for item in similar}
        cohort = [trial for trial in candidates if trial.nct_id in selected_ids]
        if len(cohort) < 8:
            warnings.append(
                "The comparable cohort is small; benchmarks and confidence are limited."
            )

        eligibility = eligibility_burden(target)
        timeline = timeline_benchmark(target, cohort)
        competition = competition_analysis(target, cohort)
        burden = load_disease_burden()
        geography = geography_recommendations(target, cohort, competition, burden)
        endpoints = endpoint_comparability(target, cohort)

        target_source = EvidenceSource(
            source_id=f"CTGOV:{target.nct_id}",
            source_type="target_trial",
            title=target.title,
            url=target.source.url,
            record_id=target.nct_id,
            retrieved_at=target.source.retrieved_at,
            locator="ClinicalTrials.gov target protocol record",
        )
        trial_sources = [
            EvidenceSource(
                source_id=f"CTGOV:{item.nct_id}",
                source_type="trial",
                title=item.title,
                url=item.source.url,
                record_id=item.nct_id,
                retrieved_at=item.source.retrieved_at,
                locator="ClinicalTrials.gov protocol record",
            )
            for item in similar
        ]
        burden_source = EvidenceSource(
            source_id="USCS:PUBLIC_USE",
            source_type="disease_burden",
            title=burden.dataset,
            url=burden.source_url,
            record_id=burden.release_date,
            retrieved_at=datetime.now(UTC),
            locator=burden.cancer_site,
        )
        if not burden.rates_per_100k:
            warnings.append(burden.limitation)

        publications: list[PublicationEvidence] = []
        publication_sources: list[EvidenceSource] = []
        try:
            publications, publication_sources = await self._pubmed.search(
                _publication_query(target),
                limit=8,
            )
        except UpstreamUnavailableError:
            warnings.append(
                "PubMed was unavailable; the result uses trial records only."
            )

        recommendation_sources = [source.source_id for source in trial_sources]
        recommendations = protocol_recommendations(
            target,
            eligibility,
            competition,
            geography,
            endpoints,
            recommendation_sources,
        )
        components, overall, confidence, sensitivity_low, sensitivity_high = (
            score_components(
                target,
                eligibility,
                timeline,
                competition,
                geography,
                endpoints,
            )
        )
        sources = [target_source, *trial_sources, *publication_sources, burden_source]
        fallback = _deterministic_memo(
            overall=overall,
            band=risk_band(overall).value,
            confidence=confidence,
            components=components,
            recommendations=recommendations,
            source_ids=[source.source_id for source in sources],
            warnings=warnings,
        )
        result = FeasibilityResult(
            methodology_version=METHODOLOGY_VERSION,
            overall_score=overall,
            risk_band=risk_band(overall),
            confidence=confidence,
            confidence_label=_confidence_label(confidence),
            components=components,
            similar_trials=similar,
            timeline=timeline,
            eligibility=eligibility,
            competition=competition,
            geography=geography,
            endpoints=endpoints,
            recommendations=recommendations,
            publications=publications,
            memo=fallback,
            sources=sources,
            warnings=warnings,
            sensitivity_low=sensitivity_low,
            sensitivity_high=sensitivity_high,
        )
        generated = await self._memo_client.generate(
            result,
            allowed_source_ids={source.source_id for source in sources},
        )
        if generated is not None:
            result.memo = generated
        elif self._memo_client.configured:
            result.warnings.append(
                "Groq memo generation failed validation; deterministic memo shown."
            )
        else:
            result.warnings.append(
                "Groq is not configured with a verified production Llama model; "
                "deterministic memo shown."
            )
        return result


def _trial_search_query(target: TrialDraft) -> str:
    # Include the primary biomarker alongside the indication to improve
    # candidate quality while keeping retrieval broad enough to surface
    # different therapeutic approaches for comparison.
    parts = [target.indication]
    if target.biomarker:
        primary = target.biomarker.split(",")[0].strip()
        if primary:
            parts.append(primary)
    return " ".join(parts)


def _publication_query(target: TrialDraft) -> str:
    indication = target.indication
    if "nsclc" in indication.lower():
        indication_query = (
            '("non-small cell lung cancer"[Title/Abstract] '
            'OR NSCLC[Title/Abstract])'
        )
    else:
        indication_query = f'"{indication}"[Title/Abstract]'
    refinements: list[str] = []
    if target.interventions:
        refinements.append(
            f'"{target.interventions[0].name}"[Title/Abstract]'
        )
    if target.molecule_class:
        refinements.append(f'"{target.molecule_class}"[Title/Abstract]')
    if target.biomarker:
        refinements.extend(
            f'"{marker.strip()}"[Title/Abstract]'
            for marker in target.biomarker.split(",")
            if marker.strip()
        )
    if not refinements:
        return indication_query
    return f"{indication_query} AND ({' OR '.join(refinements[:4])})"


def _deterministic_memo(
    *,
    overall: float,
    band: str,
    confidence: float,
    components: list[ScoreComponent],
    recommendations: list[ProtocolRecommendation],
    source_ids: list[str],
    warnings: list[str],
) -> FeasibilityMemo:
    ranked = sorted(components, key=lambda item: item.weighted_contribution, reverse=True)
    risks = [f"{item.label}: {item.score:.1f}/100. {item.rationale}" for item in ranked[:3]]
    return FeasibilityMemo(
        generated_by="Deterministic template",
        executive_summary=(
            f"Illustrative enrollment risk is {band} at {overall:.1f}/100 with "
            f"{_confidence_label(confidence).lower()} data confidence. The rating "
            "is a transparent planning heuristic, not a validated prediction."
        ),
        key_risks=risks,
        recommendations=[item.recommendation for item in recommendations[:5]],
        limitations=[
            "ClinicalTrials.gov does not report reliable site-level accrual.",
            "Study start to primary completion is not recruitment duration.",
            *warnings[:3],
        ],
        citation_ids=source_ids[:12],
    )


def _confidence_label(value: float) -> str:
    if value < 0.45:
        return "Low"
    if value < 0.72:
        return "Medium"
    return "High"
