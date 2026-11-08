import { LinkedViewProvider } from '@fasl-work/caos-app-shell';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import { simulate } from '../engine/sir';
import type { CaseData } from '../api/artifacts';
import type { Selection } from './model';
import { eulerStepAt, EulerStepView, PhasePlaneView, SystemDiagramView, ValidationView } from './views';

const params = { N: 1000, I0: 8, beta: .35, gamma: .1, days: 80 };
const data = { manifest: { case_id: 'phase-fixture', params } } as unknown as CaseData;
const selection: Selection = { data, beta: params.beta, gamma: params.gamma, coverage: 0, run: simulate(params) };
const render = (view: React.ReactNode) => renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LinkedViewProvider, null, view)));

describe('the example product visualization contract', () => {
  it('draws the SIR system with equation-derived directed flows and a scrub control', () => {
    const html = render(createElement(SystemDiagramView, { sel: selection }));
    expect(html).toContain('SIR compartments, infection and recovery flows');
    expect(html).toContain('data-stage');
    expect(html).toContain('data-linked-selection');
    expect(html).toContain('Scrub model day');
  });


  it('adversarial: draws the phase trajectory, analytic growth nullcline and linked day readout', () => {
    const html = render(createElement(PhasePlaneView, { sel: selection }));
    expect(html).toContain('S-I trajectory and growth nullcline');
    expect(html).toContain('data-phase-readout');
    expect(html).toContain('arrow keys');
  });

  it('adversarial: the Euler step matches the live update and keeps the population balanced', () => {
    const step = eulerStepAt(selection, 17);
    expect(step.dt).toBeCloseTo(.25, 12);
    expect(step.predicted.S).toBeCloseTo(step.observed.S, 8);
    expect(step.predicted.I).toBeCloseTo(step.observed.I, 8);
    expect(step.predicted.R).toBeCloseTo(step.observed.R, 8);
    expect(step.massBalance).toBeCloseTo(0, 8);
    const html = render(createElement(EulerStepView, { sel: selection }));
    expect(html).toContain('Forward Euler: one model step');
    expect(html).toContain('Euler step');
    expect(html).toContain('Scrub Euler step');
    expect(html).toContain('data-linked-cursor');
  });

  it('places the domain phase plane in the validation view before engine parity', () => {
    const html = render(createElement(ValidationView, { sel: selection }));
    expect(html).toContain('S-I phase plane');
    expect(html).toContain('Live against replay');
    expect(html).toContain('Final size');
  });
});
