# Illustrative Feasibility Methodology v0.2

This methodology is decision support, not a trained or validated enrollment
prediction.

## Comparable Trials

ClinicalTrials.gov candidates are retrieved broadly by indication, then ranked
with weighted structured and lexical features:

- indication/stage 25%
- biomarker 15%
- exact molecule class 8%
- intervention-name overlap 7%
- phase 10%
- design 10%
- endpoint family 10%
- US geography 5%
- eligibility language 10%

The dashboard displays matched and mismatched features for each selected study.

## Timeline

The benchmark uses only records with actual study-start and actual
primary-completion dates between 30 days and 10 years. It reports median and
interquartile range. This interval includes treatment and follow-up and is
therefore labeled a timeline proxy, never recruitment duration.

## Eligibility

The 0-100 burden index combines parsed criterion volume with explicit biomarker,
prior-treatment, laboratory, CNS, performance-status, washout, and procedural
constraints. It estimates protocol complexity, not the number of eligible
patients.

## Competition And Geography

Competition counts active comparable registered trials and sites, with status
weights. US state opportunity combines historical comparable-trial footprint
and inverse active competition. Country opportunity uses the same public site
signals without a disease-burden adjustment.

USCS is a versioned reference-data boundary. State incidence rates remain
empty until an approved SEER\*Stat export is imported; confidence is reduced in
the meantime.

## Overall Risk

- eligibility 25%
- active competition 25%
- timeline proxy 20%
- geographic opportunity inverse 20%
- endpoint mismatch 10%

Bands are low below 35, moderate from 35 through 64.9, and high from 65.
One-factor weight perturbation of plus or minus 20% produces the displayed
sensitivity interval.

## Memo

The deterministic memo is always available. Groq generation is enabled only
when `GROQ_MODEL` names an account-verified production Llama model. Generated
JSON is schema-validated; unknown citations and unsupported numbers cause
fallback to the deterministic memo.
