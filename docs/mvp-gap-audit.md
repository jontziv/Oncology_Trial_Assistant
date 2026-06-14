# MVP Gap Audit

## Initial State

The repository implemented intake and persistence only: trial import, editable
fields, authentication boundaries, provenance, and draft CRUD. It had no
analysis run, result contract, scoring, comparators, literature, geography,
recommendations, or memo.

## Current Coverage

| Product capability                         | Status                                                  |
| ------------------------------------------ | ------------------------------------------------------- |
| Pasted protocol parser and editable review | Implemented                                             |
| Structured manual protocol entry           | Implemented                                             |
| Similar-trial cohort and explanation       | Implemented                                             |
| Enrollment-duration benchmark              | Implemented as enrollment-adjusted study-timeline proxy |
| Competing-trial heatmap                    | Implemented from active registered sites                |
| Eligibility burden                         | Implemented                                             |
| State/country and candidate-site ranking   | Implemented with indication-matched incidence context   |
| Endpoint comparability                     | Implemented, including posted result outcomes           |
| Overall enrollment-risk heuristic          | Implemented                                             |
| Protocol-change recommendations            | Implemented                                             |
| PubMed evidence                            | Implemented                                             |
| Citation-linked memo                       | Deterministic fallback implemented; Groq optional       |
| USCS/SEER disease burden                   | 19 official State Cancer Profiles datasets bundled      |

## Remaining Validation Inputs

The software MVP is implemented. Production-grade predictive validation still
requires inputs that public registries do not provide:

1. Observed screening, randomization, activation, and accrual data to calibrate
   and validate enrollment predictions.
2. Current site capacity, startup timelines, referral networks, and investigator
   performance data for operational site selection.
3. A Groq API key plus an account-verified production Llama model ID for the
   optional generated memo.

The application labels its public-data scores as illustrative and does not
silently represent registry proxies as validated forecasts.
