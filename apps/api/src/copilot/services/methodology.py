import math
import re
from collections import Counter, defaultdict
from statistics import median

from copilot.domain.models import (
    CompetitionAnalysis,
    CompetitionRegion,
    EligibilityBurden,
    EligibilityFactor,
    EndpointComparability,
    GeographyRecommendation,
    ProtocolRecommendation,
    RiskBand,
    ScoreComponent,
    SimilarTrial,
    TimelineBenchmark,
    TrialDraft,
)
from copilot.services.reference_data import DiseaseBurdenDataset

METHODOLOGY_VERSION = "oncology-feasibility-v0.2"
ACTIVE_STATUSES = {"RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"}
STATUS_WEIGHTS = {
    "RECRUITING": 1.0,
    "NOT_YET_RECRUITING": 0.6,
    "ENROLLING_BY_INVITATION": 0.8,
    "ACTIVE_NOT_RECRUITING": 0.2,
}
ENDPOINT_FAMILIES = {
    "overall survival": ("OS", "overall survival", "survival"),
    "progression-free survival": (
        "PFS",
        "progression free survival",
        "progression-free survival",
    ),
    "objective response": (
        "ORR",
        "objective response",
        "overall response rate",
        "response rate",
    ),
    "duration of response": ("DOR", "duration of response"),
    "safety": ("SAFETY", "adverse event", "toxicity", "safety"),
    "quality of life": ("QOL", "quality of life", "patient reported"),
}


def select_similar_trials(
    target: TrialDraft,
    candidates: list[TrialDraft],
    *,
    limit: int = 20,
) -> list[SimilarTrial]:
    scored: list[SimilarTrial] = []
    for candidate in candidates:
        if candidate.nct_id == target.nct_id:
            continue
        score, matches, mismatches = _similarity(target, candidate)
        if score < 20:
            continue
        scored.append(
            SimilarTrial(
                nct_id=candidate.nct_id,
                title=candidate.title,
                similarity_score=round(score, 1),
                overall_status=candidate.overall_status,
                phases=candidate.phases,
                enrollment=candidate.enrollment,
                start_date=candidate.start_date,
                primary_completion_date=candidate.primary_completion_date,
                us_site_count=sum(
                    site.country == "United States" for site in candidate.sites
                ),
                matched_features=matches,
                mismatched_features=mismatches,
                source=candidate.source,
            )
        )
    return sorted(scored, key=lambda item: item.similarity_score, reverse=True)[:limit]


def eligibility_burden(trial: TrialDraft) -> EligibilityBurden:
    text = trial.eligibility_criteria
    normalized = text.lower()
    lines = [
        line.strip(" -*\t")
        for line in text.splitlines()
        if line.strip(" -*\t")
    ]
    criteria = [
        line
        for line in lines
        if not re.fullmatch(
            r"(key )?(inclusion|exclusion) criteria:?", line, re.IGNORECASE
        )
    ]
    if len(criteria) < 2:
        criteria = [
            part.strip()
            for part in re.split(r"[.;]\s+", text)
            if len(part.strip()) > 8
        ]
    inclusion_text, exclusion_text = _split_eligibility(normalized)
    inclusion_count = _criterion_count(inclusion_text)
    exclusion_count = _criterion_count(exclusion_text)
    factors: list[EligibilityFactor] = []
    score = min(28.0, len(criteria) * 1.4)
    factors.append(
        EligibilityFactor(
            label="Criterion volume",
            points=round(score, 1),
            evidence=f"{len(criteria)} parsed criteria or clauses",
        )
    )
    patterns = [
        (
            "Biomarker selection",
            r"\b(egfr|alk|ros1|kras|braf|met|ret|ntrk|pd-l1|mutation|expression)\b",
            14,
        ),
        (
            "Prior-treatment constraints",
            (
                r"\b(prior therapy|previously treated|treatment[- ]naive|"
                r"lines? of therapy|refractory)\b"
            ),
            12,
        ),
        (
            "Laboratory and organ function",
            r"\b(adequate organ|creatinine|bilirubin|platelet|neutrophil|hemoglobin|ast|alt)\b",
            10,
        ),
        (
            "CNS restrictions",
            r"\b(cns|brain metast|central nervous system|leptomeningeal)\b",
            10,
        ),
        (
            "Performance status",
            r"\b(ecog|performance status|karnofsky)\b",
            8,
        ),
        (
            "Washout requirements",
            r"\b(washout|within \d+ (days|weeks)|at least \d+ (days|weeks))\b",
            8,
        ),
        (
            "Procedural burden",
            r"\b(biopsy|measurable disease|imaging|contraception|pregnancy test)\b",
            10,
        ),
    ]
    for label, pattern, points in patterns:
        matches = re.findall(pattern, normalized, re.IGNORECASE)
        if matches:
            applied = min(points, 4 + len(matches) * 2)
            score += applied
            factors.append(
                EligibilityFactor(
                    label=label,
                    points=round(applied, 1),
                    evidence=f"{len(matches)} matching clause(s)",
                )
            )
    score = min(100.0, score)
    return EligibilityBurden(
        score=round(score, 1),
        band=_band(score),
        criterion_count=len(criteria),
        inclusion_count=inclusion_count,
        exclusion_count=exclusion_count,
        factors=factors,
        confidence=0.85 if len(criteria) >= 5 else 0.6,
        methodology=(
            "Rule-based burden index using criterion volume and explicit protocol "
            "constraints; it is not a patient-availability model."
        ),
    )


