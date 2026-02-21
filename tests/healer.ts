/**
 * Healer Agent
 *
 * 1. Runs Playwright tests and captures the JSON report
 * 2. For each failing test, reads the spec file + relevant component source
 * 3. Calls the LLM to produce a fixed version of the spec
 * 4. Writes the fix back to disk
 * 5. Re-runs to verify — up to MAX_ROUNDS rounds
 *
 * Usage:
 *   npm run heal
 *   (or: npx tsx healer.ts)
 */

import { readFile, writeFile } from 'fs/promises';
import { join, relative, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';
import { spawnSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const RESULTS_FILE = join(__dirname, 'test-results.json');
const SPECS_DIR = join(__dirname, 'specs');
const SRC_DIR = join(__dirname, '..', 'frontend-web', 'src');
const API_URL = process.env.API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.API_KEY ?? '';
const MAX_ROUNDS = parseInt(process.env.HEAL_ROUNDS ?? '3', 10);

// ── Types ─────────────────────────────────────────────────────────────────

interface PWError {
  message: string;
  value?: string;
}

interface PWResult {
  status: 'passed' | 'failed' | 'skipped' | 'timedOut';
  errors?: PWError[];
}

interface PWTest {
  title: string;
  location: { file: string; line: number };
  results: PWResult[];
}

interface PWSuite {
  title: string;
  specs?: PWTest[];
  suites?: PWSuite[];
}

interface PWReport {
  suites: PWSuite[];
}

interface FailingTest {
  specFile: string;      // absolute path to the spec file
  testName: string;
  errorMessage: string;
}

// ── Playwright runner ─────────────────────────────────────────────────────

function runTests(): boolean {
  console.log('▶  Running Playwright tests...');
  const result = spawnSync(
    'npx',
    ['playwright', 'test', '--reporter=json'],
    {
      cwd: __dirname,
      shell: true,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 120_000,
      env: { ...process.env },
    },
  );

  // Write JSON report (stdout from playwright --reporter=json)
  if (result.stdout) {
    writeFile(RESULTS_FILE, result.stdout, 'utf-8').catch(() => {});
  }

  return result.status === 0;
}

// ── Report parsing ────────────────────────────────────────────────────────

async function readReport(): Promise<PWReport | null> {
  if (!existsSync(RESULTS_FILE)) return null;
  const raw = await readFile(RESULTS_FILE, 'utf-8');
  try {
    return JSON.parse(raw) as PWReport;
  } catch {
    return null;
  }
}

function collectFailures(suites: PWSuite[], failures: FailingTest[] = []): FailingTest[] {
  for (const suite of suites) {
    if (suite.suites) collectFailures(suite.suites, failures);
    if (suite.specs) {
      for (const spec of suite.specs) {
        for (const result of spec.results) {
          if (result.status === 'failed' || result.status === 'timedOut') {
            const errorParts: string[] = [];
            for (const err of result.errors ?? []) {
              errorParts.push(err.message ?? '');
              if (err.value) errorParts.push(err.value);
            }
            failures.push({
              specFile: spec.location.file,
              testName: spec.title,
              errorMessage: errorParts.join('\n').slice(0, 2000),
            });
          }
        }
      }
    }
  }
  return failures;
}

// ── Source file inference ─────────────────────────────────────────────────

/**
 * Given a spec filename like "chat.spec.ts", try to find matching component
 * source files (e.g. ChatView.tsx, MessageBubble.tsx, ChatContext.tsx).
 */
async function inferSourceFiles(specFile: string): Promise<string> {
  const specBase = specFile.replace(/\.spec\.ts$/, '').toLowerCase();

  // Map spec names to likely component source files
  const mapping: Record<string, string[]> = {
    welcome: ['components/WelcomeScreen.tsx'],
    chat: ['components/ChatView.tsx', 'components/MessageBubble.tsx', 'context/ChatContext.tsx'],
    sidebar: ['components/Sidebar.tsx', 'context/ChatContext.tsx'],
    topbar: ['components/TopBar.tsx', 'context/ChatContext.tsx'],
    image: ['components/ImageView.tsx', 'api/client.ts'],
  };

  const key = Object.keys(mapping).find((k) => specBase.includes(k));
  const sourceRelPaths = key ? mapping[key] : ['App.tsx'];

  const sections: string[] = [];
  for (const relPath of sourceRelPaths) {
    const fullPath = join(SRC_DIR, relPath);
    if (existsSync(fullPath)) {
      const content = await readFile(fullPath, 'utf-8');
      sections.push(`=== FILE: src/${relPath} ===\n${content}`);
    }
  }
  return sections.join('\n\n');
}

// ── LLM call ─────────────────────────────────────────────────────────────

async function callLLM(prompt: string, systemPrompt: string): Promise<string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (API_KEY) headers['X-API-Key'] = API_KEY;

  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message: prompt,
      system_prompt: systemPrompt,
      model: process.env.HEALER_MODEL ?? null,
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
  const tsMatch = text.match(/```(?:typescript|ts)\s*([\s\S]*?)```/);
  if (tsMatch) return tsMatch[1].trim();
  const plainMatch = text.match(/```\s*([\s\S]*?)```/);
  if (plainMatch) return plainMatch[1].trim();
  if (text.trim().startsWith('import')) return text.trim();
  return text.trim();
}

// ── Healing logic ─────────────────────────────────────────────────────────

async function healSpec(failure: FailingTest, specContent: string, sourceContext: string): Promise<string> {
  const systemPrompt = `You are an expert Playwright test author and debugger.
You will be given:
  1. A failing Playwright TypeScript test file
  2. The exact error message / stack trace from the test run
  3. The React component source code that the test targets

Your task is to fix the test so it passes.

Common issues to check:
- Wrong locator (element text, role, or placeholder changed)
- Missing await on an async assertion
- Timing issue — replace hard waits with proper waitFor/expect patterns
- Test assumes wrong initial state
- API mock (page.route) pattern is incorrect

Rules:
- Output ONLY the corrected TypeScript file — no explanation, no prose, no markdown fences
- Keep all test cases — fix only what is broken
- Do not add new test cases
- Do not change test names`;

  const userPrompt = `FAILING SPEC FILE:
${specContent}

ERROR MESSAGE:
${failure.errorMessage}

TEST THAT FAILED: "${failure.testName}"

COMPONENT SOURCE:
${sourceContext}

Fix the spec file and return the complete corrected TypeScript. Output ONLY code.`;

  const response = await callLLM(userPrompt, systemPrompt);
  return extractTypeScript(response);
}

// ── Deduplication: group failures by spec file ────────────────────────────

function groupBySpec(failures: FailingTest[]): Map<string, FailingTest[]> {
  const map = new Map<string, FailingTest[]>();
  for (const f of failures) {
    const key = f.specFile;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(f);
  }
  return map;
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  let round = 0;

  while (round < MAX_ROUNDS) {
    round++;
    console.log(`\n🔄 Healer — Round ${round}/${MAX_ROUNDS}`);

    const allPassed = runTests();
    if (allPassed) {
      console.log('✅ All tests pass! Nothing to heal.');
      return;
    }

    const report = await readReport();
    if (!report) {
      console.error('❌ Could not read test-results.json');
      process.exit(1);
    }

    const failures = collectFailures(report.suites);
    if (failures.length === 0) {
      console.log('✅ No failures found in report. Done.');
      return;
    }

    console.log(`\n🩺 Found ${failures.length} failing test(s) across ${new Set(failures.map((f) => f.specFile)).size} file(s)`);

    const bySpec = groupBySpec(failures);

    for (const [specFile, specFailures] of bySpec) {
      // Resolve the spec file path (Playwright reports relative paths)
      const absSpecFile = existsSync(specFile)
        ? specFile
        : join(__dirname, specFile);

      if (!existsSync(absSpecFile)) {
        console.warn(`   ⚠️  Spec file not found: ${specFile} — skipping`);
        continue;
      }

      const specContent = await readFile(absSpecFile, 'utf-8');
      const sourceContext = await inferSourceFiles(absSpecFile.replace(/\\/g, '/').split('/').pop() ?? '');

      // Combine all errors for this spec file into one healing call
      const combinedErrors = specFailures
        .map((f) => `Test: "${f.testName}"\nError:\n${f.errorMessage}`)
        .join('\n\n---\n\n');

      console.log(`\n🤖 Healing ${relative(__dirname, absSpecFile)} (${specFailures.length} failure(s))...`);

      let fixed: string;
      try {
        // Use the first failure for the primary testName but pass combined errors
        const primary = specFailures[0];
        primary.errorMessage = combinedErrors;
        fixed = await healSpec(primary, specContent, sourceContext);
      } catch (err) {
        console.error(`   ❌ LLM call failed for ${specFile}:`, err);
        continue;
      }

      await writeFile(absSpecFile, fixed, 'utf-8');
      console.log(`   ✅ Wrote healed spec to ${relative(__dirname, absSpecFile)}`);
    }
  }

  // Final verification run
  console.log(`\n🔄 Healer — Final verification run`);
  const finalPassed = runTests();
  if (finalPassed) {
    console.log('✅ All tests pass after healing!');
  } else {
    console.log(`⚠️  Some tests still failing after ${MAX_ROUNDS} rounds. Manual review needed.`);
    const finalReport = await readReport();
    if (finalReport) {
      const remaining = collectFailures(finalReport.suites);
      for (const f of remaining) {
        console.log(`   ✗ ${f.testName} (${f.specFile})`);
      }
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Healer failed:', err);
  process.exit(1);
});
