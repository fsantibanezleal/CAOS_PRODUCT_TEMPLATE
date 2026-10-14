// The landing and the header order (shell 0.13.1, docs/06_executive-view.md): the product opens on the Introduction's executive view,
// the App has its own route and is the leftmost tab, always (App, Introduction, Methodology, Implementation, Experiments, Benchmark),
// and an old App link keeps its query string and hash (WB-008).
import { APP_ROUTE, LANDING_ROUTE, STANDARD_ROUTES } from '@fasl-work/caos-app-shell';
import { readFileSync } from 'node:fs';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import { App } from './App';

const html = (path: string) =>
  renderToString(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );

const source = readFileSync(new URL('./App.tsx', import.meta.url), 'utf8');

describe('the landing', () => {
  it('the routes are the standard ones, the App first and at /app, the landing on the Introduction', () => {
    expect(LANDING_ROUTE).toBe('/introduction');
    expect(APP_ROUTE).toBe('/app');
    expect(STANDARD_ROUTES.map((r) => r.path)).toEqual(['/app', '/introduction', '/methodology', '/implementation', '/experiments', '/benchmark']);
  });

  it('the example header lists the six routes in the decided order, the App leftmost', () => {
    const page = html('/introduction');
    const order = ['/app', '/introduction', '/methodology', '/implementation', '/experiments', '/benchmark'];
    const hrefs = [...page.matchAll(/<a [^>]*href="(\/[a-z]*)(?:[?#][^"]*)?"/g)].map((m) => m[1]);
    const seen = order.map((p) => hrefs.indexOf(p));
    expect(seen.every((i) => i >= 0)).toBe(true);
    expect([...seen].sort((a, b) => a - b)).toEqual(seen);
  });

  it('the Introduction opens on the executive view', () => {
    const page = html('/introduction');
    expect(page).toContain('data-executive-view');
    expect(page).toContain('data-executive-valid="true"');
  });

  it('the App route renders the workbench and not the executive view', () => {
    const page = html('/app');
    expect(page).not.toContain('data-executive-view');
    expect(page).toContain('data-workbench');
  });

  it('the root and the catch-all render the shell landing, which opens the Introduction and keeps an old App link', () => {
    expect(source).toMatch(/<Route path="\/" element=\{<Landing \/>\} \/>/);
    expect(source).toMatch(/<Route path="\/app" element=\{<Workbench \/>\} \/>/);
    expect(source).toMatch(/<Route path="\*" element=\{<Landing \/>\} \/>/);
    expect(source).not.toMatch(/<Route path="\/" element=\{<Workbench/);
  });

  it('adversarial: the Introduction-first order of shell 0.13.0 is refused, the landing does not move the tabs', () => {
    expect(STANDARD_ROUTES[0].path).not.toBe(LANDING_ROUTE);
    expect(STANDARD_ROUTES[0].path).toBe(APP_ROUTE);
    expect(STANDARD_ROUTES.map((r) => r.path).indexOf(LANDING_ROUTE)).toBe(1);
  });

  it('the App route opens Focus mode: the workbench sets focus, and the rail head carries the Focus control (WB-014)', () => {
    const workbench = readFileSync(new URL('./workbench/Workbench.tsx', import.meta.url), 'utf8');
    expect(workbench).toMatch(/<CaseWorkbench[\s\S]*?\bfocus\b/);
    expect(html('/app')).toContain('data-focus-enter');
  });

  it('adversarial: the root alone does not render the workbench', () => {
    expect(html('/')).not.toContain('data-workbench');
    expect(html('/nowhere')).not.toContain('data-workbench');
  });
});
