/**
 * Planner Agent
 *
 * Reads every .tsx/.ts file under ../frontend-web/src/, sends the collected
 * source to the local LLM backend (POST /api/chat), and writes the resulting
 * structured test plan to ./plan.json.
 *
 * Usage:
 *   npm run plan
 *   (or: npx tsx planner.ts)
 */

import { readdir, readFile, writeFile, stat } from 'fs/promises';
import { join, relative, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SRC_DIR = join(__dirname, '..', 'frontend-web', 'src');
const PLAN_OUT = join(__dirname, 'plan.json');
const API_URL = process.env.API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.API_KEY ?? '';

// ── Types ────────────────────────────────────────────────────────────────

export interface TestCase {
  name: string;
  preconditions: string[];
  steps: string[];
  assertions: string[];
}

export interface Suite {
  file: string;
  component: string;
  description: string;
  sourceFiles: string[];
  tests: TestCase[];
}

export interface TestPlan {
  suites: Suite[];
}

// ── File collection ──────────────────────────────────────────────────────

async function collectSourceFiles(dir: string): Promise<Array<{ path: string; content: string }>> {
  const results: Array<{ path: string; content: string }> = [];

  async function walk(current: string) {
    const entries = await readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = join(current, entry.name);
      if (entry.isDirectory()) {
        // Skip node_modules, dist, assets
        if (!['node_modules', 'dist', 'assets', '.git'].includes(entry.name)) {
          await walk(fullPath);
        }
      } else if (['.ts', '.tsx'].includes(extname(entry.name))) {
        const content = await readFile(fullPath, 'utf-8');
        const relPath = relative(SRC_DIR, fullPath).replace(/\\/g, '/');
        results.push({ path: relPath, content });
      }
    }
  }

  await walk(dir);
  return results;
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
      model: process.env.PLANNER_MODEL ?? null,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`LLM API error ${res.status}: ${text}`);
  }

  const data = (await res.json()) as { response: string };
  return data.response;
}

// ── JSON extraction ───────────────────────────────────────────────────────

function extractJSON(text: string): unknown {
  // Try to extract JSON from markdown code blocks first
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenceMatch) {
    return JSON.parse(fenceMatch[1].trim());
  }
  // Fall back to finding the first { ... } block
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start !== -1 && end !== -1) {
    return JSON.parse(text.slice(start, end + 1));
  }
  throw new Error('No JSON found in LLM response');
}

function validatePlan(data: unknown): TestPlan {
  if (typeof data !== 'object' || data === null) throw new Error('Plan is not an object');
  const plan = data as Record<string, unknown>;
  if (!Array.isArray(plan.suites)) throw new Error('Plan missing suites array');
  for (const suite of plan.suites as unknown[]) {
    const s = suite as Record<string, unknown>;
    if (typeof s.file !== 'string') throw new Error('Suite missing file');
    if (typeof s.component !== 'string') throw new Error('Suite missing component');
    if (!Array.isArray(s.tests)) throw new Error('Suite missing tests array');
  }
  return data as TestPlan;
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  console.log('📖 Planner: Reading source files from', SRC_DIR);

  const files = await collectSourceFiles(SRC_DIR);
  console.log(`   Found ${files.length} source files`);

  // Build the source context block
  const sourceContext = files
    .map((f) => `=== FILE: src/${f.path} ===\n${f.content}`)
    .join('\n\n');

  const systemPrompt = `You are a senior QA engineer specialising in Playwright end-to-end tests.
You will be given the full TypeScript/React source code of a web application.
Your task is to produce a thorough, structured JSON test plan for Playwright E2E tests.

Rules:
- Group tests into suites by component/feature area
- Each suite targets ONE spec file
- Cover: happy paths, empty/disabled states, error states, and key interactions
- Test names must be concrete and descriptive (what the test verifies)
- Steps describe user actions (click, type, navigate, wait)
- Assertions describe what should be visible/true in the DOM
- Only describe things that are observable in the browser
- The "sourceFiles" array lists which src/ files are most relevant for that suite
  (used by the generator to pass relevant source when generating test code)
- Output ONLY valid JSON — no prose, no markdown, no explanation

Output schema:
{
  "suites": [
    {
      "file": "specs/chat.spec.ts",
      "component": "ChatView",
      "description": "Full chat message flow",
      "sourceFiles": ["components/ChatView.tsx", "components/MessageBubble.tsx", "context/ChatContext.tsx"],
      "tests": [
        {
          "name": "shows welcome screen before first message",
          "preconditions": ["app freshly loaded, no messages"],
          "steps": ["navigate to /"],
          "assertions": ["heading 'How can I help you today?' is visible", "no message bubbles present"]
        }
      ]
    }
  ]
}`;

  const userPrompt = `Here is the complete source code of the application:

${sourceContext}

Produce a complete Playwright test plan JSON covering all user-facing features.
Include suites for: welcome screen, chat flow, sidebar, topbar, and image generation.
Return ONLY the JSON object.`;

  console.log('🤖 Planner: Calling LLM to generate test plan...');
  const response = await callLLM(userPrompt, systemPrompt);

  console.log('📋 Planner: Parsing LLM response...');
  let plan: TestPlan;
  try {
    const raw = extractJSON(response);
    plan = validatePlan(raw);
  } catch (err) {
    console.error('❌ Failed to parse plan from LLM response');
    console.error('Raw response:\n', response);
    throw err;
  }

  const output = JSON.stringify(plan, null, 2);
  await writeFile(PLAN_OUT, output, 'utf-8');

  console.log(`✅ Planner: Wrote ${plan.suites.length} suites to plan.json`);
  for (const suite of plan.suites) {
    console.log(`   • ${suite.file} — ${suite.tests.length} tests`);
  }
}

main().catch((err) => {
  console.error('Planner failed:', err);
  process.exit(1);
});
