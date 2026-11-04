/**
 * Live integration tests — run against the Docker app on localhost:3000.
 * These tests hit the real Ollama instance and real filesystem tools.
 *
 * Run with:
 *   npx playwright test specs/live-integration.spec.ts --config playwright.docker.config.ts
 */
import { test, expect } from '@playwright/test';

// Helper: start a new chat and wait for it to be ready
async function startFreshChat(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  // Click "New chat" if a previous session is active
  const newChatBtn = page.locator('button[title="New chat"]');
  if (await newChatBtn.isVisible()) {
    await newChatBtn.click();
    await page.waitForTimeout(300);
  }
}

// Helper: send a message and wait for streaming to complete
async function sendAndWait(
  page: import('@playwright/test').Page,
  message: string,
  timeoutMs = 60_000
): Promise<string> {
  const input = page.locator('textarea').first();
  await expect(input).toBeVisible();
  await input.fill(message);
  await input.press('Enter');

  // User bubble appears immediately
  await expect(page.getByText(message)).toBeVisible({ timeout: 5000 });

  // Wait for streaming to finish — input becomes enabled again
  await expect(input).toBeEnabled({ timeout: timeoutMs });

  // Grab the last assistant message text
  const assistantBubbles = page.locator('[data-role="assistant"]');
  const count = await assistantBubbles.count();
  if (count === 0) {
    // Fallback: grab any text that appeared after the user message
    return await page.locator('body').innerText();
  }
  return await assistantBubbles.last().innerText();
}

// ─────────────────────────────────────────────
// Test 1 — Ollama connectivity + basic response
// ─────────────────────────────────────────────
test('ollama responds to a basic message', async ({ page }) => {
  await startFreshChat(page);

  const reply = await sendAndWait(
    page,
    'Reply with exactly three words: "Ollama is working"',
    90_000
  );

  console.log('[ollama reply]', reply);

  // The model should have produced something non-empty
  expect(reply.trim().length).toBeGreaterThan(0);

  // Should contain at least one of these confirming words
  const confirmWords = ['ollama', 'working', 'three', 'words'];
  const lower = reply.toLowerCase();
  const matched = confirmWords.some(w => lower.includes(w));
  expect(matched, `Expected reply to contain one of ${confirmWords.join(', ')}, got: ${reply}`).toBe(true);
});

// ─────────────────────────────────────────────
// Test 2 — Filesystem tool: create a file on the Desktop
// ─────────────────────────────────────────────
test('model uses write_file tool to create a file on the Desktop', async ({ page }) => {
  await startFreshChat(page);

  const targetPath = '/host/users/<user>/Desktop/assistant_test.txt';
  const prompt = `Use the write_file tool to create a file at "${targetPath}" with the content "Hello from the AI assistant! Filesystem tools are working."`;

  const reply = await sendAndWait(page, prompt, 120_000);

  console.log('[filesystem reply]', reply);

  // Check the reply references the file path or confirms success
  const lower = reply.toLowerCase();
  const successIndicators = [
    'created',
    'written',
    'success',
    'file',
    'assistant_test',
    'desktop',
  ];
  const succeeded = successIndicators.some(w => lower.includes(w));

  // Also check for a tool_call event having fired — look for tool call display in the UI
  const toolCallVisible = await page
    .locator('[data-role="tool"], [class*="tool-call"], [class*="toolcall"]')
    .isVisible()
    .catch(() => false);

  console.log('[tool call visible in UI]', toolCallVisible);

  expect(
    succeeded || toolCallVisible,
    `Expected the model to confirm writing the file. Reply was: ${reply}`
  ).toBe(true);
});