def timeline_benchmark(
    target: TrialDraft,
    cohort: list[TrialDraft],
) -> TimelineBenchmark:
    durations: list[float] = []
    excluded = 0
    for trial in cohort:
        if (
            trial.start_date_type != "ACTUAL"
            or trial.primary_completion_date_type != "ACTUAL"
        ):
            excluded += 1
            continue
        if not trial.start_date or not trial.primary_completion_date:
            excluded += 1
            continue
        days = (trial.primary_completion_date - trial.start_date).days
        if days < 30 or days > 3652:
            excluded += 1
            continue
        durations.append(days / 30.4375)
    durations.sort()
    target_months = None
    if (
        target.start_date
        and target.primary_completion_date
        and target.start_date_type == "ACTUAL"
        and target.primary_completion_date_type == "ACTUAL"
    ):
        days = (target.primary_completion_date - target.start_date).days
        if 30 <= days <= 3652:
            target_months = days / 30.4375
    if not durations:
        return TimelineBenchmark(
            cohort_size=0,
            excluded_count=excluded,
            target_months=_rounded(target_months),
            confidence=0.15,
            limitation=(
                "No usable actual start-to-primary-completion intervals were "
                "available. This metric is not recruitment duration."
            ),
        )
    q1 = _percentile(durations, 25)
    q3 = _percentile(durations, 75)
    percentile = None
    if target_months is not None:
        percentile = 100 * sum(value <= target_months for value in durations) / len(
            durations
        )
    return TimelineBenchmark(
        median_months=round(median(durations), 1),
        q1_months=round(q1, 1),
        q3_months=round(q3, 1),
        cohort_size=len(durations),
        excluded_count=excluded,
        target_months=_rounded(target_months),
        percentile=_rounded(percentile),
        confidence=min(0.9, 0.35 + len(durations) / 30),
        limitation=(
            "Primary completion includes treatment and follow-up; it is a study "
            "timeline proxy, not observed recruitment duration."
        ),
    )


def competition_analysis(
    target: TrialDraft,
    cohort: list[TrialDraft],
) -> CompetitionAnalysis:
    active = [trial for trial in cohort if trial.overall_status in ACTIVE_STATUSES]
    region_trials: dict[str, set[str]] = defaultdict(set)
    region_sites: Counter[str] = Counter()
    region_density: dict[str, float] = defaultdict(float)
    target_sites: Counter[str] = Counter()
    for trial in active:
        status_weight = STATUS_WEIGHTS.get(trial.overall_status, 0.0)
        for site in trial.sites:
            if site.country != "United States" or not site.state:
                continue
            region_trials[site.state].add(trial.nct_id)
            region_sites[site.state] += 1
            region_density[site.state] += status_weight
    for site in target.sites:
        if site.country == "United States" and site.state:
            target_sites[site.state] += 1
    region_names = set(region_trials) | set(target_sites)
    rows = [
        CompetitionRegion(
            region=name,
            active_trial_count=len(region_trials[name]),
            active_site_count=region_sites[name],
            weighted_density=round(region_density[name], 1),
            target_site_count=target_sites[name],
        )
        for name in region_names
    ]
    rows.sort(key=lambda item: item.weighted_density, reverse=True)
    active_us_sites = sum(row.active_site_count for row in rows)
    score = min(100.0, len(active) * 5 + math.sqrt(active_us_sites) * 6)
    return CompetitionAnalysis(
        score=round(score, 1),
        active_trial_count=len(active),
        active_us_site_count=active_us_sites,
        regions=rows[:20],
        confidence=min(0.9, 0.35 + len(cohort) / 35),
        limitation=(
            "Density uses registered active trials and listed sites. It does not "
            "measure actual site capacity, activation timing, or accrual."
        ),
    )


