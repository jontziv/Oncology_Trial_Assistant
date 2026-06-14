import csv
import json
import re
from datetime import date
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://statecancerprofiles.cancer.gov/incidencerates/index.php"
OUTPUT = (
    Path(__file__).parents[1] / "data" / "reference" / "uscs_state_incidence.json"
)
SITES = {
    "071": ("Bladder", ["bladder cancer", "urothelial carcinoma"]),
    "076": ("Brain & ONS", ["brain cancer", "glioblastoma", "glioma"]),
    "055": ("Breast (Female)", ["breast cancer", "breast carcinoma"]),
    "057": ("Cervix", ["cervical cancer", "cervix cancer"]),
    "020": (
        "Colon & Rectum",
        ["colorectal cancer", "colon cancer", "rectal cancer"],
    ),
    "017": ("Esophagus", ["esophageal cancer", "oesophageal cancer"]),
    "072": (
        "Kidney & Renal Pelvis",
        ["kidney cancer", "renal cell carcinoma", "renal cancer"],
    ),
    "090": ("Leukemia", ["leukemia", "leukaemia"]),
    "035": (
        "Liver & Bile Duct",
        ["liver cancer", "hepatocellular carcinoma", "cholangiocarcinoma"],
    ),
    "047": (
        "Lung & Bronchus",
        [
            "lung cancer",
            "non-small cell lung cancer",
            "small cell lung cancer",
            "nsclc",
            "sclc",
        ],
    ),
    "053": ("Melanoma of the Skin", ["melanoma"]),
    "086": (
        "Non-Hodgkin Lymphoma",
        ["non-hodgkin lymphoma", "diffuse large b-cell lymphoma", "follicular lymphoma"],
    ),
    "003": (
        "Oral Cavity & Pharynx",
        ["head and neck cancer", "oral cancer", "oropharyngeal cancer", "hnscc"],
    ),
    "061": ("Ovary", ["ovarian cancer", "ovarian carcinoma"]),
    "040": ("Pancreas", ["pancreatic cancer", "pancreatic adenocarcinoma"]),
    "066": ("Prostate", ["prostate cancer", "prostate carcinoma"]),
    "018": ("Stomach", ["gastric cancer", "stomach cancer"]),
    "080": ("Thyroid", ["thyroid cancer", "thyroid carcinoma"]),
    "058": (
        "Uterus",
        ["endometrial cancer", "uterine cancer", "uterus cancer"],
    ),
}
SEX_BY_SITE = {
    "055": "2",
    "057": "2",
    "061": "2",
    "066": "1",
    "058": "2",
}


def main() -> None:
    datasets = []
    for code, (name, aliases) in SITES.items():
        source_url = _source_url(code)
        rates, period = _download(source_url)
        if len(rates) < 50:
            raise RuntimeError(f"Expected at least 50 state rows for {name}")
        datasets.append(
            {
                "dataset": "NCI/CDC State Cancer Profiles (NPCR + SEER)",
                "release_date": "2024 submission",
                "geography": "United States states and District of Columbia",
                "cancer_site": name,
                "aliases": aliases,
                "source_url": source_url,
                "rates_per_100k": rates,
                "limitation": (
                    f"{period} age-adjusted incidence per 100,000 is disease-burden "
                    "context, not a prevalence, referral, or trial-eligible-patient estimate."
                ),
            }
        )
    payload = {
        "retrieved_at": date.today().isoformat(),
        "datasets": datasets,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _source_url(code: str) -> str:
    query = urlencode(
        {
            "statefips": "00",
            "areatype": "state",
            "cancer": code,
            "race": "00",
            "sex": SEX_BY_SITE.get(code, "0"),
            "age": "001",
            "stage": "999",
            "ruralurban": "0",
            "year": "0",
            "type": "incd",
            "sortVariableName": "rate",
            "sortOrder": "desc",
            "output": "1",
        }
    )
    return f"{BASE_URL}?{query}"


def _download(url: str) -> tuple[dict[str, float], str]:
    request = Request(
        url,
        headers={"User-Agent": "OncologyTrialFeasibilityCopilot/0.1"},
    )
    with urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8-sig")
    lines = content.splitlines()
    title = next(
        (line.strip('"') for line in lines if "(All Stages" in line),
        "Latest five-year incidence",
    )
    period_match = re.search(r"\b(20\d{2}-20\d{2})\b", title)
    period = period_match.group(1) if period_match else "Latest five-year"
    header_index = next(
        index for index, line in enumerate(lines) if line.startswith("State,FIPS,")
    )
    rates: dict[str, float] = {}
    for row in csv.reader(StringIO("\n".join(lines[header_index:]))):
        if not row or len(row) < 3:
            if rates:
                break
            continue
        state = re.sub(r"\(\d+\)$", "", row[0]).strip()
        if state.startswith("US ") or state == "Puerto Rico":
            continue
        try:
            rates[state] = float(row[2].strip())
        except ValueError:
            continue
    return rates, period


if __name__ == "__main__":
    main()
