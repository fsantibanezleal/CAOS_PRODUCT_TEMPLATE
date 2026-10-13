// The landing (shell 0.13.0, docs/06_executive-view.md): the product opens on the Introduction's executive view, the App has its
// own route, and an old App link keeps its query string and hash (WB-008).
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
  it('the routes are the standard ones: the Introduction first, the App at /app', () => {
    expect(LANDING_ROUTE).toBe('/introduction');
    expect(APP_ROUTE).toBe('/app');
    expect(STANDARD_ROUTES.map((r) => r.path)).toEqual(['/introduction', '/app', '/methodology', '/implementation', '/experiments', '/benchmark']);
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

  it('adversarial: the root alone does not render the workbench', () => {
    expect(html('/')).not.toContain('data-workbench');
    expect(html('/nowhere')).not.toContain('data-workbench');
  });
});
