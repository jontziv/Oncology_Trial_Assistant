import { describe, expect, it } from "vitest";
import { analysisFormSchema } from "@/lib/analysis-form";

describe("analysisFormSchema", () => {
  it("requires the decision-critical fields", () => {
    const result = analysisFormSchema.safeParse({
      analysisTitle: "",
      title: "",
      indication: "",
      phases: "",
      overallStatus: "",
      interventionName: "",
      interventionType: "",
      moleculeClass: "",
      biomarker: "",
      targetGeographies: "",
      enrollment: 0,
      eligibilityCriteria: "",
      primaryEndpoint: "",
      primaryEndpointTimeFrame: "",
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues.length).toBeGreaterThan(5);
  });
});
