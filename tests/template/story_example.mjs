// The template example's own story assertions (EX-016, EX-017), moved out of the base story check in 0.15.001: the SIR example's
// four views, its linked scene and panel selection, the shared day cursor across the system, phase and method views, the
// comparison measures with their computed values, the forward-Euler step, the exact return target of the exit and the phone
// callout band. A product removes this file with tests/template/ at instantiation; the generic story check every product runs
// is frontend/scripts/check_story_mode.mjs, and the shell's G21 measures the rest.
//   cd frontend && npm run build && node ../tests/template/story_example.mjs [origin]
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontend = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'frontend');
const { chromium } = createRequire(join(frontend, 'package.json'))('playwright');

let server;
let browser;
try {
  let base = process.argv[2] ? process.argv[2].replace(/\/+$/, '') : null;
  if (!base) {
    const { servePages } = createRequire(join(frontend, 'package.json'))('@fasl-work/caos-app-shell/serve');
    server = await servePages(join(frontend, 'dist'), process.env.VITE_BASE || '/', 0);
    base = server.url.replace(/\/+$/, '');
  }
  const errors = [];
  // the check talks only to a loopback server: no proxy resolution, which on a machine that auto-detects its proxy stalls the first
  // request of every new browser context about 21 s (CAOS_ChancaDEM 0.13.000, CAOS_MANAGE shell known defect 69)
  browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'] });
  const directMethod = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  directMethod.on('pageerror', (error) => errors.push(error.message));
  await directMethod.goto(`${base}/story/method?case=EX02_epidemic`, { waitUntil: 'domcontentloaded' });
  const methodSlider = directMethod.getByRole('slider', { name: 'Scrub Euler step' });
  const methodPanelStep = directMethod.locator('.template-story-evidence p').first().locator('strong');
  const methodCallout = directMethod.locator('[data-caos-callout="step"] strong');
  const methodDrawing = directMethod.locator('svg[data-euler-step] [data-linked-cursor-marker]');
  const assertMethodStep = async (expected) => {
    assert.equal(await methodSlider.inputValue(), expected, 'method slider selects the expected sample');
    assert.equal(await methodPanelStep.innerText(), expected, 'method prose reports the selected sample');
    assert.equal(await methodCallout.innerText(), `${expected} Euler updates`, 'method callout reports the selected sample');
    assert.equal(await methodDrawing.getAttribute('data-linked-cursor-position'), expected, 'Euler drawing uses the selected sample');
    assert.match(await methodSlider.locator('..').innerText(), new RegExp(`Euler step ${expected}/`), 'slider text displays the selected step index');
  };
  await assertMethodStep('0');
  await methodSlider.press('ArrowRight');
  await assertMethodStep('1');
  await methodSlider.press('End');
  await assertMethodStep(await methodSlider.getAttribute('max'));
  assert.equal(await directMethod.locator('[data-caos-callout="infections"] strong').innerText(), '0.00 people / step', 'the terminal sample has no next Euler update');
  await directMethod.close();
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
  const attackMeasure = desktop.getByRole('button', { name: 'Attack rate', exact: true });
  const peakMeasure = desktop.getByRole('button', { name: 'Peak infections', exact: true });
  assert.equal(await attackMeasure.getAttribute('aria-pressed'), 'true', 'attack rate is the initial comparison measure');
  await peakMeasure.click();
  assert.equal(await peakMeasure.getAttribute('aria-pressed'), 'true', 'the comparison measure selector changes the active measure');
  const peakStage = await desktop.locator('.template-story-stage').innerText();
  assert.match(peakStage, /Peak infections \(people\)/, 'the stage redraws peak infections with its own unit and scale');
  assert.match(peakStage, /27,345/, 'the peak-infections view shows the computed scenario value');
  await attackMeasure.click();
  const attackStage = await desktop.locator('.template-story-stage').innerText();
  assert.match(attackStage, /Attack rate by immunisation/, 'the attack-rate comparison can be restored');
  assert.match(attackStage, /92\.4\s*%/, 'the attack-rate view shows its computed percentage values');
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
  await desktop.waitForURL((url) => `${url.pathname}${url.search}` === `${new URL(base).pathname.replace(/\/+$/, '')}${from}`);

  const phone = await browser.newPage({ viewport: { width: 390, height: 844 } });
  phone.on('pageerror', (error) => errors.push(error.message));
  await phone.goto(`${base}/story/context?case=EX02_epidemic`, { waitUntil: 'domcontentloaded' });
  await phone.locator('[data-system-diagram]').waitFor({ state: 'visible' });
  await phone.evaluate(() => document.fonts.ready);
  await phone.waitForFunction(() => Number.parseFloat(document.querySelector('.template-story-drawing')?.style.paddingTop) > 0);
  const geometry = await phone.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
    stage: (() => { const r = document.querySelector('[data-stage]').getBoundingClientRect(); return { top: r.top, right: r.right, bottom: r.bottom }; })(),
    drawing: (() => { const r = document.querySelector('.template-story-drawing .caos-plot').getBoundingClientRect(); return { top: r.top, right: r.right, bottom: r.bottom }; })(),
    calls: [...document.querySelectorAll('[data-caos-callout]')].map((el) => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top, bottom: r.bottom }; }),
  }));
  assert.ok(geometry.width <= geometry.viewport + 1, 'phone story has no page-level horizontal overflow');
  assert.equal(geometry.calls.length, 3, 'the phone draws each sourced callout');
  assert.ok(geometry.calls.every((call) => call.left >= 0 && call.right <= geometry.viewport && call.bottom <= geometry.drawing.top + 1), 'phone callout band stays above the active drawing');
  // the shared day cursor on the phone: the context step's diagram carries its marker, and a scrub moves every linked marker to it
  assert.ok(await phone.locator('[data-story] [data-linked-cursor-marker]').count(), 'phone context step shows the shared day cursor');
  await phone.locator('[data-story] [data-linked-cursor]').first().evaluate((input) => {
    const next = String(Math.round(Number(input.min || 0) + (Number(input.max || 100) - Number(input.min || 0)) * 0.63));
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, next);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await phone.waitForTimeout(150);
  const scrub = await phone.evaluate(() => ({
    value: document.querySelector('[data-story] [data-linked-cursor]').value,
    markers: [...document.querySelectorAll('[data-story] [data-linked-cursor-marker]')].map((el) => el.getAttribute('data-linked-cursor-position')),
  }));
  assert.ok(scrub.markers.length && scrub.markers.every((position) => position === scrub.value), `phone scrub moves every linked marker to the cursor (${JSON.stringify(scrub)})`);
  assert.deepEqual(errors, [], 'no uncaught page errors');
  console.log('story_example: four distinct story views, linked scene/panel scrubbing, pause/exit state, desktop/phone callout clearance and the phone day cursor, and matching Method step readouts at direct load, ArrowRight and End passed.');
} finally {
  try {
    await browser?.close();
} finally {
    await server?.close();
  }
}