def geography_recommendations(
    target: TrialDraft,
    cohort: list[TrialDraft],
    competition: CompetitionAnalysis,
    burden: DiseaseBurdenDataset,
) -> list[GeographyRecommendation]:
    history: dict[str, set[str]] = defaultdict(set)
    facilities: dict[str, Counter[str]] = defaultdict(Counter)
    country_history: dict[str, set[str]] = defaultdict(set)
    country_facilities: dict[str, Counter[str]] = defaultdict(Counter)
    country_active_sites: Counter[str] = Counter()
    target_countries = {country.casefold() for country in target.target_geographies}
    for trial in cohort:
        for site in trial.sites:
            country_history[site.country].add(trial.nct_id)
            if site.facility:
                country_facilities[site.country][site.facility] += 1
            if trial.overall_status in ACTIVE_STATUSES:
                country_active_sites[site.country] += 1
            if site.country == "United States" and site.state:
                history[site.state].add(trial.nct_id)
                if site.facility:
                    facilities[site.state][site.facility] += 1
    competing = {row.region: row.active_site_count for row in competition.regions}
    target_states = {
        site.state
        for site in target.sites
        if site.country == "United States" and site.state
    }
    max_history = max((len(value) for value in history.values()), default=1)
    max_competing = max(1, max(competing.values(), default=0))
    state_recommendations: list[GeographyRecommendation] = []
    for state in sorted(set(history) | target_states):
        footprint = len(history[state]) / max_history
        inverse_competition = 1 - competing.get(state, 0) / max_competing
        burden_rate = burden.rates_per_100k.get(state)
        if burden_rate is None:
            opportunity = 100 * (0.65 * footprint + 0.35 * inverse_competition)
            confidence = 0.55
            burden_note = "Official state burden not loaded"
        else:
            max_rate = max(burden.rates_per_100k.values(), default=burden_rate)
            opportunity = 100 * (
                0.45 * (burden_rate / max_rate)
                + 0.35 * footprint
                + 0.20 * inverse_competition
            )
            confidence = 0.78
            burden_note = f"USCS rate {burden_rate:.1f} per 100,000"
        state_recommendations.append(
            GeographyRecommendation(
                region=state,
                level="state",
                opportunity_score=round(opportunity, 1),
                historical_trial_count=len(history[state]),
                active_competing_sites=competing.get(state, 0),
                candidate_facilities=[
                    name for name, _ in facilities[state].most_common(4)
                ],
                disease_burden_rate=burden_rate,
                rationale=(
                    f"{burden_note}; {len(history[state])} comparable historical "
                    f"trials and {competing.get(state, 0)} active competing sites."
                ),
                confidence=confidence,
            )
        )
    max_country_history = max(
        (len(value) for value in country_history.values()), default=1
    )
    max_country_competition = max(1, max(country_active_sites.values(), default=0))
    country_recommendations: list[GeographyRecommendation] = []
    for country, trials in country_history.items():
        is_target = country.casefold() in target_countries
        opportunity = min(
            100,
            100
            * (
                0.65 * len(trials) / max_country_history
                + 0.25
                * (1 - country_active_sites[country] / max_country_competition)
            )
            + (10 if is_target else 0),
        )
        country_recommendations.append(
            GeographyRecommendation(
                region=country,
                level="country",
                opportunity_score=round(opportunity, 1),
                historical_trial_count=len(trials),
                active_competing_sites=country_active_sites[country],
                candidate_facilities=[
                    name for name, _ in country_facilities[country].most_common(4)
                ],
                rationale=(
                    f"{len(trials)} comparable historical trials and "
                    f"{country_active_sites[country]} active comparable sites"
                    + ("; included in the requested geographies." if is_target else ".")
                    + " No cross-country disease-burden adjustment is applied."
                ),
                confidence=0.55 if is_target else 0.5,
            )
        )
    ranked_states = sorted(
        state_recommendations, key=lambda item: item.opportunity_score, reverse=True
    )[:12]
    ranked_countries = sorted(
        country_recommendations,
        key=lambda item: item.opportunity_score,
        reverse=True,
    )[:8]
    return [*ranked_states, *ranked_countries]


