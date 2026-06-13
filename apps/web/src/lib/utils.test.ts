import { describe, expect, it } from "vitest";
import { formatDate } from "@/lib/utils";

describe("formatDate", () => {
  it("formats UTC timestamps deterministically", () => {
    expect(formatDate("2026-06-13T10:00:00Z")).toBe("Jun 13, 2026");
  });
});
