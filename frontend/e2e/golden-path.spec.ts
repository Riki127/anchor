import { expect, test } from '@playwright/test';
import { begin, answer } from './helpers';
test('three detailed answers complete and persist profile history', async ({ page }) => {
    await begin(page);
    await answer(page, 3);
    await expect(page.getByTestId('verdict')).toBeVisible();
    await page.getByRole('button', { name: 'Back to home' }).click();
    await expect(page.getByRole('button', { name: /View result/ })).toHaveCount(1);
    await page.reload();
    await page.getByRole('button', { name: /View result/ }).click();
    await expect(page.getByTestId('recommendation')).toBeVisible();
});
test('short answers reach ten questions', async ({ page }) => {
    await begin(page);
    await answer(page, 10, 'I helped.');
    await expect(page.getByTestId('verdict')).toBeVisible();
});
