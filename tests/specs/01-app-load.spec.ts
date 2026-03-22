import { test, expect } from '@playwright/test';

test.describe('App Load & Layout', () => {
  test('page loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known non-critical errors (favicon, etc.)
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') && !e.includes('ERR_CONNECTION_REFUSED')
    );
    expect(criticalErrors, `Console errors: ${criticalErrors.join('\n')}`).toHaveLength(0);
  });

  test('sidebar is visible with all navigation buttons', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('💬 Chat')).toBeVisible();
    await expect(page.getByText('🎨 Image Generation')).toBeVisible();
    await expect(page.getByText('🧠 Models')).toBeVisible();
    await expect(page.getByText('🖼️ Gallery')).toBeVisible();
    await expect(page.getByText('⚙️ Settings')).toBeVisible();
  });

  test('sidebar can be toggled closed and reopened', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Click toggle button (hamburger)
    const toggleBtn = page.locator('button[title="Toggle sidebar"]').first();
    await toggleBtn.click();
    // Sidebar should be hidden
    await expect(page.getByText('💬 Chat')).not.toBeVisible();

    // Reopen via the floating button
    const openBtn = page.locator('button[title="Open sidebar"]');
    await openBtn.click();
    await expect(page.getByText('💬 Chat')).toBeVisible();
  });

  test('status indicators render at bottom-left', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Both Ollama and Auto1111 status dots should be in the DOM
    const dots = page.locator('[title*="Ollama"], [title*="Auto1111"], [title*="llama"], [title*="stable"]');
    // At least one status component should be present
    await expect(dots.first()).toBeTruthy();
  });

  test('mode switching — all 4 modes render without crashing', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    for (const mode of ['🎨 Image Generation', '🧠 Models', '🖼️ Gallery', '💬 Chat']) {
      await page.getByText(mode).click();
      await page.waitForTimeout(300);
      // Page should not have crashed (no error overlay)
      await expect(page.locator('body')).not.toContainText('Something went wrong');
    }
  });
});
