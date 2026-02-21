import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results.json' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'npm run dev',
      cwd: '../frontend-web',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'uvicorn backend.gateway.main:app --port 8000',
      cwd: '..',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
