import type { TrialDraft } from "@oncology/api-client";
import { z } from "zod";

export function createBlankTrialDraft(params: {
  indication: string;
  phases: string;
  moleculeClass: string;
  biomarker: string;
  geography: string;
  interventionName: string;
  primaryEndpoint: string;
  eligibilityCriteria: string;
}): TrialDraft {
  const suffix = Date.now().toString().slice(-6);
  const manualId = `MANUAL${suffix}`;
  const now = new Date().toISOString();
  const geos = params.geography
    .split(",")
    .map((g) => g.trim())
    .filter(Boolean);
  return {
    nct_id: manualId,
    title: `Manual protocol – ${params.indication}`,
    overall_status: "NOT_YET_RECRUITING",
    indication: params.indication,
    conditions: [params.indication],
    phases: params.phases
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean),
    interventions: [
      {
        name: params.interventionName || "To be specified",
        intervention_type: "DRUG",
        description: null,
      },
    ],
    molecule_class: params.moleculeClass || null,
    biomarker: params.biomarker || null,
    target_geographies: geos.length ? geos : ["United States"],
    summary: null,
    eligibility_criteria:
      params.eligibilityCriteria ||
      "Inclusion criteria:\n- To be specified\n\nExclusion criteria:\n- To be specified",
    minimum_age: null,
    maximum_age: null,
    sex: null,
    healthy_volunteers: null,
    study_design: {
      study_type: "INTERVENTIONAL",
      allocation: "RANDOMIZED",
      intervention_model: "PARALLEL",
      primary_purpose: "TREATMENT",
      masking: null,
      arm_count: 0,
    },
    primary_endpoints: [
      {
        measure: params.primaryEndpoint || "Overall Survival",
        time_frame: null,
        description: null,
      },
    ],
    secondary_endpoints: [],
    has_results: false,
    results_primary_endpoints: [],
    enrollment: 100,
    enrollment_type: "ESTIMATED",
    start_date: null,
    start_date_type: null,
    primary_completion_date: null,
    primary_completion_date_type: null,
    sites: [],
    source: {
      provider: "Manual entry",
      record_id: manualId,
      url: "https://clinicaltrials.gov",
      retrieved_at: now,
      source_version: null,
      field_locators: {},
    },
  };
}

export const analysisFormSchema = z.object({
  analysisTitle: z.string().trim().min(3, "Enter an analysis title."),
  title: z.string().trim().min(3, "Study title is required."),
  indication: z.string().trim().min(2, "Indication is required."),
  phases: z.string().trim().min(1, "At least one phase is required."),
  overallStatus: z.string().trim().min(1, "Recruitment status is required."),
  interventionName: z.string().trim().min(2, "Intervention is required."),
  interventionType: z.string().trim().min(1, "Intervention type is required."),
  moleculeClass: z.string(),
  biomarker: z.string(),
  targetGeographies: z
    .string()
    .trim()
    .min(2, "Enter at least one target country."),
  enrollment: z.number().int().min(1, "Enrollment must be at least 1."),
  eligibilityCriteria: z
    .string()
    .trim()
    .min(3, "Eligibility criteria are required."),
  primaryEndpoint: z.string().trim().min(2, "Primary endpoint is required."),
  primaryEndpointTimeFrame: z.string(),
});

export type AnalysisFormValues = z.infer<typeof analysisFormSchema>;

export function trialToForm(
  trial: TrialDraft,
  analysisTitle = `${trial.nct_id} feasibility review`,
): AnalysisFormValues {
  return {
    analysisTitle,
    title: trial.title,
    indication: trial.indication,
    phases: trial.phases.join(", "),
    overallStatus: trial.overall_status,
    interventionName: trial.interventions[0]?.name ?? "",
    interventionType: trial.interventions[0]?.intervention_type ?? "",
    moleculeClass: trial.molecule_class ?? "",
    biomarker: trial.biomarker ?? "",
    targetGeographies: (trial.target_geographies ?? ["United States"]).join(
      ", ",
    ),
    enrollment: trial.enrollment,
    eligibilityCriteria: trial.eligibility_criteria,
    primaryEndpoint: trial.primary_endpoints[0]?.measure ?? "",
    primaryEndpointTimeFrame: trial.primary_endpoints[0]?.time_frame ?? "",
  };
}

export function formToTrial(
  values: AnalysisFormValues,
  source: TrialDraft,
): TrialDraft {
  return {
    ...source,
    title: values.title,
    indication: values.indication,
    conditions: [values.indication, ...source.conditions.slice(1)],
    phases: values.phases
      .split(",")
      .map((phase) => phase.trim())
      .filter(Boolean),
    overall_status: values.overallStatus,
    interventions: [
      {
        ...source.interventions[0],
        name: values.interventionName,
        intervention_type: values.interventionType,
      },
      ...source.interventions.slice(1),
    ],
    molecule_class: values.moleculeClass || null,
    biomarker: values.biomarker || null,
    target_geographies: values.targetGeographies
      .split(",")
      .map((country) => country.trim())
      .filter(Boolean),
    enrollment: values.enrollment,
    eligibility_criteria: values.eligibilityCriteria,
    primary_endpoints: [
      {
        ...source.primary_endpoints[0],
        measure: values.primaryEndpoint,
        time_frame: values.primaryEndpointTimeFrame || null,
      },
      ...source.primary_endpoints.slice(1),
    ],
  };
}
