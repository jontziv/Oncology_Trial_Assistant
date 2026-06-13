import type { TrialDraft } from "@oncology/api-client";
import { z } from "zod";

export const analysisFormSchema = z.object({
  analysisTitle: z.string().trim().min(3, "Enter an analysis title."),
  title: z.string().trim().min(3, "Study title is required."),
  indication: z.string().trim().min(2, "Indication is required."),
  phases: z.string().trim().min(1, "At least one phase is required."),
  overallStatus: z.string().trim().min(1, "Recruitment status is required."),
  interventionName: z.string().trim().min(2, "Intervention is required."),
  interventionType: z.string().trim().min(1, "Intervention type is required."),
  biomarker: z.string(),
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
    biomarker: trial.biomarker ?? "",
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
    biomarker: values.biomarker || null,
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
