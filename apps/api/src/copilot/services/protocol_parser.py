import hashlib
import re
from datetime import UTC, datetime

from copilot.domain.models import (
    Endpoint,
    Intervention,
    ProtocolParseResult,
    SourceReference,
    StudyDesign,
    TrialDraft,
)

PARSER_VERSION = "protocol-parser-v1"

INDICATION_ALIASES = {
    "non-small cell lung cancer": ("non-small cell lung cancer", "nsclc"),
    "small cell lung cancer": ("small cell lung cancer", "sclc"),
    "breast cancer": ("breast cancer", "breast carcinoma"),
    "colorectal cancer": ("colorectal cancer", "colon cancer", "rectal cancer"),
    "prostate cancer": ("prostate cancer", "prostate carcinoma"),
    "pancreatic cancer": ("pancreatic cancer", "pancreatic adenocarcinoma"),
    "melanoma": ("melanoma",),
    "renal cell carcinoma": ("renal cell carcinoma", "kidney cancer", "rcc"),
    "hepatocellular carcinoma": ("hepatocellular carcinoma", "liver cancer", "hcc"),
    "ovarian cancer": ("ovarian cancer", "ovarian carcinoma"),
    "gastric cancer": ("gastric cancer", "stomach cancer"),
    "esophageal cancer": ("esophageal cancer", "oesophageal cancer"),
    "head and neck cancer": ("head and neck cancer", "hnscc"),
    "glioblastoma": ("glioblastoma", "gbm"),
    "multiple myeloma": ("multiple myeloma",),
    "acute myeloid leukemia": ("acute myeloid leukemia", "aml"),
    "non-hodgkin lymphoma": ("non-hodgkin lymphoma", "nhl"),
}
BIOMARKERS = (
    "HER2",
    "PD-L1",
    "EGFR",
    "ALK",
    "ROS1",
    "KRAS",
    "BRAF",
    "MET",
    "RET",
    "NTRK",
    "BRCA1",
    "BRCA2",
    "MSI-H",
    "dMMR",
    "TMB",
    "HRD",
    "PSMA",
    "CD19",
    "BCMA",
)
MOLECULE_CLASSES = (
    "antibody-drug conjugate",
    "bispecific antibody",
    "monoclonal antibody",
    "checkpoint inhibitor",
    "tyrosine kinase inhibitor",
    "small molecule inhibitor",
    "cell therapy",
    "CAR-T",
    "cancer vaccine",
    "oncolytic virus",
    "radiopharmaceutical",
)
COUNTRIES = (
    "United States",
    "Canada",
    "United Kingdom",
    "France",
    "Germany",
    "Spain",
    "Italy",
    "Greece",
    "Netherlands",
    "Belgium",
    "Switzerland",
    "Poland",
    "Australia",
    "New Zealand",
    "Japan",
    "China",
    "South Korea",
    "Singapore",
    "India",
    "Israel",
    "Brazil",
    "Mexico",
)


def parse_protocol(text: str) -> ProtocolParseResult:
    normalized = text.replace("\r\n", "\n").strip()
    extracted: list[str] = []
    warnings: list[str] = []

    title = _labeled_value(normalized, ("protocol title", "study title", "title"))
    if title:
        extracted.append("title")
    else:
        title = _first_content_line(normalized)
        warnings.append("Study title was inferred from the first line; confirm it.")

    indication = _labeled_value(
        normalized, ("oncology indication", "indication", "condition", "disease")
    )
    if indication:
        extracted.append("indication")
    else:
        indication = _known_indication(normalized)
        if indication:
            extracted.append("indication")
        else:
            indication = "Oncology indication to confirm"
            warnings.append("No oncology indication was recognized.")

    phases = _phases(normalized)
    if phases:
        extracted.append("phases")
    else:
        phases = ["NA"]
        warnings.append("No study phase was recognized.")

    intervention_name = _labeled_value(
        normalized,
        (
            "investigational product",
            "investigational drug",
            "study drug",
            "intervention",
            "treatment",
        ),
    )
    if intervention_name:
        intervention_name = re.split(
            r"\s+(?:dose|administered|versus|vs\.?)\b",
            intervention_name,
            maxsplit=1,
            flags=re.I,
        )[0]
        extracted.append("interventions")
    else:
        intervention_name = "Intervention to confirm"
        warnings.append("No investigational intervention was recognized.")

    molecule_class = _find_terms(normalized, MOLECULE_CLASSES)
    if molecule_class:
        extracted.append("molecule_class")
    biomarkers = _find_terms(normalized, BIOMARKERS)
    if biomarkers:
        extracted.append("biomarker")

    geographies = _find_terms(normalized, COUNTRIES)
    if geographies:
        extracted.append("target_geographies")
    else:
        geographies = ["United States"]
        warnings.append(
            "No target country was recognized; United States was used as a review default."
        )

    inclusion = _section(
        normalized,
        r"(?:key\s+)?inclusion criteria",
        (r"(?:key\s+)?exclusion criteria", r"primary (?:endpoint|outcome|objective)"),
    )
    exclusion = _section(
        normalized,
        r"(?:key\s+)?exclusion criteria",
        (
            r"primary (?:endpoint|outcome|objective)",
            r"secondary (?:endpoint|outcome|objective)",
            r"statistical analysis",
            r"study design",
        ),
    )
    criteria_parts = []
    if inclusion:
        criteria_parts.append(f"Inclusion criteria:\n{inclusion}")
    if exclusion:
        criteria_parts.append(f"Exclusion criteria:\n{exclusion}")
    if criteria_parts:
        eligibility = "\n\n".join(criteria_parts)
        extracted.append("eligibility_criteria")
    else:
        eligibility = (
            "Inclusion criteria:\n- To be confirmed\n\n"
            "Exclusion criteria:\n- To be confirmed"
        )
        warnings.append("Inclusion and exclusion sections were not recognized.")

    endpoint = _labeled_value(
        normalized, ("primary endpoint", "primary outcome", "primary objective")
    )
    if endpoint:
        extracted.append("primary_endpoints")
    else:
        endpoint = "Primary endpoint to confirm"
        warnings.append("No primary endpoint was recognized.")

    enrollment = _enrollment(normalized)
    if enrollment is not None:
        extracted.append("enrollment")
    else:
        enrollment = 100
        warnings.append("No planned enrollment was recognized; 100 was used as a review default.")

    manual_id = _manual_id(normalized)
    randomized = bool(re.search(r"\brandomi[sz]ed\b", normalized, re.I))
    masking = _masking(normalized)
    arm_count = _arm_count(normalized)
    if randomized or masking or arm_count:
        extracted.append("study_design")

    trial = TrialDraft(
        nct_id=manual_id,
        title=title[:600],
        overall_status="NOT_YET_RECRUITING",
        indication=indication,
        conditions=[indication],
        phases=phases,
        interventions=[
            Intervention(
                name=intervention_name[:300],
                intervention_type="DRUG",
            )
        ],
        molecule_class=", ".join(molecule_class) or None,
        biomarker=", ".join(biomarkers) or None,
        target_geographies=geographies,
        summary=_section(
            normalized,
            r"(?:study |protocol )?(?:summary|synopsis)",
            (
                r"(?:study )?objectives?",
                r"(?:study )?design",
                r"(?:key\s+)?inclusion criteria",
            ),
        )
        or None,
        eligibility_criteria=eligibility,
        study_design=StudyDesign(
            study_type="INTERVENTIONAL",
            allocation="RANDOMIZED" if randomized else None,
            intervention_model="PARALLEL" if randomized or arm_count > 1 else None,
            primary_purpose="TREATMENT",
            masking=masking,
            arm_count=arm_count,
        ),
        primary_endpoints=[Endpoint(measure=endpoint[:600])],
        enrollment=enrollment,
        enrollment_type="ESTIMATED",
        source=SourceReference(
            provider="Pasted protocol",
            record_id=manual_id,
            url="urn:oncology-copilot:pasted-protocol",
            retrieved_at=datetime.now(UTC),
            source_version=PARSER_VERSION,
            field_locators={field: "Pasted protocol text" for field in extracted},
        ),
    )
    return ProtocolParseResult(
        trial=trial,
        extracted_fields=sorted(set(extracted)),
        warnings=warnings,
        parser_version=PARSER_VERSION,
    )


