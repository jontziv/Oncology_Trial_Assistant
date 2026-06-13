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
  await page.route("http://localhost:8000/v1/analyses", async (route) => {
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
