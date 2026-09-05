import type { Page } from "@playwright/test";

/**
 * The Home screen shows a different entry button depending on whether the
 * employee already has a completed session in the (real, shared) dev
 * database - "Get started" for a first-time visit, "Start a new check-in"
 * for a returning one. Either leads to the same role-title Start screen.
 */
export async function goToStartScreen(page: Page): Promise<void> {
  await page.goto("/");
  const getStarted = page.getByTestId("get-started-button");
  const startNew = page.getByTestId("start-new-button");
  await Promise.race([getStarted.waitFor({ state: "visible" }), startNew.waitFor({ state: "visible" })]);
  if (await getStarted.isVisible()) {
    await getStarted.click();
  } else {
    await startNew.click();
  }
}