def _labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?im)^\s*(?:{label_pattern})\s*[:\-]\s*(.+?)\s*$",
        text,
    )
    return _clean_value(match.group(1)) if match else None


def _first_content_line(text: str) -> str:
    for line in text.splitlines():
        clean = _clean_value(line)
        if len(clean) >= 3 and not re.fullmatch(r"(protocol|synopsis|study)", clean, re.I):
            return clean
    return "Pasted oncology protocol"


def _known_indication(text: str) -> str | None:
    lowered = text.casefold()
    for canonical, aliases in INDICATION_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases):
            return canonical.title()
    return None


def _phases(text: str) -> list[str]:
    values: set[str] = set()
    pattern = re.compile(
        r"\bphase\s*(?:i{1,3}|iv|[1-4])(?:\s*[/\-]\s*(?:i{1,3}|iv|[1-4]))?\b",
        re.I,
    )
    roman = {"I": "1", "II": "2", "III": "3", "IV": "4"}
    for match in pattern.findall(text):
        for part in re.findall(r"i{1,3}|iv|[1-4]", match, re.I):
            number = roman.get(part.upper(), part)
            values.add(f"PHASE{number}")
    return sorted(values)


def _find_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    found = [
        term
        for term in terms
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I)
    ]
    return found


def _section(text: str, heading: str, following_headings: tuple[str, ...]) -> str:
    start = re.search(rf"(?im)^\s*{heading}\s*:?\s*$", text)
    if not start:
        return ""
    remainder = text[start.end() :]
    stops = [
        match.start()
        for next_heading in following_headings
        if (match := re.search(rf"(?im)^\s*{next_heading}\s*:?\s*$", remainder))
    ]
    content = remainder[: min(stops)] if stops else remainder
    return content.strip()[:20_000]


def _enrollment(text: str) -> int | None:
    patterns = (
        r"(?:planned|target|estimated)\s+(?:sample size|enrollment|enrolment)\D{0,12}(\d{1,6})",
        r"(?:sample size|enrollment|enrolment)\s*[:\-]\s*(?:approximately\s*)?(\d{1,6})",
        r"\bN\s*=\s*(\d{1,6})\b",
        r"(?:enroll|enrol)\s+(?:approximately\s*)?(\d{1,6})\s+(?:participants|patients|subjects)",
    )
    for pattern in patterns:
        if match := re.search(pattern, text, re.I):
            value = int(match.group(1))
            if 1 <= value <= 100_000:
                return value
    return None


def _masking(text: str) -> str | None:
    lowered = text.casefold()
    if "double-blind" in lowered or "double blind" in lowered:
        return "DOUBLE"
    if "single-blind" in lowered or "single blind" in lowered:
        return "SINGLE"
    if "open-label" in lowered or "open label" in lowered:
        return "NONE"
    return None


def _arm_count(text: str) -> int:
    if match := re.search(r"\b(\d{1,2})[- ]arm\b", text, re.I):
        return int(match.group(1))
    return 0


def _manual_id(text: str) -> str:
    digest = int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)
    return f"MANUAL{digest % 1_000_000:06d}"


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" \t-*#"))