def endpoint_comparability(
    target: TrialDraft,
    cohort: list[TrialDraft],
) -> EndpointComparability:
    target_family = _endpoint_family(target.primary_endpoints[0].measure)
    distribution: Counter[str] = Counter()
    comparable = 0
    for trial in cohort:
        family = _endpoint_family(trial.primary_endpoints[0].measure)
        distribution[family] += 1
        comparable += family == target_family
    score = 50.0 if not cohort else 100 * comparable / len(cohort)
    return EndpointComparability(
        score=round(score, 1),
        target_family=target_family,
        cohort_distribution=dict(distribution.most_common()),
        comparable_count=comparable,
        cohort_size=len(cohort),
        rationale=(
            f"{comparable} of {len(cohort)} comparable trials use the "
            f"{target_family} primary-endpoint family."
        ),
        confidence=min(0.9, 0.3 + len(cohort) / 30),
    )


def score_components(
    target: TrialDraft,
    eligibility: EligibilityBurden,
    timeline: TimelineBenchmark,
    competition: CompetitionAnalysis,
    geography: list[GeographyRecommendation],
    endpoints: EndpointComparability,
) -> tuple[list[ScoreComponent], float, float, float, float]:
    timeline_score = 50.0
    if timeline.target_months and timeline.median_months:
        timeline_score = min(100.0, 50 * timeline.target_months / timeline.median_months)
    state_geography = [item for item in geography if item.level == "state"]
    geography_score = (
        100 - state_geography[0].opportunity_score if state_geography else 60.0
    )
    endpoint_risk = 100 - endpoints.score
    values = [
        (
            "eligibility",
            "Eligibility burden",
            eligibility.score,
            0.25,
            eligibility.confidence,
            f"{eligibility.criterion_count} criteria; {eligibility.band.value} burden.",
        ),
        (
            "competition",
            "Active competition",
            competition.score,
            0.25,
            competition.confidence,
            f"{competition.active_trial_count} active comparable trials.",
        ),
        (
            "timeline",
            "Study timeline proxy",
            timeline_score,
            0.20,
            timeline.confidence,
            timeline.limitation,
        ),
        (
            "geography",
            "Geographic opportunity",
            geography_score,
            0.20,
            state_geography[0].confidence if state_geography else 0.25,
            (
                f"Best observed state opportunity is {state_geography[0].region}."
                if state_geography
                else "No usable US site geography was found."
            ),
        ),
        (
            "endpoints",
            "Endpoint comparability",
            endpoint_risk,
            0.10,
            endpoints.confidence,
            endpoints.rationale,
        ),
    ]
    components = [
        ScoreComponent(
            key=key,
            label=label,
            score=round(score, 1),
            weight=weight,
            weighted_contribution=round(score * weight, 1),
            confidence=confidence,
            rationale=rationale,
            inputs={"target_nct_id": target.nct_id},
        )
        for key, label, score, weight, confidence, rationale in values
    ]
    overall = sum(item.score * item.weight for item in components)
    confidence = sum(item.confidence * item.weight for item in components)
    perturbations: list[float] = []
    for index, _component in enumerate(components):
        for multiplier in (0.8, 1.2):
            weights = [item.weight for item in components]
            weights[index] *= multiplier
            total_weight = sum(weights)
            perturbations.append(
                sum(
                    item.score * weight
                    for item, weight in zip(components, weights, strict=True)
                )
                / total_weight
            )
    return (
        components,
        round(overall, 1),
        round(confidence, 2),
        round(min(perturbations), 1),
        round(max(perturbations), 1),
    )


def protocol_recommendations(
    target: TrialDraft,
    eligibility: EligibilityBurden,
    competition: CompetitionAnalysis,
    geography: list[GeographyRecommendation],
    endpoints: EndpointComparability,
    trial_source_ids: list[str],
) -> list[ProtocolRecommendation]:
    recommendations: list[ProtocolRecommendation] = []
    evidence = trial_source_ids[:5] or [f"CTGOV:{target.nct_id}"]
    if eligibility.score >= 55:
        recommendations.append(
            ProtocolRecommendation(
                priority="high",
                category="eligibility",
                recommendation=(
                    "Review exclusions and laboratory thresholds line by line; "
                    "remove requirements that do not protect safety or interpretability."
                ),
                expected_benefit="Broader eligible pool and fewer screen failures.",
                tradeoff="May increase population heterogeneity and monitoring needs.",
                evidence_ids=evidence,
            )
        )
    if target.biomarker:
        recommendations.append(
            ProtocolRecommendation(
                priority="high",
                category="biomarker operations",
                recommendation=(
                    "Define accepted assays, tissue alternatives, retesting rules, "
                    "and central-lab turnaround targets for the biomarker gate."
                ),
                expected_benefit="Reduces avoidable biomarker-screening attrition.",
                tradeoff="Broader assay acceptance can increase analytic variability.",
                evidence_ids=evidence,
            )
        )
    if competition.score >= 55:
        recommendations.append(
            ProtocolRecommendation(
                priority="high",
                category="site strategy",
                recommendation=(
                    "Avoid concentrating activation in the highest-density competing "
                    "states; sequence outreach toward high-opportunity states."
                ),
                expected_benefit="Reduces direct competition for the same investigators.",
                tradeoff="Newer site networks may require more startup support.",
                evidence_ids=evidence,
            )
        )
    if endpoints.score < 40:
        recommendations.append(
            ProtocolRecommendation(
                priority="medium",
                category="endpoint",
                recommendation=(
                    f"Reconfirm whether {endpoints.target_family} is operationally "
                    "appropriate and align assessment timing with comparable studies."
                ),
                expected_benefit="Improves interpretability against public precedents.",
                tradeoff="Changing endpoints may alter sample-size and follow-up needs.",
                evidence_ids=evidence,
            )
        )
    state_geography = [item for item in geography if item.level == "state"]
    if state_geography:
        recommendations.append(
            ProtocolRecommendation(
                priority="medium",
                category="geography",
                recommendation=(
                    "Validate candidate facilities in "
                    + ", ".join(item.region for item in state_geography[:3])
                    + " using current capacity and startup intelligence before selection."
                ),
                expected_benefit="Focuses manual feasibility on data-supported candidates.",
                tradeoff="Registry history is not proof of current site performance.",
                evidence_ids=evidence,
            )
        )
    return recommendations


