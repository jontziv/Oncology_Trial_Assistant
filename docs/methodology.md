# Illustrative Feasibility Methodology v0.3

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

## Enrollment Duration

The benchmark uses only records with actual study-start and actual
primary-completion dates between 30 days and 10 years. It reports median and
interquartile range. When actual enrollment is also available, enrollment
divided by that interval produces a participants-per-month proxy and a
target-enrollment projection. The interval includes treatment and follow-up,
so this is a conservative planning benchmark, not observed recruitment
duration.

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

US state opportunity also uses indication-matched, age-adjusted 2018–2022
incidence rates from NCI/CDC State Cancer Profiles. The bundled importer
retrieves NPCR and SEER tables for 19 cancer sites. Incidence is context only;
it is not prevalence, referral volume, or a trial-eligible-patient estimate.
Unknown indications omit this factor rather than borrowing another cancer
site's rate.

## Endpoints

Primary endpoints are normalized into common oncology families. For trials
with posted ClinicalTrials.gov results, the posted primary result outcome is
preferred; otherwise the registered primary outcome is used.

## Overall Risk

- eligibility 25%
- active competition 25%
- enrollment-duration benchmark 20%
- geographic opportunity inverse 20%
- endpoint mismatch 10%

Bands are low below 35, moderate from 35 through 64.9, and high from 65.
One-factor weight perturbation of plus or minus 20% produces the displayed
sensitivity interval.

## Memo

The deterministic memo is always available. Groq generation is enabled only
when `GROQ_MODEL` names an account-verified production Llama model. Its
evidence packet includes computed metrics, comparable trials, geography,
publications, recommendations, and source metadata. Generated JSON is
schema-validated; unknown citations and unsupported numbers cause fallback to
the deterministic memo.
