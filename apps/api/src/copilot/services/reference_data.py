from pathlib import Path

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
    normalized = indication.casefold()
    matches = [
        dataset
        for dataset in catalog.datasets
        if any(alias.casefold() in normalized for alias in dataset.aliases)
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
