/**
 * Generator Agent
 *
 * Reads ./plan.json, then for each suite:
 *   1. Reads the relevant component source files listed in suite.sourceFiles
 *   2. Calls the LLM with the suite plan + source → gets a Playwright spec
 *   3. Writes the spec to ./specs/<suite.file>
 *
 * Usage:
 *   npm run generate
 *   (or: npx tsx generator.ts)
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PLAN_FILE = join(__dirname, 'plan.json');
const SPECS_DIR = join(__dirname, 'specs');
const SRC_DIR = join(__dirname, '..', 'frontend-web', 'src');
const API_URL = process.env.API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.API_KEY ?? '';

// ── Types (mirrors planner.ts) ────────────────────────────────────────────

interface TestCase {
  name: string;
  preconditions: string[];
  steps: string[];
  assertions: string[];
}

interface Suite {
  file: string;
  component: string;
  description: string;
  sourceFiles: string[];
  tests: TestCase[];
}

interface TestPlan {
  suites: Suite[];
}

// ── Helpers ───────────────────────────────────────────────────────────────

async function readSourceFile(relPath: string): Promise<string> {
  const fullPath = join(SRC_DIR, relPath);
  if (!existsSync(fullPath)) {
    console.warn(`   ⚠️  Source file not found: ${relPath}`);
    return '';
  }
  return readFile(fullPath, 'utf-8');
}

async function callLLM(prompt: string, systemPrompt: string): Promise<string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (API_KEY) headers['X-API-Key'] = API_KEY;

  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message: prompt,
      system_prompt: systemPrompt,
      model: process.env.GENERATOR_MODEL ?? null,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`LLM API error ${res.status}: ${text}`);
  }

  const data = (await res.json()) as { response: string };
  return data.response;
}

function extractTypeScript(text: string): string {
  // Extract from typescript/ts code fences
  const tsMatch = text.match(/```(?:typescript|ts)\s*([\s\S]*?)```/);
  if (tsMatch) return tsMatch[1].trim();

  // Plain code fence
  const plainMatch = text.match(/```\s*([\s\S]*?)```/);
  if (plainMatch) return plainMatch[1].trim();

  // If the response starts with 'import' it's probably raw TS
  if (text.trim().startsWith('import')) return text.trim();

  // Return as-is and let the user inspect
  return text.trim();
}

// ── Per-suite generation ──────────────────────────────────────────────────

async function generateSuite(suite: Suite): Promise<string> {
  // Collect relevant source
  const sourceSections = await Promise.all(
    suite.sourceFiles.map(async (f) => {
      const content = await readSourceFile(f);
      return content ? `=== FILE: src/${f} ===\n${content}` : '';
    }),
  );
  const sourceContext = sourceSections.filter(Boolean).join('\n\n');

  const systemPrompt = `You are an expert Playwright test author writing TypeScript E2E tests.
You will be given:
  1. The React component source code that is being tested
  2. A structured test plan describing what to test

Your task is to write a complete, runnable Playwright TypeScript spec file.

Rules:
- Use \`@playwright/test\` imports only
- Use role-based locators (getByRole, getByText, getByPlaceholder, getByTitle) — avoid CSS selectors
- Never use page.waitForTimeout() — use proper async waiting (waitFor, expect.toBeVisible, etc.)
- Add a test.beforeEach that navigates to '/' for each test
- Group all tests inside one test.describe block matching the component name
- Each test must be independent and not rely on previous test state
- For tests that need existing messages, mock the API using page.route() or accept the real backend
- Import shared helpers from '../utils/api-helpers.js' where needed
- The app runs at http://localhost:5173 (configured in playwright.config.ts as baseURL)
- Output ONLY the TypeScript code — no prose, no explanation, no markdown`;

  const testPlanText = suite.tests
    .map(
      (t, i) =>
        `Test ${i + 1}: ${t.name}
  Preconditions: ${t.preconditions.join(', ') || 'none'}
  Steps: ${t.steps.join(' → ')}
  Assertions: ${t.assertions.join('; ')}`,
    )
    .join('\n\n');

  const userPrompt = `Component source:
${sourceContext}

Suite: "${suite.description}" (${suite.component})
File to generate: ${suite.file}

Test plan (${suite.tests.length} tests):
${testPlanText}

Write the complete Playwright TypeScript spec file now. Output ONLY TypeScript code.`;

  const response = await callLLM(userPrompt, systemPrompt);
  return extractTypeScript(response);
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  // Read plan
  if (!existsSync(PLAN_FILE)) {
    throw new Error(`plan.json not found at ${PLAN_FILE}. Run 'npm run plan' first.`);
  }

  const planRaw = await readFile(PLAN_FILE, 'utf-8');
  const plan = JSON.parse(planRaw) as TestPlan;
  console.log(`📋 Generator: Loaded plan with ${plan.suites.length} suites`);

  // Ensure specs/ directory exists
  await mkdir(SPECS_DIR, { recursive: true });

  // Generate each suite
  for (let i = 0; i < plan.suites.length; i++) {
    const suite = plan.suites[i];
    console.log(`\n🤖 Generator [${i + 1}/${plan.suites.length}]: Generating ${suite.file}...`);
    console.log(`   Component: ${suite.component} | Tests: ${suite.tests.length}`);

    let code: string;
    try {
      code = await generateSuite(suite);
    } catch (err) {
      console.error(`   ❌ Failed to generate ${suite.file}:`, err);
      continue;
    }

    const outPath = join(__dirname, suite.file);
    // Ensure sub-directory exists (e.g. specs/)
    await mkdir(dirname(outPath), { recursive: true });
    await writeFile(outPath, code, 'utf-8');
    console.log(`   ✅ Written to ${suite.file}`);
  }

  console.log('\n✨ Generator complete. Run "npm test" to execute the specs.');
}

main().catch((err) => {
  console.error('Generator failed:', err);
  process.exit(1);
});
