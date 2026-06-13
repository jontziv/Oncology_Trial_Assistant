export type SourceReference = {
  provider: string;
  record_id: string;
  url: string;
  retrieved_at: string;
  source_version: string | null;
  field_locators: Record<string, string>;
};

export type Intervention = {
  name: string;
  intervention_type: string;
  description: string | null;
};

export type Endpoint = {
  measure: string;
  time_frame: string | null;
  description: string | null;
};

export type Site = {
  facility: string | null;
  city: string | null;
  state: string | null;
  country: string;
  status: string | null;
  latitude: number | null;
  longitude: number | null;
};

export type TrialDraft = {
  nct_id: string;
  title: string;
  overall_status: string;
  indication: string;
  conditions: string[];
  phases: string[];
  interventions: Intervention[];
  biomarker: string | null;
  summary: string | null;
  eligibility_criteria: string;
  minimum_age: string | null;
  maximum_age: string | null;
  sex: string | null;
  healthy_volunteers: boolean | null;
  study_design: {
    study_type: string;
    allocation: string | null;
    intervention_model: string | null;
    primary_purpose: string | null;
    masking: string | null;
    arm_count: number;
  };
  primary_endpoints: Endpoint[];
  secondary_endpoints: Endpoint[];
  enrollment: number;
  enrollment_type: string | null;
  start_date: string | null;
  primary_completion_date: string | null;
  sites: Site[];
  source: SourceReference;
};

export type TrialSearchResult = {
  nct_id: string;
  title: string;
  overall_status: string;
  phases: string[];
  conditions: string[];
  interventions: string[];
  enrollment: number | null;
  us_site_count: number;
};

export type TrialSearchResponse = {
  items: TrialSearchResult[];
  next_page_token: string | null;
  total_count: number | null;
};

export type Analysis = {
  id: string;
  owner_id: string;
  title: string;
  status: "draft" | "ready";
  trial: TrialDraft;
  created_at: string;
  updated_at: string;
};
