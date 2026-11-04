/**
 * Comprehensive filesystem tool tests.
 * Tests all 7 filesystem tools against the running Docker app.
 *
 * Run with:
 *   npx playwright test specs/filesystem-tools.spec.ts --config playwright.docker.config.ts
 */
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

const BASE = '/host/users/<user>';
const DESKTOP = `${BASE}/Desktop`;
const TEST_FILE = `${DESKTOP}/fs_tool_test.txt`;
const MOVED_FILE = `${DESKTOP}/fs_tool_moved.txt`;

// ── Helpers ────────────────────────────────────────────────────────────────

async function freshChat(page: Page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const btn = page.locator('button[title="New chat"]');
  if (await btn.isVisible()) {
    await btn.click();
    await page.waitForTimeout(300);
  }
}

async function send(page: Page, message: string, timeoutMs = 90_000): Promise<string> {
  const input = page.locator('textarea').first();
  await expect(input).toBeVisible();
  await input.fill(message);
  await input.press('Enter');
  await expect(page.getByText(message, { exact: true })).toBeVisible({ timeout: 5000 });
  // Wait for streaming to finish
  await expect(input).toBeEnabled({ timeout: timeoutMs });
  // Return full page text so we can assert on model reply
  return page.locator('body').innerText();
}

async function lastToolResult(page: Page): Promise<{ name: string; args: Record<string, unknown>; result: Record<string, unknown> } | null> {
  // Query the backend DB directly via a helper endpoint — fall back to page text
  try {
    const res = await page.evaluate(async () => {
      const r = await fetch('/api/debug/last-tool-execution');
      if (!r.ok) return null;
      return r.json();
    });
    return res;
  } catch {
    return null;
  }
}

// ── Tests ──────────────────────────────────────────────────────────────────

test.describe('Filesystem Tools', () => {

  // 1. write_file ─────────────────────────────────────────────────────────
  test('write_file: creates a new text file on the Desktop', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use write_file to create the file "${TEST_FILE}" with content "write_file test passed"`
    );
    const lower = body.toLowerCase();
    expect(
      lower.includes('success') || lower.includes('created') || lower.includes('written') || lower.includes('fs_tool_test'),
      `Expected write confirmation. Got:\n${body}`
    ).toBe(true);
  });

  // 2. read_file ──────────────────────────────────────────────────────────
  test('read_file: reads the file just created', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use read_file to read the file "${TEST_FILE}" and tell me its full contents`
    );
    expect(
      body.includes('write_file test passed'),
      `Expected file contents in reply. Got:\n${body}`
    ).toBe(true);
  });

  // 3. get_file_info ──────────────────────────────────────────────────────
  test('get_file_info: returns metadata for the test file', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use get_file_info to get the metadata of "${TEST_FILE}" and tell me its size and type`
    );
    const lower = body.toLowerCase();
    expect(
      lower.includes('file') && (lower.includes('size') || lower.includes('byte') || lower.includes('kb') || lower.includes('modified')),
      `Expected file metadata in reply. Got:\n${body}`
    ).toBe(true);
  });

  // 4. list_directory ─────────────────────────────────────────────────────
  test('list_directory: lists Desktop directory and finds the test file', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use list_directory to list all files in "${DESKTOP}" and tell me if "fs_tool_test.txt" is there`
    );
    expect(
      body.includes('fs_tool_test') || body.toLowerCase().includes('yes') || body.toLowerCase().includes('found'),
      `Expected test file to appear in directory listing. Got:\n${body}`
    ).toBe(true);
  });

  // 5. search_files ───────────────────────────────────────────────────────
  test('search_files: finds the test file by partial name', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use search_files to search for files matching "fs_tool_test" and tell me the results`
    );
    expect(
      body.includes('fs_tool_test'),
      `Expected search to find the test file. Got:\n${body}`
    ).toBe(true);
  });

  // 6. move_file ──────────────────────────────────────────────────────────
  test('move_file: renames the test file', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use move_file to rename "${TEST_FILE}" to "${MOVED_FILE}"`
    );
    const lower = body.toLowerCase();
    expect(
      lower.includes('success') || lower.includes('moved') || lower.includes('renamed') || lower.includes('fs_tool_moved'),
      `Expected move confirmation. Got:\n${body}`
    ).toBe(true);
  });

  // 7. read_file after move ───────────────────────────────────────────────
  test('read_file: can read the file at its new location after move', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use read_file to read "${MOVED_FILE}" and tell me its contents`
    );
    expect(
      body.includes('write_file test passed'),
      `Expected file contents at new path. Got:\n${body}`
    ).toBe(true);
  });

  // 8. delete_file ────────────────────────────────────────────────────────
  test('delete_file: deletes the moved test file', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use delete_file to delete the file "${MOVED_FILE}"`
    );
    const lower = body.toLowerCase();
    expect(
      lower.includes('success') || lower.includes('deleted') || lower.includes('removed'),
      `Expected delete confirmation. Got:\n${body}`
    ).toBe(true);
  });

  // 9. Confirm deletion ───────────────────────────────────────────────────
  test('get_file_info: confirms deleted file no longer exists', async ({ page }) => {
    await freshChat(page);
    const body = await send(
      page,
      `Use get_file_info to check if "${MOVED_FILE}" still exists`
    );
    const lower = body.toLowerCase();
    expect(
      lower.includes('not found') || lower.includes("doesn't exist") || lower.includes('does not exist') || lower.includes('error'),
      `Expected "not found" response for deleted file. Got:\n${body}`
    ).toBe(true);
  });

});
