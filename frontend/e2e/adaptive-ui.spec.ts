import { expect, test } from '@playwright/test';
import { begin, goToStartScreen, detailed } from './helpers';

test('suggested ladder requires review before continuing', async ({ page }) => {
    await goToStartScreen(page);
    await page.getByLabel('Role to explore').fill('Software Engineer');
    await page.getByRole('button', { name: 'Explore role' }).click();
    await page.getByRole('radio').first().check();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByRole('checkbox', { name: /reviewed/ })).toBeFocused();
    await expect(page.getByText(/not an employer-approved or verified/)).toBeVisible();
    await page.getByRole('checkbox', { name: /reviewed/ }).check();
    await page.getByRole('radio').nth(1).check();
    await expect(page.getByRole('checkbox', { name: /reviewed/ })).not.toBeChecked();
    await page.getByRole('checkbox', { name: /reviewed/ }).check();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByRole('button', { name: 'Start the conversation' })).toBeVisible();
    await page.getByRole('button', { name: 'Back to levels' }).click();
    await expect(page.getByRole('checkbox', { name: /reviewed/ })).not.toBeChecked();
});
test('provider failure keeps the answer and item for retry', async ({ page }) => {
    await begin(page);
    const submissions: unknown[] = [];
    let fail = true;
    await page.route('**/sessions/*/answer', async (route) => {
        submissions.push(route.request().postDataJSON());
        if (fail) {
            fail = false;
            await route.fulfill({ status: 502, body: '{}', contentType: 'application/json' });
        }
        else
            await route.continue();
    });
    await page.getByLabel('Your answer').fill('  ' + detailed + '  ');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText(/coach could not respond/)).toBeVisible();
    await expect(page.getByLabel('Your answer')).toHaveValue('  ' + detailed + '  ');
    await expect(page.getByText('Question 1', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText('Question 2', { exact: true })).toBeVisible();
    expect(submissions[0]).toEqual(submissions[1]);
    await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
    await expect(page.getByLabel('Your answer')).toHaveValue('');
});
test('keyboard profile and tier selection preserve role and tier on back', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('main')).toHaveCount(1);
    await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('Your name')).toBeFocused();
    await page.keyboard.type('Keyboard ' + Date.now());
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Welcome');
    await expect(page.getByRole('button', { name: 'Start a new check-in' })).toBeEnabled();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    await page.keyboard.type('Software Engineer');
    await page.keyboard.press('Enter');
    await expect(page.getByRole('group')).toBeVisible();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');
    await page.keyboard.press('ArrowDown');
    const choice = await page.locator('input:checked').inputValue();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { level: 1 })).toContainText('conversation');
    await page.getByRole('button', { name: 'Back to levels' }).click();
    await expect(page.locator('input:checked')).toHaveValue(choice);
    await page.getByRole('button', { name: 'Back to role' }).click();
    await expect(page.getByLabel('Role to explore')).toHaveValue('Software Engineer');
    await page.getByRole('button', { name: 'Explore role' }).click();
    await expect(page.locator('input:checked')).toHaveValue(choice);
    await page.screenshot({ path: 'test-results/adaptive-desktop-tiers.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: 'test-results/adaptive-mobile-tiers.png', fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
test('invalid input and profile switch are visible and usable', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Your name').fill('   ');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByLabel('Your name')).toBeFocused();
    await expect(page.getByLabel('Your name')).toHaveAttribute('aria-invalid', 'true');
    await goToStartScreen(page);
    await page.getByRole('button', { name: 'Back to home' }).click();
    await page.getByRole('button', { name: 'Switch profile' }).click();
    await expect(page.getByLabel('Your name')).toHaveValue('');
    expect(await page.evaluate(() => localStorage.getItem('anchor.person'))).toBeNull();
});
test('failed profile restore can be retried without showing empty history', async ({ page }) => {
    await goToStartScreen(page);
    await page.route('**/people/*/status', route => route.fulfill({ status: 503, body: '{}' }));
    await page.reload();
    await expect(page.getByText(/Could not load or save/)).toBeVisible();
    await expect(page.getByText('No completed check-ins yet.')).toHaveCount(0);
    await page.unroute('**/people/*/status');
    await page.getByRole('button', { name: 'Retry loading profile' }).click();
    await expect(page.getByText('No completed check-ins yet.')).toBeVisible();
});
test('session conflict retains answer and offers home navigation', async ({ page }) => {
    await begin(page);
    await page.route('**/sessions/*/answer', route => route.fulfill({ status: 409, body: '{}' }));
    await page.getByLabel('Your answer').fill(detailed);
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText(/conflicts with the saved session/)).toBeVisible();
    await expect(page.getByLabel('Your answer')).toHaveValue(detailed);
    await page.getByRole('button', { name: 'Back to home' }).click();
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Welcome');
});
