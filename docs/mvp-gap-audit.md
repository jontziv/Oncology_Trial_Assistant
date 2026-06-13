# MVP Gap Audit

## Before This Refactor

The repository implemented intake and persistence only: trial import, editable
fields, authentication boundaries, provenance, and draft CRUD. It had no
analysis run, result contract, scoring, comparators, literature, geography,
recommendations, or memo.

## Current Coverage

| Product capability                       | Status                                                    |
| ---------------------------------------- | --------------------------------------------------------- |
| Structured protocol import/parser        | Implemented                                               |
| Similar-trial cohort and explanation     | Implemented                                               |
| Timeline benchmark                       | Implemented as start-to-primary-completion proxy          |
| Competing-trial heatmap                  | Implemented from active registered sites                  |
| Eligibility burden                       | Implemented                                               |
| State/country and candidate-site ranking | Implemented with limitations                              |
| Endpoint comparability                   | Implemented                                               |
| Overall enrollment-risk heuristic        | Implemented                                               |
| Protocol-change recommendations          | Implemented                                               |
| PubMed evidence                          | Implemented                                               |
| Citation-linked memo                     | Deterministic fallback implemented; Groq optional         |
| USCS disease burden                      | Integration boundary implemented; reviewed export pending |

## Remaining External Inputs

Two capabilities cannot be honestly completed from repository code alone:

1. A reviewed USCS/SEER\*Stat state-level lung and bronchus incidence export.
2. A Groq API key plus an account-verified production Llama model ID.

The application exposes both absences as limitations and does not silently
substitute fabricated epidemiology or another model family.
