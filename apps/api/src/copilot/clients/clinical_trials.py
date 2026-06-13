import asyncio
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import quote

import httpx

from copilot.domain.models import (
    Endpoint,
    Intervention,
    Site,
    SourceReference,
    StudyDesign,
    TrialDraft,
    TrialSearchResponse,
    TrialSearchResult,
)


class UpstreamUnavailableError(RuntimeError):
    """Raised when an upstream cannot provide a usable response."""


class TrialNotFoundError(RuntimeError):
    """Raised when an NCT identifier does not exist."""


class ClinicalTrialsClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        max_attempts: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_attempts = max_attempts
        self._client = client

    async def get_study(self, nct_id: str) -> TrialDraft:
        normalized_id = nct_id.strip().upper()
        response = await self._request(f"/studies/{quote(normalized_id)}")
        if response.status_code == httpx.codes.NOT_FOUND:
            raise TrialNotFoundError(normalized_id)
        self._raise_for_upstream(response)
        return map_study(response.json(), retrieved_at=datetime.now(UTC))

    async def search(
        self,
        query: str,
        *,
        page_token: str | None = None,
        limit: int = 10,
    ) -> TrialSearchResponse:
        params: dict[str, str | int] = {
            "query.term": query,
            "pageSize": min(max(limit, 1), 25),
            "countTotal": "true",
            "format": "json",
        }
        if page_token:
            params["pageToken"] = page_token
        response = await self._request("/studies", params=params)
        self._raise_for_upstream(response)
        payload = response.json()
        return TrialSearchResponse(
            items=[map_search_result(study) for study in payload.get("studies", [])],
            next_page_token=payload.get("nextPageToken"),
            total_count=payload.get("totalCount"),
        )

    async def search_studies(
        self,
        query: str,
        *,
        limit: int = 40,
    ) -> list[TrialDraft]:
        response = await self._request(
            "/studies",
            params={
                "query.term": query,
                "pageSize": min(max(limit, 1), 100),
                "format": "json",
            },
        )
        self._raise_for_upstream(response)
        retrieved_at = datetime.now(UTC)
        studies: list[TrialDraft] = []
        for payload in response.json().get("studies", []):
            try:
                studies.append(map_study(payload, retrieved_at=retrieved_at))
            except (UpstreamUnavailableError, ValueError):
                continue
        return studies

    async def _request(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> httpx.Response:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            for attempt in range(self._max_attempts):
                try:
                    response = await client.get(f"{self._base_url}{path}", params=params)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt + 1 == self._max_attempts:
                        raise UpstreamUnavailableError("ClinicalTrials.gov unavailable") from exc
                    await asyncio.sleep(0.25 * (2**attempt))
                    continue
                if response.status_code not in {429, 500, 502, 503, 504}:
                    return response
                if attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                    await asyncio.sleep(min(delay, 2.0))
            raise UpstreamUnavailableError("ClinicalTrials.gov unavailable")
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _raise_for_upstream(response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise UpstreamUnavailableError(
                f"ClinicalTrials.gov returned HTTP {response.status_code}"
            )


def map_study(payload: dict[str, Any], *, retrieved_at: datetime) -> TrialDraft:
    protocol = payload.get("protocolSection", {})
    identity = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    design_module = protocol.get("designModule", {})
    arms_module = protocol.get("armsInterventionsModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    outcomes = protocol.get("outcomesModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    description = protocol.get("descriptionModule", {})

    nct_id = _required_text(identity, "nctId")
    conditions = _string_list(conditions_module.get("conditions"))
    phases = _string_list(design_module.get("phases")) or ["NOT_APPLICABLE"]
    interventions = [
        Intervention(
            name=item.get("name") or "Unnamed intervention",
            intervention_type=item.get("type") or "OTHER",
            description=item.get("description"),
        )
        for item in arms_module.get("interventions", [])
    ]
    if not interventions:
        interventions = [
            Intervention(name="Not reported", intervention_type="NOT_REPORTED")
        ]

    enrollment_info = design_module.get("enrollmentInfo") or {}
    enrollment = enrollment_info.get("count")
    if not isinstance(enrollment, int) or enrollment < 1:
        enrollment = 1

    design_info = design_module.get("designInfo") or {}
    masking_info = design_info.get("maskingInfo") or {}
    locations = [
        Site(
            facility=item.get("facility"),
            city=item.get("city"),
            state=item.get("state"),
            country=item.get("country") or "Not reported",
            status=item.get("status"),
            latitude=(item.get("geoPoint") or {}).get("lat"),
            longitude=(item.get("geoPoint") or {}).get("lon"),
        )
        for item in contacts.get("locations", [])
    ]

    primary_endpoints = _map_endpoints(outcomes.get("primaryOutcomes", []))
    if not primary_endpoints:
        primary_endpoints = [Endpoint(measure="Not reported")]

    source_version = (
        payload.get("derivedSection", {})
        .get("miscInfoModule", {})
        .get("versionHolder")
    )
    return TrialDraft(
        nct_id=nct_id,
        title=identity.get("officialTitle") or identity.get("briefTitle") or nct_id,
        overall_status=status.get("overallStatus") or "UNKNOWN",
        indication=conditions[0] if conditions else "Not reported",
        conditions=conditions or ["Not reported"],
        phases=phases,
        interventions=interventions,
        molecule_class=_infer_molecule_class(interventions),
        biomarker=_infer_biomarker(conditions, eligibility.get("eligibilityCriteria")),
        target_geographies=sorted(
            {
                location.country
                for location in locations
                if location.country != "Not reported"
            }
        )
        or ["United States"],
        summary=description.get("briefSummary"),
        eligibility_criteria=eligibility.get("eligibilityCriteria") or "Not reported",
        minimum_age=eligibility.get("minimumAge"),
        maximum_age=eligibility.get("maximumAge"),
        sex=eligibility.get("sex"),
        healthy_volunteers=eligibility.get("healthyVolunteers"),
        study_design=StudyDesign(
            study_type=design_module.get("studyType") or "UNKNOWN",
            allocation=design_info.get("allocation"),
            intervention_model=design_info.get("interventionModel"),
            primary_purpose=design_info.get("primaryPurpose"),
            masking=masking_info.get("masking"),
            arm_count=len(arms_module.get("armGroups", [])),
        ),
        primary_endpoints=primary_endpoints,
        secondary_endpoints=_map_endpoints(outcomes.get("secondaryOutcomes", [])),
        enrollment=enrollment,
        enrollment_type=enrollment_info.get("type"),
        start_date=_parse_partial_date((status.get("startDateStruct") or {}).get("date")),
        start_date_type=(status.get("startDateStruct") or {}).get("type"),
        primary_completion_date=_parse_partial_date(
            (status.get("primaryCompletionDateStruct") or {}).get("date")
        ),
        primary_completion_date_type=(
            status.get("primaryCompletionDateStruct") or {}
        ).get("type"),
        sites=locations,
        source=SourceReference(
            provider="ClinicalTrials.gov",
            record_id=nct_id,
            url=f"https://clinicaltrials.gov/study/{nct_id}",
            retrieved_at=retrieved_at,
            source_version=source_version,
            field_locators={
                "title": "protocolSection.identificationModule",
                "design": "protocolSection.designModule",
                "eligibility": "protocolSection.eligibilityModule",
                "endpoints": "protocolSection.outcomesModule",
                "sites": "protocolSection.contactsLocationsModule.locations",
            },
        ),
    )


def map_search_result(payload: dict[str, Any]) -> TrialSearchResult:
    protocol = payload.get("protocolSection", {})
    identity = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    conditions = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    locations = contacts.get("locations", [])
    return TrialSearchResult(
        nct_id=identity.get("nctId") or "UNKNOWN",
        title=identity.get("briefTitle") or identity.get("officialTitle") or "Untitled",
        overall_status=status.get("overallStatus") or "UNKNOWN",
        phases=_string_list(design.get("phases")),
        conditions=_string_list(conditions.get("conditions")),
        interventions=[
            item.get("name") or "Unnamed"
            for item in arms.get("interventions", [])
        ],
        enrollment=(design.get("enrollmentInfo") or {}).get("count"),
        us_site_count=sum(
            1 for location in locations if location.get("country") == "United States"
        ),
    )


def _map_endpoints(items: list[dict[str, Any]]) -> list[Endpoint]:
    return [
        Endpoint(
            measure=item.get("measure") or "Not reported",
            time_frame=item.get("timeFrame"),
            description=item.get("description"),
        )
        for item in items
    ]


def _parse_partial_date(value: str | None) -> date | None:
    if not value:
        return None
    parts = value.split("-")
    try:
        if len(parts) == 1:
            return date(int(parts[0]), 1, 1)
        if len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1)
        return date.fromisoformat(value)
    except ValueError:
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise UpstreamUnavailableError(f"ClinicalTrials.gov response missing {key}")
    return value


def _infer_biomarker(conditions: list[str], eligibility_text: str | None) -> str | None:
    haystack = " ".join([*conditions, eligibility_text or ""]).upper()
    known = ["EGFR", "ALK", "ROS1", "KRAS", "BRAF", "MET", "RET", "NTRK", "PD-L1"]
    matches = [
        marker
        for marker in known
        if re.search(rf"(?<![A-Z0-9]){re.escape(marker)}(?![A-Z0-9])", haystack)
    ]
    return ", ".join(matches) if matches else None


def _infer_molecule_class(interventions: list[Intervention]) -> str | None:
    text = " ".join(
        f"{item.name} {item.intervention_type} {item.description or ''}"
        for item in interventions
    ).lower()
    patterns = [
        ("Cell therapy", r"\b(car[- ]?t|tcr|cell therapy|cellular therapy)\b"),
        ("Checkpoint inhibitor", r"\b(pd-?1|pd-?l1|ctla-?4|checkpoint)\b"),
        (
            "Tyrosine kinase inhibitor",
            r"\b(tyrosine kinase inhibitor|\btki\b|inib\b)",
        ),
        (
            "Antibody-drug conjugate",
            r"\b(antibody[- ]drug conjugate|\badc\b|deruxtecan)\b",
        ),
        ("Monoclonal antibody", r"\b(monoclonal antibody|mab\b)"),
        ("Cancer vaccine", r"\b(vaccine|immunization)\b"),
        ("Chemotherapy", r"\b(chemotherapy|platinum|taxane|pemetrexed)\b"),
        ("Radiotherapy", r"\b(radiation|radiotherapy)\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    types = {
        item.intervention_type.replace("_", " ").title()
        for item in interventions
        if item.intervention_type not in {"OTHER", "NOT_REPORTED"}
    }
    return ", ".join(sorted(types)) or None
