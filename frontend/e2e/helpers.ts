import { expect, type Page } from '@playwright/test';
export const api = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';
export const detailed = 'I led a specific project, clarified requirements with stakeholders, implemented and tested the solution, measured the outcome, and improved team delivery through documented feedback.';
export async function goToStartScreen(page: Page) {
    await page.goto('/');
    await page.getByLabel('Your name').fill(`Coachee ${Date.now()} ${Math.random()}`);
    await page.getByRole('button', { name: 'Continue' }).click();
    await page.getByRole('button', { name: 'Start a new check-in' }).click();
}
export async function begin(page: Page) {
    await goToStartScreen(page);
    await page.getByLabel('Role to explore').fill('Software Engineer');
    await page.getByRole('button', { name: 'Explore role' }).click();
    await page.getByRole('radio').first().check();
    await page.getByRole('checkbox', { name: /reviewed/ }).check();
    await page.getByRole('button', { name: 'Continue' }).click();
    await page.getByRole('button', { name: 'Start the conversation' }).click();
}
export async function answer(page: Page, count: number, text = detailed) {
    for (let i = 1; i <= count; i++) {
        await expect(page.getByText(`Question ${i}`, { exact: true })).toBeVisible();
        await page.getByLabel('Your answer').fill(text);
        await page.getByRole('button', { name: 'Continue' }).click();
    }
}
