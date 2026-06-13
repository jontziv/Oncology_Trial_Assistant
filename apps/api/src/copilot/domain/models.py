from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    COMPLETE = "complete"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class RiskBand(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SourceReference(BaseModel):
    provider: str
    record_id: str
    url: str
    retrieved_at: datetime
    source_version: str | None = None
    field_locators: dict[str, str] = Field(default_factory=dict)


class Intervention(BaseModel):
    name: str
    intervention_type: str
    description: str | None = None


class Endpoint(BaseModel):
    measure: str
    time_frame: str | None = None
    description: str | None = None


class Site(BaseModel):
    facility: str | None = None
    city: str | None = None
    state: str | None = None
    country: str
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class StudyDesign(BaseModel):
    study_type: str
    allocation: str | None = None
    intervention_model: str | None = None
    primary_purpose: str | None = None
    masking: str | None = None
    arm_count: int = 0


class TrialDraft(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nct_id: str = Field(pattern=r"^(NCT\d{8}|MANUAL\d{6})$")
    title: str = Field(min_length=3, max_length=600)
    overall_status: str
    indication: str = Field(min_length=2)
    conditions: list[str] = Field(min_length=1)
    phases: list[str] = Field(min_length=1)
    interventions: list[Intervention] = Field(min_length=1)
    molecule_class: str | None = None
    biomarker: str | None = None
    target_geographies: list[str] = Field(
        default_factory=lambda: ["United States"]
    )
    summary: str | None = None
    eligibility_criteria: str = Field(min_length=3)
    minimum_age: str | None = None
    maximum_age: str | None = None
    sex: str | None = None
    healthy_volunteers: bool | None = None
    study_design: StudyDesign
    primary_endpoints: list[Endpoint] = Field(min_length=1)
    secondary_endpoints: list[Endpoint] = Field(default_factory=list)
    enrollment: int = Field(ge=1)
    enrollment_type: str | None = None
    start_date: date | None = None
    start_date_type: str | None = None
    primary_completion_date: date | None = None
    primary_completion_date_type: str | None = None
    sites: list[Site] = Field(default_factory=list)
    source: SourceReference

    @field_validator("nct_id")
    @classmethod
    def normalize_nct_id(cls, value: str) -> str:
        return value.upper()


class TrialSearchResult(BaseModel):
    nct_id: str
    title: str
    overall_status: str
    phases: list[str]
    conditions: list[str]
    interventions: list[str]
    enrollment: int | None = None
    us_site_count: int = 0


class TrialSearchResponse(BaseModel):
    items: list[TrialSearchResult]
    next_page_token: str | None = None
    total_count: int | None = None


class ScoreComponent(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    weighted_contribution: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    inputs: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class SimilarTrial(BaseModel):
    nct_id: str
    title: str
    similarity_score: float = Field(ge=0, le=100)
    overall_status: str
    phases: list[str]
    enrollment: int
    start_date: date | None = None
    primary_completion_date: date | None = None
    us_site_count: int = 0
    matched_features: list[str] = Field(default_factory=list)
    mismatched_features: list[str] = Field(default_factory=list)
    source: SourceReference


class TimelineBenchmark(BaseModel):
    label: str = "Start-to-primary-completion timeline proxy"
    median_months: float | None = None
    q1_months: float | None = None
    q3_months: float | None = None
    cohort_size: int = 0
    excluded_count: int = 0
    target_months: float | None = None
    percentile: float | None = None
    confidence: float = Field(ge=0, le=1)
    limitation: str


class EligibilityFactor(BaseModel):
    label: str
    points: float
    evidence: str


class EligibilityBurden(BaseModel):
    score: float = Field(ge=0, le=100)
    band: RiskBand
    criterion_count: int
    inclusion_count: int
    exclusion_count: int
    factors: list[EligibilityFactor]
    confidence: float = Field(ge=0, le=1)
    methodology: str


class CompetitionRegion(BaseModel):
    region: str
    active_trial_count: int
    active_site_count: int
    weighted_density: float
    target_site_count: int = 0


class CompetitionAnalysis(BaseModel):
    score: float = Field(ge=0, le=100)
    active_trial_count: int
    active_us_site_count: int
    regions: list[CompetitionRegion]
    confidence: float = Field(ge=0, le=1)
    limitation: str


class GeographyRecommendation(BaseModel):
    region: str
    level: str
    opportunity_score: float = Field(ge=0, le=100)
    historical_trial_count: int
    active_competing_sites: int
    candidate_facilities: list[str]
    disease_burden_rate: float | None = None
    rationale: str
    confidence: float = Field(ge=0, le=1)


class EndpointComparability(BaseModel):
    score: float = Field(ge=0, le=100)
    target_family: str
    cohort_distribution: dict[str, int]
    comparable_count: int
    cohort_size: int
    rationale: str
    confidence: float = Field(ge=0, le=1)


class ProtocolRecommendation(BaseModel):
    priority: str
    category: str
    recommendation: str
    expected_benefit: str
    tradeoff: str
    evidence_ids: list[str]


class PublicationEvidence(BaseModel):
    pmid: str
    title: str
    journal: str | None = None
    publication_date: str | None = None
    authors: list[str] = Field(default_factory=list)
    url: str
    source_id: str


class EvidenceSource(BaseModel):
    source_id: str
    source_type: str
    title: str
    url: str
    record_id: str
    retrieved_at: datetime
    locator: str | None = None


class FeasibilityMemo(BaseModel):
    generated_by: str
    executive_summary: str
    key_risks: list[str]
    recommendations: list[str]
    limitations: list[str]
    citation_ids: list[str]


class FeasibilityResult(BaseModel):
    methodology_version: str
    overall_score: float = Field(ge=0, le=100)
    risk_band: RiskBand
    confidence: float = Field(ge=0, le=1)
    confidence_label: str
    components: list[ScoreComponent]
    similar_trials: list[SimilarTrial]
    timeline: TimelineBenchmark
    eligibility: EligibilityBurden
    competition: CompetitionAnalysis
    geography: list[GeographyRecommendation]
    endpoints: EndpointComparability
    recommendations: list[ProtocolRecommendation]
    publications: list[PublicationEvidence]
    memo: FeasibilityMemo
    sources: list[EvidenceSource]
    warnings: list[str] = Field(default_factory=list)
    sensitivity_low: float = Field(ge=0, le=100)
    sensitivity_high: float = Field(ge=0, le=100)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalysisRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    analysis_id: UUID
    owner_id: UUID
    status: RunStatus = RunStatus.RUNNING
    methodology_version: str = "oncology-feasibility-v0.2"
    result: FeasibilityResult | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class Analysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    title: str = Field(min_length=3, max_length=200)
    status: AnalysisStatus = AnalysisStatus.DRAFT
    trial: TrialDraft
    latest_run: AnalysisRun | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreateAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    trial: TrialDraft


class UpdateAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    trial: TrialDraft | None = None


class RunAnalysisRequest(BaseModel):
    force_refresh: bool = False
