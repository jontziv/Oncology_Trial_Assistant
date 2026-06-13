from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"


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

    nct_id: str = Field(pattern=r"^NCT\d{8}$")
    title: str = Field(min_length=3, max_length=600)
    overall_status: str
    indication: str = Field(min_length=2)
    conditions: list[str] = Field(min_length=1)
    phases: list[str] = Field(min_length=1)
    interventions: list[Intervention] = Field(min_length=1)
    biomarker: str | None = None
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
    primary_completion_date: date | None = None
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


class Analysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    title: str = Field(min_length=3, max_length=200)
    status: AnalysisStatus = AnalysisStatus.DRAFT
    trial: TrialDraft
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreateAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    trial: TrialDraft


class UpdateAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    trial: TrialDraft | None = None

