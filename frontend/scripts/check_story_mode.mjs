import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { chromium } from 'playwright';

let serverProcess;
let base = process.argv[2] ? process.argv[2].replace(/\/+$/, '') : null;
if (!base) {
  const portServer = createServer();
  await new Promise((resolve, reject) => { portServer.once('error', reject); portServer.listen(0, '127.0.0.1', resolve); });
  const address = portServer.address();
  if (!address || typeof address === 'string') throw new Error('Could not allocate the story smoke server port');
  const port = address.port;
  await new Promise((resolve) => portServer.close(resolve));
  base = `http://127.0.0.1:${port}`;
  serverProcess = spawn(process.execPath, ['scripts/serve.mjs', '--host', '127.0.0.1', '--port', String(port)], { cwd: process.cwd(), stdio: 'ignore' });
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (serverProcess.exitCode !== null) throw new Error(`Story smoke server exited with ${serverProcess.exitCode}`);
    try { const response = await fetch(base); if (response.ok) { ready = true; break; } } catch { /* wait for startup */ }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  if (!ready) { serverProcess.kill(); throw new Error('Story smoke server did not become ready'); }
}
const errors = [];
const browser = await chromium.launch({ headless: true });
try {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  desktop.on('pageerror', (error) => errors.push(error.message));
  const from = '/app?case=EX02_epidemic&view=system&focus=1';
  await desktop.goto(`${base}/story/context?case=EX02_epidemic&from=${encodeURIComponent(from)}`, { waitUntil: 'domcontentloaded' });
  await desktop.locator('[data-story-step="context"]').waitFor({ state: 'visible', timeout: 15000 });
  assert.equal(await desktop.locator('[data-story-link]').count(), 4, 'four directly linked story steps, including the numerical method');
  assert.equal(await desktop.locator('[data-system-diagram]').count(), 1, 'context is a distinct system diagram');
  await desktop.locator('[data-system-diagram] g[role="button"]').first().click();
  assert.match(await desktop.locator('[data-linked-selection]').innerText(), /S/);
  assert.equal(await desktop.locator('[data-linked-view="panel"][data-linked-id="S"]').getAttribute('data-linked-selected'), 'true', 'scene selection updates the linked evidence panel');
  await desktop.locator('[data-linked-view="panel"][data-linked-id="R"]').click();
  assert.equal(await desktop.locator('[data-linked-view="scene"][data-linked-id="R"]').getAttribute('data-linked-selected'), 'true', 'panel selection updates the linked scene');
  const slider = desktop.getByRole('slider', { name: 'Scrub model day' });
  await slider.focus();
  await slider.press('ArrowRight');
  const sharedDay = await desktop.locator('.template-story-evidence').innerText();
  await desktop.locator('[data-story-link="phase"]').click();
  await desktop.locator('[data-phase-plane]').waitFor({ state: 'visible' });
  assert.equal((await desktop.locator('.template-story-evidence').innerText()).match(/linked day\s+([\d.,]+)/i)?.[1], sharedDay.match(/linked day\s+([\d.,]+)/i)?.[1], 'system scrub is retained by the phase view and panel');
  await desktop.locator('[data-phase-plane]').focus();
  await desktop.keyboard.press('ArrowRight');
  const scrubbedPanel = await desktop.locator('.template-story-evidence').innerText();
  assert.ok(scrubbedPanel.includes('S ='), 'panel readout follows phase-plane keyboard scrub');
  await desktop.locator('[data-story-link="decision"]').click();
  await desktop.locator('[data-story-step="decision"]').waitFor({ state: 'visible' });
  assert.ok(await desktop.locator('.template-story-stage .caos-plot').count(), 'decision uses a separate comparison view');
  await desktop.locator('[data-story-link="method"]').click();
  const eulerSvg = desktop.locator('svg[data-euler-step]').first();
  await eulerSvg.waitFor({ state: 'visible' });
  assert.match(await eulerSvg.getAttribute('aria-label') ?? '', /Euler/i, 'method step renders the actual numerical update');
  const play = desktop.locator('[data-story] button[aria-pressed]').first();
  await play.click();
  assert.equal(await play.getAttribute('aria-pressed'), 'true');
  await desktop.locator('[data-story-link="phase"]').click();
  assert.equal(await desktop.locator('[data-story] button[aria-pressed]').first().getAttribute('aria-pressed'), 'false', 'reader interaction pauses playback');
  await desktop.locator('.caos-story-exit').click();
  await desktop.waitForURL((url) => `${url.pathname}${url.search}` === from);

  const phone = await browser.newPage({ viewport: { width: 390, height: 844 } });
  phone.on('pageerror', (error) => errors.push(error.message));
  await phone.goto(`${base}/story/context?case=EX02_epidemic`, { waitUntil: 'domcontentloaded' });
  await phone.locator('[data-system-diagram]').waitFor({ state: 'visible' });
  const geometry = await phone.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
    stage: (() => { const r = document.querySelector('[data-stage]').getBoundingClientRect(); return { top: r.top, right: r.right, bottom: r.bottom }; })(),
    drawing: (() => { const r = document.querySelector('.template-story-drawing .caos-plot').getBoundingClientRect(); return { top: r.top, right: r.right, bottom: r.bottom }; })(),
    calls: [...document.querySelectorAll('[data-caos-callout]')].map((el) => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top, bottom: r.bottom }; }),
  }));
  assert.ok(geometry.width <= geometry.viewport + 1, 'phone story has no page-level horizontal overflow');
  assert.ok(geometry.calls.every((call) => call.left >= 0 && call.right <= geometry.viewport && call.bottom <= geometry.drawing.top + 1), 'phone callout band stays above the active drawing');
  assert.deepEqual(errors, [], 'no uncaught page errors');
  console.log('Four distinct story views, linked scene/panel scrubbing, pause/exit state, and desktop/phone callout clearance passed.');
} finally {
  await browser.close();
  serverProcess?.kill();
}
