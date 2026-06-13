from pathlib import Path

from pydantic import BaseModel


class DiseaseBurdenDataset(BaseModel):
    dataset: str
    release_date: str
    geography: str
    cancer_site: str
    source_url: str
    rates_per_100k: dict[str, float]
    limitation: str


def load_disease_burden() -> DiseaseBurdenDataset:
    path = (
        Path(__file__).parents[3]
        / "data"
        / "reference"
        / "uscs_lung_incidence.json"
    )
    return DiseaseBurdenDataset.model_validate_json(path.read_text())
