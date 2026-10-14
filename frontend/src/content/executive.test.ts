// The example's executive view (CAOS_MANAGE conventions/problem-context-first.md, decided 2026-10-13): an executive frame of a
// problem space, general, never a client and never a pitch, valid against the shell's schema 2.0.0, with three illustrations
// that meet the standard the shell's gate measures in the page (WB-007).
import { readFileSync } from 'node:fs';
import { EXECUTIVE_SCHEMA_VERSION, FOUR_CS, validateExecutive } from '@fasl-work/caos-app-shell';
import { describe, expect, it } from 'vitest';
import executive from '../../../content/executive.json';
import pkg from '../../package.json';

const PUBLIC = new URL('../../public/', import.meta.url);
const NAMES = ['pain', 'situation', 'proposal'] as const;
const read = (name: (typeof NAMES)[number]) => readFileSync(new URL(executive.illustrations[name].file as string, PUBLIC), 'utf8');

const TOKEN = /^(none|currentColor|var\(--color-[a-z0-9-]+\))$/;

/** What is wrong with one illustration, in the terms of the gate: literal colours, charts, labels without a twin, no viewBox. */
export function svgProblems(svg: string): string[] {
  const out: string[] = [];
  if (!/viewBox="[^"]+"/.test(svg)) out.push('no viewBox');
  if (/<(img|image|script|foreignObject)\b/i.test(svg)) out.push('holds an img, image, script or foreignObject');
  if (/data-chart/i.test(svg)) out.push('declares a chart (data-chart)');
  if (/#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i.test(svg)) out.push('a literal colour');
  for (const m of svg.matchAll(/\b(fill|stroke|stop-color|flood-color)="([^"]*)"/g)) {
    if (!TOKEN.test(m[2])) out.push(`${m[1]}="${m[2]}" is not a theme token`);
  }
  for (const m of svg.matchAll(/style="([^"]*)"/g)) {
    if (/(fill|stroke|color)\s*:/.test(m[1])) out.push('a colour set in a style attribute');
  }
  const count = (lang: string) => [...svg.matchAll(new RegExp(`<text[^>]*data-lang="${lang}"`, 'g'))].length;
  if (count('en') < 5) out.push(`only ${count('en')} English label(s)`);
  if (count('en') !== count('es')) out.push(`${count('en')} English and ${count('es')} Spanish labels`);
  if (/<text(?![^>]*data-lang=)/.test(svg)) out.push('a label with no data-lang');
  if (/font-family/.test(svg)) out.push('a label sets its own font family');
  return [...new Set(out)];
}

