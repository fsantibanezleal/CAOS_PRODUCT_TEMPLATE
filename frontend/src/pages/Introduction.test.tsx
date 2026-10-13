// The Introduction's two views (problem-context-first.md): the shell's ExecutiveView first and open, the technical view second (WB-006).
import { CitationsProvider } from '@fasl-work/caos-app-shell';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import executive from '../../../content/executive.json';
import { CITATIONS } from '../content/citations';
import { Introduction, IntroductionPage } from './Introduction';

const page = (node: React.ReactNode) =>
  renderToString(
    <CitationsProvider items={CITATIONS}>
      <MemoryRouter>{node}</MemoryRouter>
    </CitationsProvider>,
  );

describe('the Introduction', () => {
  it('the Introduction opens on the executive view rendered from content/executive.json', () => {
    const html = page(<Introduction />);
    expect(html).toContain('data-executive-view');
    expect(html).toContain('data-executive-valid="true"');
    // the executive tab is the first and the selected one; the technical view is the second and is not rendered while closed
    const tabs = [...html.matchAll(/<button[^>]*role="tab"[^>]*aria-selected="(true|false)"[^>]*>([^<]*)</g)].map((m) => [m[1], m[2]]);
    expect(tabs).toEqual([
      ['true', 'Executive'],
      ['false', 'Technical'],
    ]);
    // the four sections, in the shell's order, and the data of the file
    for (const title of ['Industry &amp; Exec Tailoring', 'AI Transformation Story', '4Cs Positioning', 'Delivery &amp; Credibility']) expect(html).toContain(title);
    expect(html).toContain(executive.initiative.en);
    expect(html).not.toContain('What this product is');
  });

  it('adversarial: an invalid data file renders the error state and not a blank view', () => {
    const bad = JSON.parse(JSON.stringify(executive));
    delete bad.outcomes[1].proof.unit;
    const html = page(<IntroductionPage data={bad} />);
    expect(html).toContain('data-executive-valid="false"');
    expect(html).toContain('outcomes[1].proof.unit');
    expect(html).not.toContain('data-executive-valid="true"');
  });
});
