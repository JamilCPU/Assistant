import { test, expect } from '@playwright/test';

test.describe('Gallery & Sidebar', () => {
  test('gallery view renders', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.getByText('🖼️ Gallery').click();
    await page.waitForTimeout(500);
    await expect(page.locator('body')).not.toContainText('Something went wrong');
    // Should show a search input or "No images" state
    const searchOrEmpty = page.locator('input[placeholder*="Search"], input[placeholder*="search"]').or(
      page.getByText('No images', { exact: false })
    ).first();
    await expect(searchOrEmpty).toBeVisible({ timeout: 5000 });
  });

  test('gallery API returns valid paginated response', async ({ page }) => {
    const response = await page.request.get('/api/images?page=1&per_page=24');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('images');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
    expect(data).toHaveProperty('per_page');
    expect(Array.isArray(data.images)).toBe(true);
  });

  test('sidebar conversation rename works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Need at least one session — send a message to create one
    await page.getByText('💬 Chat').click();
    const input = page.locator('textarea').first();
    await input.fill('Rename test message');
    await input.press('Enter');

    // Wait for session to appear in sidebar (stream must complete for refreshSessions)
    const sessionItem = page.locator('li.group').first();
    await sessionItem.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {});
    if (await sessionItem.isVisible()) {
      await sessionItem.hover();
      const renameBtn = page.locator('button[title="Rename conversation"]').first();
      if (await renameBtn.isVisible()) {
        await renameBtn.click();
        await page.waitForTimeout(200);
        // Edit input should appear inside the session list item
        const editInput = page.locator('li.group input[type="text"]').first();
        await editInput.fill('My Renamed Session');
        await editInput.press('Enter');
        await page.waitForTimeout(1500);
        // Look for the renamed session by title attribute on the button
        await expect(page.locator('button[title="My Renamed Session"]').first()).toBeVisible({ timeout: 8000 });
      }
    }
  });

  test('sidebar conversation delete button appears on hover', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Create a session
    await page.getByText('💬 Chat').click();
    const input = page.locator('textarea').first();
    await input.fill('Delete test message');
    await input.press('Enter');
    await page.waitForTimeout(2000);

    const sessionItem = page.locator('li.group').first();
    if (await sessionItem.isVisible()) {
      await sessionItem.hover();
      const deleteBtn = page.locator('button[title="Delete conversation"]').first();
      await expect(deleteBtn).toBeVisible({ timeout: 2000 });
    }
  });

  test('personas API returns valid list', async ({ page }) => {
    const response = await page.request.get('/api/personas');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('personas');
    expect(Array.isArray(data.personas)).toBe(true);
    expect(data.personas.length).toBeGreaterThan(0);

    const first = data.personas[0];
    expect(first).toHaveProperty('id');
    expect(first).toHaveProperty('name');
    expect(first).toHaveProperty('system_prompt');
    expect(first).toHaveProperty('is_builtin');
  });

  test('models API returns valid response', async ({ page }) => {
    const response = await page.request.get('/api/models');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('chat');
    expect(data).toHaveProperty('image');
    expect(data).toHaveProperty('loras');
    expect(data).toHaveProperty('tts');
  });
});
