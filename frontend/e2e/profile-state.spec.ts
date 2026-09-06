import { expect, test } from "@playwright/test";
import { goToStartScreen } from "./helpers";

test("profile entry cannot clear a pending role operation with a redundant status response", async ({ page }) => {
  let statusRequests = 0;
  let releaseStatus = () => {};
  let releaseRole = () => {};
  const statusGate = new Promise<void>((resolve) => { releaseStatus = resolve; });
  const roleGate = new Promise<void>((resolve) => { releaseRole = resolve; });

  await page.route("**/people/*/status", async (route) => {
    statusRequests++;
    if (statusRequests === 2) {
      await statusGate;
    }
    await route.continue();
  });
  await goToStartScreen(page);
  await page.route("**/roles/resolve", async (route) => {
    await roleGate;
    await route.continue();
  });
  await page.getByLabel("Role to explore").fill("Software Engineer");
  await page.getByRole("button", { name: "Explore role" }).click();
  await expect(page.getByLabel("Role to explore")).toBeDisabled();
  releaseStatus();
  // A redundant status response must not finish the pending role operation.
  expect(statusRequests).toBe(1);
  await expect(page.getByLabel("Role to explore")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Back to home" })).toBeDisabled();
  releaseRole();
  await expect(page.getByRole("group")).toBeVisible();
  await page.getByRole("button", { name: "Back to home" }).click();
  await page.getByRole("button", { name: "Switch profile" }).click();
  const nextName = "Another profile " + Date.now();
  await page.getByLabel("Your name").fill(nextName);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Welcome, " + nextName);
});

test("nullable history fields show explicit fallbacks", async ({ page }) => {
  await page.route("**/people/*/status", async (route) => {
    const response = await route.fetch();
    const status = await response.json();
    await route.fulfill({
      json: {
        ...status,
        sessions: [{
          id: 1,
          role_title: "Software Engineer",
          selected_tier_name: null,
          completed_at: null,
          verdict: null,
        }],
      },
    });
  });
  await goToStartScreen(page);
  await page.getByRole("button", { name: "Back to home" }).click();
  await expect(page.getByText("Software Engineer · Level not recorded")).toBeVisible();
  await expect(page.getByText("Date not recorded · Result not recorded")).toBeVisible();
  await expect(page.getByText(/1970/)).toHaveCount(0);
});
