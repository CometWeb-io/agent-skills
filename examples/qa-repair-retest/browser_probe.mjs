// Run by test_qa_runtime.py against an owned, disposable fixture only.
import assert from 'node:assert/strict';
import { quote } from './policy.mjs';

const { chromium } = await import(process.env.QA_PLAYWRIGHT_MODULE || 'playwright');
let input = '';
for await (const chunk of process.stdin) input += chunk;
const { url, token, otherToken, record } = JSON.parse(input);
assert.match(url, /^http:\/\/127\.0\.0\.1:\d+$/);
assert.match(record, /^[a-f0-9]{32}$/);
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const blocked = [];
  // A browser is permitted to request only this fixture's loopback origin.
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === url) return route.continue();
    blocked.push(route.request().url());
    return route.abort();
  });
  await context.addInitScript(token => sessionStorage.setItem('qa-demo-token', token), token);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${url}/?record=${record}`);
  await page.locator('#ready').waitFor();
  await page.locator('#billing').selectOption('annual');
  await page.locator('#calculate').click();
  const expected = quote(3, 4, true);
  assert.deepEqual(JSON.parse(await page.locator('#result').textContent()), expected);
  await page.locator('#save').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent.startsWith('Saved;'));
  await page.reload();
  await page.locator('#ready').waitFor();
  await page.locator('#load').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent.startsWith('{'));
  assert.deepEqual(JSON.parse(await page.locator('#saved').textContent()), expected);
  const blockedProbe = 'http://127.0.0.1:18765/outside-fixture';
  assert.equal(await page.evaluate(async url => {
    try { await fetch(url); return false; } catch { return true; }
  }, blockedProbe), true);
  assert.deepEqual(blocked, [blockedProbe]);
  const denied = await page.evaluate(async ({ token, record }) => {
    const statuses = [];
    for (const method of ['GET', 'DELETE']) {
      const result = await fetch(`/records/${record}`, { method, headers: { Authorization: `Bearer ${token}` } });
      statuses.push(result.status);
    }
    return statuses;
  }, { token: otherToken, record });
  assert.deepEqual(denied, [404, 404]);
  await page.locator('#clear').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent === 'No data');
  await page.reload();
  await page.locator('#ready').waitFor();
  await page.locator('#load').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent === 'No data');
  // Preserve the original dependency-free localStorage flow as a browser control.
  await page.goto(url);
  await page.locator('#ready').waitFor();
  await page.locator('#save').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent.startsWith('Saved;'));
  await page.reload();
  await page.locator('#ready').waitFor();
  await page.locator('#load').click();
  await page.waitForFunction(() => document.querySelector('#saved').textContent.startsWith('{'));
  assert.deepEqual(JSON.parse(await page.locator('#saved').textContent()), quote(3, 4));
  await page.locator('#clear').click();
  await page.locator('#load').click();
  assert.equal(await page.locator('#saved').textContent(), 'No data');
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ browser: browser.version(), save_reload_read: true,
    other_principal_read_delete: denied, cleanup_reload_read: true, local_storage_control: true, blocked_context_requests: blocked.length, page_errors: errors }));
} finally {
  await browser.close();
}
