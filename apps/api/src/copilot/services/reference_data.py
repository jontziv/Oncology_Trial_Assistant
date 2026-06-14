from pathlib import Path
import re

from pydantic import BaseModel, Field


class DiseaseBurdenCatalog(BaseModel):
    datasets: list["DiseaseBurdenDataset"]


class DiseaseBurdenDataset(BaseModel):
    dataset: str
    release_date: str
    geography: str
    cancer_site: str
    aliases: list[str] = Field(default_factory=list)
    source_url: str
    rates_per_100k: dict[str, float]
    limitation: str


def load_disease_burden(indication: str) -> DiseaseBurdenDataset:
    path = (
        Path(__file__).parents[3]
        / "data"
        / "reference"
        / "uscs_state_incidence.json"
    )
    catalog = DiseaseBurdenCatalog.model_validate_json(path.read_text())
    normalized = _normalize_indication(indication)
    indication_tokens = set(normalized.split())
    matches = [
        dataset
        for dataset in catalog.datasets
        if any(_alias_matches(alias, normalized, indication_tokens) for alias in dataset.aliases)
    ]
    if matches:
        return max(matches, key=lambda dataset: max(map(len, dataset.aliases)))
    return DiseaseBurdenDataset(
        dataset="NCI/CDC State Cancer Profiles (NPCR + SEER)",
        release_date="2024 submission",
        geography="United States states and District of Columbia",
        cancer_site="No indication-specific match",
        source_url="https://statecancerprofiles.cancer.gov/incidencerates/",
        rates_per_100k={},
        limitation=(
            f"No indication-specific State Cancer Profiles dataset is bundled for "
            f"{indication!r}; disease burden was omitted from geography scoring."
        ),
    )


def _normalize_indication(value: str) -> str:
    normalized = value.casefold().replace("-", " ")
    normalized = re.sub(r"\bcarcinoma\b", "cancer", normalized)
    normalized = re.sub(r"\bneoplasm\b", "cancer", normalized)
    normalized = re.sub(r"\bmalignancy\b", "cancer", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return " ".join(normalized.split())


def _alias_matches(alias: str, normalized_indication: str, indication_tokens: set[str]) -> bool:
    normalized_alias = _normalize_indication(alias)
    if not normalized_alias:
        return False
    if normalized_alias in normalized_indication:
        return True
    alias_tokens = set(normalized_alias.split())
    # Accept reordered terminology when all alias terms are present,
    # e.g. "Lung Non-Small Cell Carcinoma" vs "non-small cell lung cancer".
    return bool(alias_tokens) and alias_tokens.issubset(indication_tokens)
