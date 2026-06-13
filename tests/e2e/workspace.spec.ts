import { expect, test } from "@playwright/test";

test("presents the product limitation and trial workspace entry", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Make the first feasibility conversation more rigorous.",
    }),
  ).toBeVisible();
  await expect(page.getByText("Illustrative methodology.")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Start an analysis" }),
  ).toBeVisible();
});

test("shows an empty saved-analysis state in demo mode", async ({ page }) => {
  await page.route("**/v1/analyses", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "[]",
    });
  });

  await page.goto("/analyses");

  await expect(
    page.getByRole("heading", { name: "Saved analyses" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "No saved analyses yet" }),
  ).toBeVisible();
});

test("renders a completed feasibility analysis", async ({ page }) => {
  await page.route("**/v1/analyses/demo/results", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        methodology_version: "oncology-feasibility-v0.2",
        overall_score: 58,
        risk_band: "moderate",
        confidence: 0.68,
        confidence_label: "Medium",
        sensitivity_low: 54,
        sensitivity_high: 62,
        components: [
          {
            key: "eligibility",
            label: "Eligibility burden",
            score: 68,
            weight: 0.25,
            weighted_contribution: 17,
            confidence: 0.8,
            rationale: "Biomarker and CNS restrictions increase burden.",
            inputs: {},
          },
        ],
        eligibility: {
          score: 68,
          band: "high",
          criterion_count: 24,
          inclusion_count: 12,
          exclusion_count: 12,
          factors: [],
          confidence: 0.8,
          methodology: "Rule-based burden index.",
        },
        timeline: {
          label: "Start-to-primary-completion timeline proxy",
          median_months: 28,
          q1_months: 22,
          q3_months: 34,
          cohort_size: 12,
          excluded_count: 3,
          confidence: 0.7,
          limitation: "Not recruitment duration.",
        },
        competition: {
          score: 62,
          active_trial_count: 7,
          active_us_site_count: 48,
          confidence: 0.7,
          limitation: "Registered sites only.",
          regions: [
            {
              region: "California",
              active_trial_count: 4,
              active_site_count: 12,
              weighted_density: 9.4,
              target_site_count: 2,
            },
          ],
        },
        geography: [
          {
            region: "Texas",
            level: "state",
            opportunity_score: 79,
            historical_trial_count: 9,
            active_competing_sites: 3,
            candidate_facilities: ["Example Cancer Center"],
            rationale: "Historical footprint with lower competition.",
            confidence: 0.55,
          },
        ],
        endpoints: {
          score: 75,
          target_family: "objective response",
          cohort_distribution: { "objective response": 9 },
          comparable_count: 9,
          cohort_size: 12,
          rationale: "9 of 12 trials use objective response.",
          confidence: 0.7,
        },
        recommendations: [
          {
            priority: "high",
            category: "eligibility",
            recommendation: "Remove nonessential laboratory restrictions.",
            expected_benefit: "Broader eligible pool.",
            tradeoff: "More heterogeneous population.",
            evidence_ids: ["CTGOV:NCT00000001"],
          },
        ],
        similar_trials: [
          {
            nct_id: "NCT00000001",
            title: "Comparable NSCLC study",
            similarity_score: 82,
            overall_status: "RECRUITING",
            phases: ["PHASE2"],
            enrollment: 100,
            us_site_count: 10,
            matched_features: ["indication", "phase"],
            mismatched_features: [],
            source: {
              provider: "ClinicalTrials.gov",
              record_id: "NCT00000001",
              url: "https://clinicaltrials.gov/study/NCT00000001",
              retrieved_at: "2026-06-13T00:00:00Z",
              field_locators: {},
            },
          },
        ],
        publications: [],
        memo: {
          generated_by: "Deterministic template",
          executive_summary: "Illustrative enrollment risk is moderate.",
          key_risks: ["Eligibility burden is elevated."],
          recommendations: ["Review exclusions."],
          limitations: ["Not a validated prediction."],
          citation_ids: ["CTGOV:NCT00000001"],
        },
        sources: [
          {
            source_id: "CTGOV:NCT00000001",
            source_type: "trial",
            title: "Comparable NSCLC study",
            url: "https://clinicaltrials.gov/study/NCT00000001",
            record_id: "NCT00000001",
            retrieved_at: "2026-06-13T00:00:00Z",
            locator: "Protocol record",
          },
        ],
        warnings: ["USCS state rates are not loaded."],
        generated_at: "2026-06-13T00:00:00Z",
      }),
    });
  });
  await page.route("**/v1/analyses/demo", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "demo",
        title: "NSCLC feasibility",
        trial: { nct_id: "NCT00000002" },
      }),
    });
  });

  await page.goto("/analyses/demo/results");

  await expect(
    page.getByRole("heading", { name: "Risk decomposition" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "What I would change" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Comparable trial cohort" }),
  ).toBeVisible();
});