def _similarity(
    target: TrialDraft, candidate: TrialDraft
) -> tuple[float, list[str], list[str]]:
    matches: list[str] = []
    mismatches: list[str] = []
    indication = _jaccard(
        _tokens(" ".join(target.conditions)),
        _tokens(" ".join(candidate.conditions)),
    )
    eligibility = _jaccard(
        _tokens(target.eligibility_criteria),
        _tokens(candidate.eligibility_criteria),
    )
    intervention = _jaccard(
        _tokens(" ".join(item.name for item in target.interventions)),
        _tokens(" ".join(item.name for item in candidate.interventions)),
    )
    molecule_class = bool(
        target.molecule_class
        and candidate.molecule_class
        and target.molecule_class.casefold() == candidate.molecule_class.casefold()
    )
    phase = bool(set(target.phases) & set(candidate.phases))
    biomarker = bool(
        target.biomarker
        and candidate.biomarker
        and set(_tokens(target.biomarker)) & set(_tokens(candidate.biomarker))
    )
    design = target.study_design.intervention_model == candidate.study_design.intervention_model
    endpoint = (
        _endpoint_family(target.primary_endpoints[0].measure)
        == _endpoint_family(candidate.primary_endpoints[0].measure)
    )
    geography = any(site.country == "United States" for site in candidate.sites)
    features = [
        ("indication", indication >= 0.3),
        ("biomarker", biomarker),
        ("molecule class", molecule_class),
        ("intervention", intervention >= 0.2),
        ("phase", phase),
        ("design", design),
        ("endpoint", endpoint),
        ("US geography", geography),
        ("eligibility language", eligibility >= 0.15),
    ]
    for name, matched in features:
        (matches if matched else mismatches).append(name)
    score = (
        25 * indication
        + 15 * float(biomarker)
        + 8 * float(molecule_class)
        + 7 * intervention
        + 10 * float(phase)
        + 10 * float(design)
        + 10 * float(endpoint)
        + 5 * float(geography)
        + 10 * eligibility
    )
    return score, matches, mismatches


def _tokens(value: str) -> set[str]:
    stop = {
        "and",
        "the",
        "with",
        "for",
        "from",
        "that",
        "this",
        "patients",
        "study",
        "trial",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in stop
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0


def _split_eligibility(text: str) -> tuple[str, str]:
    parts = re.split(r"exclusion criteria:?", text, maxsplit=1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def _criterion_count(text: str) -> int:
    return max(
        len([line for line in text.splitlines() if line.strip(" -*\t")]),
        len([part for part in re.split(r"[.;]\s+", text) if len(part.strip()) > 8]),
    )


def _endpoint_family(value: str) -> str:
    normalized = value.lower()
    for family, terms in ENDPOINT_FAMILIES.items():
        if any(term.lower() in normalized for term in terms):
            return family
    return "other"


def _percentile(values: list[float], percentile: int) -> float:
    index = (len(values) - 1) * percentile / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def _band(score: float) -> RiskBand:
    if score < 35:
        return RiskBand.LOW
    if score < 65:
        return RiskBand.MODERATE
    return RiskBand.HIGH


def risk_band(score: float) -> RiskBand:
    return _band(score)


def _rounded(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None