/** The geometry of every rectangle, so two scenes can be compared for the setting they share. */
const rects = (svg: string) => new Set([...svg.matchAll(/<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"/g)].map((m) => m.slice(1, 5).join(',')));

const clone = () => JSON.parse(JSON.stringify(executive));

/** The floors of the standard (problem-context-first.md) as [min, max] counts of rows; the shell's schema holds the same numbers. */
const FLOORS: Record<string, [number, number]> = {
  headline_figures: [2, 3],
  'pain.paragraphs': [2, 3],
  'pain.bearers': [3, 5],
  'pain.figures': [2, 4],
  'pain.causes': [3, 5],
  'context.paragraphs': [1, 2],
  'context.forces': [3, 4],
  'context.evidence': [1, 4],
  'situation.roles': [3, 5],
  'situation.state_of_the_art': [3, 5],
  'trends.items': [3, 5],
  'proposal.paragraphs': [1, 2],
  'proposal.four_cs': [4, 4],
  'proposal.actions': [3, 6],
  'proposal.risks': [1, 4],
  'proposal.unknowns': [1, 4],
};

/** The source ids cited in each part of the file: 0 is the landing, 1 to 4 the sub-tabs that cite (the proposal cites none). */
function citations(): Array<{ source: string; tab: number }> {
  const out: Array<{ source: string; tab: number }> = [];
  const walk = (node: unknown, tab: number) => {
    if (Array.isArray(node)) node.forEach((n) => walk(n, tab));
    else if (node && typeof node === 'object') {
      for (const [k, v] of Object.entries(node)) {
        if (k === 'source' && typeof v === 'string') out.push({ source: v, tab });
        else walk(v, tab);
      }
    }
  };
  walk(executive.headline_figures, 0);
  walk(executive.pain, 1);
  walk(executive.context, 2);
  walk(executive.situation, 3);
  walk(executive.trends, 4);
  return out;
}

describe('the example executive view', () => {
  it('the shell is pinned exactly at 0.13.1, the release that carries schema 2.0.0, the landing and the App-first order', () => {
    expect(pkg.dependencies['@fasl-work/caos-app-shell']).toBe('0.13.1');
    expect(EXECUTIVE_SCHEMA_VERSION).toBe('2.0.0');
  });

  it('the example executive data is valid against schema 2.0.0', () => {
    expect(validateExecutive(executive)).toEqual([]);
    expect(FOUR_CS).toHaveLength(4);
    expect(executive.proposal.four_cs.map((r) => r.c.en)).toEqual(['Choice', 'Context', 'Cost', 'Control']);
  });

  it('the example meets every floor of the standard, in the sub-tabs and the landing', () => {
    const at = (path: string): unknown[] => path.split('.').reduce((node: any, key) => node[key], executive);
    for (const [path, [min, max]] of Object.entries(FLOORS)) {
      const n = at(path).length;
      expect(n, path).toBeGreaterThanOrEqual(min);
      expect(n, path).toBeLessThanOrEqual(max);
    }
    expect(executive.pain.figures.length + executive.context.evidence.length + executive.situation.state_of_the_art.length).toBeGreaterThanOrEqual(7);
  });

  it('every source is a titled https link that some figure or claim cites, and no sub-tab names more than six', () => {
    const cited = new Set(citations().map((c) => c.source));
    expect(executive.sources.length).toBeGreaterThanOrEqual(8);
    for (const s of executive.sources) {
      expect(s.url, s.id).toMatch(/^https:\/\/[^\s]+$/);
      expect(s.title.en.length, s.id).toBeGreaterThan(10);
      expect(s.title.es.length, s.id).toBeGreaterThan(10);
      expect(cited.has(s.id), s.id).toBe(true);
    }
    for (const tab of [1, 2, 3, 4]) {
      const ids = new Set(citations().filter((c) => c.tab === tab).map((c) => c.source));
      expect(ids.size, `sub-tab ${tab}`).toBeLessThanOrEqual(6);
    }
  });

  it('the example frames a problem space: no organisation, no client, no product and no call to act on a product', () => {
    const text = JSON.stringify({ ...executive, sources: undefined });
    expect(text).not.toMatch(/\b(NHS|Kaiser|Mayo|Clinic|Inc\.|Ltd|GmbH)\b/);
    expect(text).not.toMatch(/\b(our client|nuestro cliente|workbench|banco de trabajo|this product|este producto|the app|la app)\b/i);
    expect(text).not.toMatch(/\bSIR\b/);
  });

  it('the example illustrations use only theme tokens and carry both languages', () => {
    for (const name of NAMES) expect(svgProblems(read(name)), name).toEqual([]);
  });

  it('the illustrations are named pain, situation and proposal and are scenes of people and places, not charts', () => {
    for (const name of NAMES) {
      const svg = read(name);
      expect(executive.illustrations[name].file, name).toBe(`executive/${name}.svg`);
      expect(svg, name).not.toMatch(/<(polyline|image)\b|axis|tick/i);
      expect((svg.match(/<circle\b/g) ?? []).length, `${name} people`).toBeGreaterThanOrEqual(6);
      expect((svg.match(/<(rect|path|circle)\b/g) ?? []).length, `${name} detail`).toBeGreaterThanOrEqual(80);
    }
  });

  it('the pain and the proposal share the setting, so the change is visible between them', () => {
    const [pain, , proposal] = NAMES.map((n) => rects(read(n)));
    const shared = [...pain].filter((r) => proposal.has(r)).length / Math.min(pain.size, proposal.size);
    expect(shared).toBeGreaterThan(0.6);
  });

  it('adversarial: planted literal colours, charts, missing labels, long sentences and broken rules are refused', () => {
    const svg = read('pain');
    expect(svgProblems(svg.replace('var(--color-bad)', '#ff0000'))).toContain('a literal colour');
    expect(svgProblems(svg.replace('var(--color-bad)', 'red')).join()).toMatch(/not a theme token/);
    expect(svgProblems(svg.replace('<svg ', '<svg data-chart="line" '))).toContain('declares a chart (data-chart)');
    expect(svgProblems(svg.replace(/<text data-lang="es"[^>]*>[^<]*<\/text>/, ''))[0]).toMatch(/English and \d+ Spanish/);
    expect(svgProblems(svg.replace(/ viewBox="[^"]*"/, ''))).toContain('no viewBox');

    const long = clone();
    long.pain.key_message.en = Array.from({ length: 31 }, () => 'word').join(' ') + '.';
    expect(validateExecutive(long).map((p) => p.path)).toContain('pain.key_message.en');

    const uncited = clone();
    uncited.sources.push({ id: 'extra', title: { en: 'An extra source', es: 'Una fuente extra' }, url: 'https://example.org/x' });
    expect(validateExecutive(uncited).map((p) => p.message).join()).toMatch(/cited by no figure/);

    const nolink = clone();
    nolink.sources[0].url = 'http://example.org/insecure';
    expect(validateExecutive(nolink).length).toBeGreaterThan(0);

    const owner = clone();
    owner.proposal.actions[0].owner.en = 'A role nobody has';
    expect(validateExecutive(owner).map((p) => p.path)).toContain('proposal.actions[0].owner');

    const weights = clone();
    weights.pain.causes.forEach((c: { weight: number }) => (c.weight = 60));
    expect(validateExecutive(weights).map((p) => p.path)).toContain('pain.causes');

    const pitch = clone();
    pitch.proposal.actions[0].action.en = 'Buy the product now.';
    expect(validateExecutive(pitch).map((p) => p.message).join()).toMatch(/promotional/);

    const fourcs = clone();
    fourcs.proposal.four_cs.reverse();
    expect(validateExecutive(fourcs).map((p) => p.path).join()).toMatch(/four_cs/);
  });
});
