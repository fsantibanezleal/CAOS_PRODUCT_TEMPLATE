// The views of the selected case. Each is a PlotCard with its lane and provenance, keyed by the selection it shows;
// a view whose data is not there yet declares data-state="loading" (the gate waits for it, a reader sees why).
import {
  BarChart,
  Equation,
  PlotCard,
  SubTabs,
  Stage,
  Verdict,
  formatNumber,
  pick,
  useShellLang,
  useWorkbenchState,
  useLinkedView,
  ViewsRow,
  type BiText,
} from '@fasl-work/caos-app-shell';
import { UPlotChart } from '@fasl-work/caos-app-shell/chart';
import { createContext, useContext, useMemo, type PointerEvent, type KeyboardEvent, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router';
import { atTimes, finalSize, simulate } from '../engine/sir';
import type { Text } from '../lib/contract.types';
import { ReadinessNote } from '../readiness/ReadinessNote';
import { COVERAGE, type Selection } from './model';

/** The reason the selected case is not available yet, when the readiness document says so; null otherwise. */
export const UnavailableContext = createContext<Text | null>(null);

function Pending({ label }: { label: BiText }) {
  const lang = useShellLang();
  const reason = useContext(UnavailableContext);
  // A case the readiness document lists as absent says so, with the reason: never an empty chart, never a spinner.
  if (reason) {
    return (
      <p className="caos-pending" data-state="unavailable">
        {reason[lang]}
      </p>
    );
  }
  return (
    <p className="caos-pending" data-state="loading">
      {pick(label, lang)}
    </p>
  );
}

/** The rows every view of the workbench consumes. The rail is at its measured height (ADR-0071 rule 6), so the note
 * sits in the open view: the first group (Dynamics) and the write-up (Context). */
const CASE_ROWS = ['case-index', 'case-manifest', 'trace'];

/** The readiness note above a filling view: the note takes its own line and the view the height that is left, so a
 * note never pushes the chart past its card (a note beside a `fill` chart clipped its legend). */
function NotedFill({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <ReadinessNote ids={CASE_ROWS} />
      <div style={{ flex: '1 1 0', minHeight: 0, position: 'relative' }}>{children}</div>
    </div>
  );
}

const LOADING: BiText = { en: 'Loading the case artifacts', es: 'Cargando los artefactos del caso' };

/** S, I and R of the live run, with the replay trace of the case dashed under the live infected curve. */
export function DynamicsView({ sel }: { sel: Selection | null }) {
  const stateKey = useWorkbenchState()?.stateKey;
  const series = useMemo(() => {
    if (!sel) return null;
    const at = atTimes(sel.run, sel.data.trace.t);
    return { t: sel.data.trace.t, ...at, replayI: sel.data.trace.I };
  }, [sel]);
  return (
    <PlotCard
      fill
      title={{ en: 'Susceptible, infected and recovered over time', es: 'Susceptibles, contagiados y recuperados en el tiempo' }}
      lane="live"
      provenance="synthetic"
      dataKey={stateKey}
      note={{ en: 'Solid: the live run with the rail values. Dashed: the committed replay of the case.', es: 'Continua: la corrida en vivo con los valores del panel. Segmentada: la reproducción comprometida del caso.' }}
    >
      <NotedFill>
      {series ? (
        <UPlotChart
          title={{ en: 'SIR trajectory', es: 'Trayectoria SIR' }}
          height="fill"
          x={{ values: series.t, label: { en: 'Day', es: 'Día' }, unit: 'd' }}
          y={{ label: { en: 'People', es: 'Personas' } }}
          series={[
            { label: { en: 'Susceptible', es: 'Susceptibles' }, values: series.S, color: '--color-accent' },
            { label: { en: 'Infected', es: 'Contagiados' }, values: series.I, color: '--color-bad' },
            { label: { en: 'Recovered', es: 'Recuperados' }, values: series.R, color: '--color-good' },
            { label: { en: 'Infected (replay)', es: 'Contagiados (reproducción)' }, values: series.replayI, color: '--color-fg-subtle', dash: [6, 4], width: 1.5 },
          ]}
          marks={sel && sel.run.peakI > sel.data.manifest.params.I0 ? [{ x: sel.run.tPeak, label: { en: 'peak', es: 'pico' } }] : []}
        />
      ) : (
        <Pending label={LOADING} />
      )}
      </NotedFill>
    </PlotCard>
  );
}

/** Live against replay: the parity of the two engines, and the scientific check of the final size. */
export function ValidationView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  return (
    <SubTabs
      ariaLabel={pick({ en: 'Validation views', es: 'Vistas de validación' }, lang)}
      tabs={[
        { id: 'phase-plane', label: pick({ en: 'S-I phase plane', es: 'Plano de fase S-I' }, lang), content: <PhasePlaneView sel={sel} /> },
        { id: 'parity', label: pick({ en: 'Live against replay', es: 'En vivo contra reproducción' }, lang), content: <ParityView sel={sel} /> },
        { id: 'final-size', label: pick({ en: 'Final size', es: 'Tamaño final' }, lang), content: <FinalSizeView sel={sel} /> },
      ]}
    />
  );
}

/** The model's authored 2D system map: compartments, equation-derived flows and a scrub-linked time slice. */
export function SystemDiagramView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  const sharedCursor = useLinkedView((state) => state.cursor);
  const scrub = useLinkedView((state) => state.scrub);
  const linkedSelection = useLinkedView((state) => state.selectedId);
  const select = useLinkedView((state) => state.select);
  if (!sel) return <Pending label={LOADING} />;
  const peakIndex = sel.run.I.reduce((best, value, index) => value > sel.run.I[best]! ? index : best, 0);
  const index = Math.max(0, Math.min(sel.run.t.length - 1, sharedCursor ?? peakIndex));
  const S = sel.run.S[index]!, I = sel.run.I[index]!, R = sel.run.R[index]!;
  const infections = sel.beta * S * I / sel.data.manifest.params.N;
  const recoveries = sel.gamma * I;
  const maxFlow = Math.max(infections, recoveries, 1);
  const t = (en: string, es: string) => lang === 'es' ? es : en;
  const node = (x: number, name: string, symbol: string, value: number, detail: string, tone: string) => <g key={symbol} role="button" tabIndex={0} aria-label={`${name} ${formatNumber(value, lang, { decimals: 0 })}`} aria-pressed={(linkedSelection ?? 'I') === symbol} data-linked-id={symbol} data-linked-view="scene" data-linked-selected={(linkedSelection ?? 'I') === symbol ? 'true' : 'false'} onClick={() => select(symbol, 'scene')} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(symbol, 'scene'); } }} style={{ cursor: 'pointer' }}>
    <rect x={x} y="164" width="230" height="176" rx="18" fill={(linkedSelection ?? 'I') === symbol ? 'var(--color-accent-soft)' : 'var(--color-surface)'} stroke={(linkedSelection ?? 'I') === symbol ? tone : 'var(--color-border)'} strokeWidth={(linkedSelection ?? 'I') === symbol ? 3 : 2}/>
    <rect x={x} y="164" width="7" height="176" rx="3" fill={tone}/>
    <text x={x + 24} y="204" fill="var(--color-fg-faint)" fontSize="13" fontWeight="700" letterSpacing="1.2">{symbol}</text>
    <text x={x + 24} y="239" fill="var(--color-fg)" fontSize="21" fontWeight="650">{name}</text>
    <text x={x + 24} y="286" fill="var(--color-fg)" fontSize="29" fontFamily="var(--font-mono)">{formatNumber(value, lang, { decimals: 0 })}</text>
    <text x={x + 24} y="316" fill="var(--color-fg-subtle)" fontSize="13">{detail}</text>
  </g>;
  return <PlotCard fill title={{ en: 'SIR system and directed state transitions', es: 'Sistema SIR y transiciones de estado dirigidas' }} lane="live" provenance="synthetic">
    <Stage label={{ en: 'SIR compartments, infection and recovery flows', es: 'Compartimentos SIR, flujos de contagio y recuperación' }}>
      {({ width, height }) => width < 520 ? <svg viewBox="0 0 360 410" width={width} height={height} role="group" aria-label={t('Vertical SIR process map and live flows', 'Mapa vertical del proceso SIR y flujos en vivo')} data-system-diagram="" data-layout="mobile">
        <defs><marker id="sir-mobile-infection-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L0,8 L8,4 z" fill="var(--color-accent)"/></marker><marker id="sir-mobile-recovery-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L0,8 L8,4 z" fill="var(--color-good)"/></marker></defs>
        <text x="180" y="20" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="11">{t('Closed population · no external inflow', 'Población cerrada · sin ingreso externo')}</text>
        {([['S', t('Susceptible', 'Susceptibles'), S, 'var(--color-accent)'], ['I', t('Infectious', 'Contagiados'), I, 'var(--color-bad)'], ['R', t('Recovered', 'Recuperados'), R, 'var(--color-good)']] as const).map(([symbol, name, value, tone], row) => {
          const y = 35 + row * 113;
          const chosen = (linkedSelection ?? 'I') === symbol;
          const fraction = value / sel.data.manifest.params.N * 100;
          return <g key={symbol} role="button" tabIndex={0} aria-label={`${name} ${formatNumber(value, lang, { decimals: 0 })}`} aria-pressed={chosen} data-linked-id={symbol} data-linked-view="scene" data-linked-selected={chosen ? 'true' : 'false'} onClick={() => select(symbol, 'scene')} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(symbol, 'scene'); } }} style={{ cursor: 'pointer' }}>
            <rect x="24" y={y} width="312" height="70" rx="12" fill={chosen ? 'var(--color-accent-soft)' : 'var(--color-surface)'} stroke={chosen ? tone : 'var(--color-border)'} strokeWidth={chosen ? 2.5 : 1.5}/><rect x="24" y={y} width="6" height="70" rx="3" fill={tone}/>
            <text x="43" y={y + 23} fill="var(--color-fg-faint)" fontSize="11" fontWeight="700">{symbol}</text><text x="65" y={y + 24} fill="var(--color-fg)" fontSize="15" fontWeight="650">{name}</text><text x="65" y={y + 48} fill="var(--color-fg-subtle)" fontSize="11">{formatNumber(fraction, lang, { decimals: 2 })}% {t('of population', 'de población')}</text><text x="319" y={y + 38} textAnchor="end" fill="var(--color-fg)" fontSize="18" fontFamily="var(--font-mono)">{formatNumber(value, lang, { decimals: 0 })}</text>
          </g>;
        })}
        <line x1="320" y1="106" x2="320" y2="125" stroke="var(--color-accent)" strokeWidth="3" markerEnd="url(#sir-mobile-infection-arrow)"/><text x="180" y="119" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="10">{t('INFECTION', 'CONTAGIO')} · βSI/N = {formatNumber(infections, lang, { decimals: 1 })} {t('people/day', 'personas/día')}</text>
        <line x1="320" y1="219" x2="320" y2="238" stroke="var(--color-good)" strokeWidth="3" markerEnd="url(#sir-mobile-recovery-arrow)"/><text x="180" y="232" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="10">{t('RECOVERY', 'RECUPERACIÓN')} · γI = {formatNumber(recoveries, lang, { decimals: 1 })} {t('people/day', 'personas/día')}</text>
        <text x="180" y="381" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="12">N = S + I + R = {formatNumber(S + I + R, lang, { decimals: 0 })} {t('people', 'personas')}</text><text x="180" y="400" textAnchor="middle" fill="var(--color-fg-faint)" fontSize="10">{t('Flows at selected day', 'Flujos en el día seleccionado')}</text>
      </svg> : <svg viewBox="0 0 960 520" width={width} height={height} role="img" aria-label={t('SIR compartments and equation-derived flows at the selected day', 'Compartimentos SIR y flujos derivados de las ecuaciones en el día seleccionado')} data-system-diagram="" data-layout="desktop">
        <title>{t('SIR system diagram', 'Diagrama del sistema SIR')}</title>
        <defs><marker id="sir-infection-arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" fill="var(--color-accent)"/></marker><marker id="sir-recovery-arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" fill="var(--color-good)"/></marker></defs>
        <text x="480" y="66" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="14">{t('Closed population · no births, deaths or external inflow', 'Población cerrada · sin nacimientos, muertes ni ingreso externo')}</text>
        {node(46, t('Susceptible', 'Susceptibles'), 'S', S, `${formatNumber(S / sel.data.manifest.params.N * 100, lang, { decimals: 1 })}% ${t('of N', 'de N')}`, 'var(--color-accent)')}
        {node(365, t('Infectious', 'Contagiados'), 'I', I, `${formatNumber(I / sel.data.manifest.params.N * 100, lang, { decimals: 2 })}% ${t('of N', 'de N')}`, 'var(--color-bad)')}
        {node(684, t('Recovered', 'Recuperados'), 'R', R, `${formatNumber(R / sel.data.manifest.params.N * 100, lang, { decimals: 1 })}% ${t('of N', 'de N')}`, 'var(--color-good)')}
        <path d="M276 205 C310 155 332 155 364 205" fill="none" stroke="var(--color-accent)" strokeWidth={Math.max(2.5, 9 * infections / maxFlow)} markerEnd="url(#sir-infection-arrow)"/>
        <text x="320" y="136" textAnchor="middle" fill="var(--color-fg)" fontSize="13" fontWeight="650">{t('INFECTION', 'CONTAGIO')}</text>
        <text x="320" y="156" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="12">βSI/N = {formatNumber(infections, lang, { decimals: 1 })} {t('people/day', 'personas/día')}</text>
        <path d="M595 205 C628 155 650 155 683 205" fill="none" stroke="var(--color-good)" strokeWidth={Math.max(2.5, 9 * recoveries / maxFlow)} markerEnd="url(#sir-recovery-arrow)"/>
        <text x="639" y="136" textAnchor="middle" fill="var(--color-fg)" fontSize="13" fontWeight="650">{t('RECOVERY', 'RECUPERACIÓN')}</text>
        <text x="639" y="156" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="12">γI = {formatNumber(recoveries, lang, { decimals: 1 })} {t('people/day', 'personas/día')}</text>
        <text x="145" y="390" fill="var(--color-fg-subtle)" fontSize="12">{t('TIME SLICE', 'CORTE TEMPORAL')}</text>
        <path d="M145 408 H815" stroke="var(--color-border)" strokeWidth="2"/>
        <circle cx={145 + (index / Math.max(1, sel.run.t.length - 1)) * 670} cy="408" r="8" fill="var(--color-accent)" stroke="var(--color-bg)" strokeWidth="3" data-linked-cursor-marker="" data-linked-cursor-position={index}/>
        <text x="145" y="434" fill="var(--color-fg-subtle)" fontSize="12">0 d</text><text x="815" y="434" textAnchor="end" fill="var(--color-fg-subtle)" fontSize="12">{formatNumber(sel.run.t.at(-1) ?? 0, lang, { decimals: 0 })} d</text>
        <text x="480" y="462" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="14">N = S + I + R = {formatNumber(S + I + R, lang, { decimals: 0 })} {t('people', 'personas')}</text>
        <text x="480" y="487" textAnchor="middle" fill="var(--color-fg-faint)" fontSize="12">{t('Flows are evaluated from the live model at the selected day.', 'Los flujos se evalúan con el modelo en vivo en el día seleccionado.')}</text>
      </svg>}
    </Stage>
    <label className="caos-system-scrub">{t('Day', 'Día')} <strong>{formatNumber(sel.run.t[index]!, lang, { decimals: 2 })}</strong><input aria-label={t('Scrub model day', 'Mover día del modelo')} type="range" min={0} max={sel.run.t.length - 1} value={index} data-linked-cursor="" onChange={(event) => scrub(Number(event.currentTarget.value))}/></label>
    <p className="caos-system-selection" aria-live="polite" data-linked-selection={linkedSelection ?? 'I'}>{t('Selected state', 'Estado seleccionado')}: <strong>{linkedSelection ?? 'I'}</strong> · {linkedSelection === 'S' ? `dS/dt = −βSI/N = −${formatNumber(infections, lang, { decimals: 1 })}` : linkedSelection === 'R' ? `dR/dt = γI = ${formatNumber(recoveries, lang, { decimals: 1 })}` : `dI/dt = βSI/N − γI = ${formatNumber(infections - recoveries, lang, { decimals: 1 })}`} {t('people/day', 'personas/día')}</p>
  </PlotCard>;
}

/** Compute the exact Euler prediction and observed next sample from the selected live run. */
export function eulerStepAt(sel: Selection, index: number) {
  const i = Math.max(0, Math.min(sel.run.t.length - 1, Math.trunc(index)));
  const dt = i < sel.run.t.length - 1 ? sel.run.t[i + 1]! - sel.run.t[i]! : 0;
  const N = sel.data.manifest.params.N;
  const before = { S: sel.run.S[i]!, I: sel.run.I[i]!, R: sel.run.R[i]! };
  const derivative = { S: -sel.beta * before.S * before.I / N, I: sel.beta * before.S * before.I / N - sel.gamma * before.I, R: sel.gamma * before.I };
  const predicted = { S: before.S + dt * derivative.S, I: before.I + dt * derivative.I, R: before.R + dt * derivative.R };
  const observed = i < sel.run.t.length - 1 ? { S: sel.run.S[i + 1]!, I: sel.run.I[i + 1]!, R: sel.run.R[i + 1]! } : before;
  const residual = { S: observed.S - predicted.S, I: observed.I - predicted.I, R: observed.R - predicted.R };
  return { index: i, dt, before, derivative, predicted, observed, residual, massBalance: observed.S + observed.I + observed.R - N };
}

/** V5: expose the actual forward-Euler update at the shared cursor; values are the same live run as V1/V3/V4. */
export function EulerStepView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  const cursor = useLinkedView((state) => state.cursor);
  const scrub = useLinkedView((state) => state.scrub);
  if (!sel) return <Pending label={LOADING} />;
  const step = eulerStepAt(sel, cursor ?? 0);
  const { index, dt, before, observed: next, massBalance: residual } = step;
  const nextIndex = Math.min(sel.run.t.length - 1, index + 1);
  const { S, I, R } = before;
  const infections = dt ? sel.beta * S * I / sel.data.manifest.params.N * dt : 0;
  const recoveries = dt ? sel.gamma * I * dt : 0;
  const t = (en: string, es: string) => lang === 'es' ? es : en;
  const compartments = [
    { key: 'S', label: t('Susceptible', 'Susceptibles'), value: S, after: next.S, x: 90, tone: 'var(--color-step-1)' },
    { key: 'I', label: t('Infectious', 'Contagiados'), value: I, after: next.I, x: 390, tone: 'var(--color-bad)' },
    { key: 'R', label: t('Recovered', 'Recuperados'), value: R, after: next.R, x: 690, tone: 'var(--color-good)' },
  ];
  return <PlotCard fill title={{ en: 'Forward Euler: one model step', es: 'Euler explícito: un paso del modelo' }} lane="live" provenance="synthetic">
    <Stage label={{ en: 'One quarter-day update of all three SIR compartments', es: 'Actualización de un cuarto de día de los tres compartimentos SIR' }}>
      {({ width, height }) => width < 520 ? <svg viewBox="0 0 360 460" width={width} height={height} role="group" aria-label={t('Vertical forward-Euler update for the selected model step', 'Actualización vertical de Euler explícito para el paso seleccionado')} data-euler-step="" data-layout="mobile">
        <text x="180" y="24" textAnchor="middle" fill="var(--color-fg)" fontSize="13" fontWeight="700">t = {formatNumber(sel.run.t[index]!, lang, { decimals: 2 })} d → {formatNumber(sel.run.t[nextIndex]!, lang, { decimals: 2 })} d · Δt = {formatNumber(dt, lang, { decimals: 2 })} d</text>
        {compartments.map((c, row) => { const y = 42 + row * 78; return <g key={c.key}><rect x="22" y={y} width="316" height="64" rx="10" fill="var(--color-surface)" stroke={c.tone} strokeWidth="1.5"/><text x="38" y={y + 23} fill="var(--color-fg)" fontSize="13" fontWeight="700">{c.key} · {c.label}</text><text x="38" y={y + 47} fill="var(--color-fg-subtle)" fontSize="11">{formatNumber(c.value, lang, { decimals: 1 })} → {formatNumber(c.after, lang, { decimals: 1 })} {t('people', 'personas')}</text></g>; })}
        <text x="180" y="286" textAnchor="middle" fill="var(--color-accent)" fontSize="11">S → I · βSIΔt/N = {formatNumber(infections, lang, { decimals: 1 })} {t('new cases', 'contagios nuevos')}</text><text x="180" y="307" textAnchor="middle" fill="var(--color-good)" fontSize="11">I → R · γIΔt = {formatNumber(recoveries, lang, { decimals: 1 })} {t('recoveries', 'recuperaciones')}</text>
        <text x="180" y="346" textAnchor="middle" fill="var(--color-fg)" fontFamily="var(--font-mono)" fontSize="10">Sₖ₊₁ = Sₖ − βSₖIₖΔt/N</text><text x="180" y="364" textAnchor="middle" fill="var(--color-fg)" fontFamily="var(--font-mono)" fontSize="10">Iₖ₊₁ = Iₖ + (βSₖIₖ/N − γIₖ)Δt</text><text x="180" y="382" textAnchor="middle" fill="var(--color-fg)" fontFamily="var(--font-mono)" fontSize="10">Rₖ₊₁ = Rₖ + γIₖΔt</text>
        <text x="180" y="411" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="11">{t('population balance residual', 'residuo de balance poblacional')} = {formatNumber(residual, lang, { decimals: 6 })} {t('people', 'personas')}</text><line x1="35" x2="325" y1="438" y2="438" stroke="var(--color-border)" strokeWidth="2"/><circle cx={35 + index / Math.max(1, sel.run.t.length - 1) * 290} cy="438" r="6" fill="var(--color-accent)" data-linked-cursor-marker="" data-linked-cursor-position={index}/>
      </svg> : <svg viewBox="0 0 980 510" width={width} height={height} role="img" aria-label={t('Forward Euler update from the selected model step', 'Actualización de Euler explícito desde el paso seleccionado')} data-euler-step="" data-layout="desktop">
        <text x="490" y="34" textAnchor="middle" fill="var(--color-fg)" fontSize="18" fontWeight="700">t = {formatNumber(sel.run.t[index]!, lang, { decimals: 2 })} d → {formatNumber(sel.run.t[Math.min(sel.run.t.length - 1, index + 1)]!, lang, { decimals: 2 })} d · Δt = {formatNumber(dt, lang, { decimals: 2 })} d</text>
        {compartments.map((c) => <g key={c.key}><rect x={c.x} y="118" width="200" height="170" rx="16" fill="var(--color-surface)" stroke={c.tone} strokeWidth="2"/><text x={c.x + 18} y="151" fill="var(--color-fg-subtle)" fontSize="14">{c.key} · {c.label}</text><text x={c.x + 18} y="204" fill="var(--color-fg)" fontSize="25" fontFamily="var(--font-mono)">{formatNumber(c.value, lang, { decimals: 1 })}</text><text x={c.x + 18} y="233" fill="var(--color-fg-faint)" fontSize="13">{t('after step', 'después del paso')}</text><text x={c.x + 18} y="263" fill="var(--color-fg)" fontSize="19" fontFamily="var(--font-mono)">{formatNumber(c.after, lang, { decimals: 1 })}</text></g>)}
        <path d="M290 180 H380" fill="none" stroke="var(--color-accent)" strokeWidth="3" markerEnd="url(#euler-arrow)"/><text x="335" y="160" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="12">−{formatNumber(infections, lang, { decimals: 1 })} S → I</text>
        <path d="M590 230 H680" fill="none" stroke="var(--color-good)" strokeWidth="3" markerEnd="url(#euler-arrow)"/><text x="635" y="210" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="12">−{formatNumber(recoveries, lang, { decimals: 1 })} I → R</text>
        <defs><marker id="euler-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="var(--color-accent)"/></marker></defs>
        <text x="490" y="348" textAnchor="middle" fill="var(--color-fg)" fontSize="15" fontFamily="var(--font-mono)">Sₖ₊₁ = Sₖ − βSₖIₖΔt/N · Iₖ₊₁ = Iₖ + (βSₖIₖ/N − γIₖ)Δt · Rₖ₊₁ = Rₖ + γIₖΔt</text>
        <text x="490" y="384" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="14">{t('population balance residual', 'residuo de balance poblacional')} = {formatNumber(residual, lang, { decimals: 6 })} {t('people', 'personas')}</text>
        <line x1="90" x2="890" y1="435" y2="435" stroke="var(--color-border)" strokeWidth="3"/><circle cx={90 + index / Math.max(1, sel.run.t.length - 1) * 800} cy="435" r="9" fill="var(--color-accent)" data-linked-cursor-marker="" data-linked-cursor-position={index}/>
      </svg>}
    </Stage>
    <label className="caos-system-scrub" data-euler-step="" data-linked-cursor-marker="" data-linked-cursor-position={index}>{t('Euler step', 'Paso de Euler')} {index + 1}/{sel.run.t.length - 1}<input aria-label={t('Scrub Euler step', 'Mover paso de Euler')} type="range" min={0} max={sel.run.t.length - 1} value={index} data-linked-cursor="" onChange={(event) => scrub(Number(event.currentTarget.value))}/></label>
    <p className="caos-plot-note">{t('population balance residual', 'residuo de balance poblacional')}: {formatNumber(residual, lang, { decimals: 6 })} {t('people', 'personas')} · {t('The before/after values come from the same live forward-Euler run.', 'Los valores antes/después vienen de la misma corrida Euler explícita en vivo.')}</p>
  </PlotCard>;
}

/** A domain view of the SIR vector field: trajectory, analytically derived growth nullcline and a linked day readout. */
export function PhasePlaneView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  const sharedCursor = useLinkedView((state) => state.cursor);
  const scrub = useLinkedView((state) => state.scrub);
  if (!sel) return <Pending label={LOADING} />;
  const n = sel.data.manifest.params.N;
  const peakIndex = sel.run.I.reduce((best, value, index, values) => value > values[best]! ? index : best, 0);
  const index = Math.max(0, Math.min(sel.run.t.length - 1, sharedCursor ?? peakIndex));
  const current = { s: sel.run.S[index]! / n, i: sel.run.I[index]! / n, day: sel.run.t[index]! };
  const t = (en: string, es: string) => lang === 'es' ? es : en;
  const nearest = (event: PointerEvent<SVGSVGElement> | KeyboardEvent<SVGSVGElement>) => {
    if ('key' in event) {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight' && event.key !== 'Home' && event.key !== 'End') return;
      event.preventDefault();
      scrub(event.key === 'Home' ? 0 : event.key === 'End' ? sel.run.t.length - 1 : Math.max(0, Math.min(sel.run.t.length - 1, index + (event.key === 'ArrowLeft' ? -1 : 1))));
      return;
    }
    const r = event.currentTarget.getBoundingClientRect();
    const px = ((event.clientX - r.left) / r.width) * 960;
    const py = ((event.clientY - r.top) / r.height) * 520;
    const left = 74, right = 928, top = 24, bottom = 458;
    const maxI = Math.max(...sel.run.I) / n || 1;
    let best = 0, bestDistance = Infinity;
    for (let k = 0; k < sel.run.t.length; k += 1) {
      const x = left + (sel.run.S[k]! / n) * (right - left);
      const y = bottom - (sel.run.I[k]! / n / maxI) * (bottom - top);
      const distance = (x - px) ** 2 + (y - py) ** 2;
      if (distance < bestDistance) { best = k; bestDistance = distance; }
    }
    scrub(best);
  };
  return <PlotCard fill title={{ en: 'Susceptible–infected phase plane', es: 'Plano de fase susceptibles–contagiados' }} lane="live" provenance="synthetic">
    <Stage label={{ en: 'S-I trajectory and growth nullcline', es: 'Trayectoria S-I y nulclina de crecimiento' }}>
      {({ width, height }) => {
        const maxI = Math.max(...sel.run.I) / n || 1;
        const x = (s: number) => 90 + s * 838;
        const y = (i: number) => 458 - (i / maxI) * 434;
        const path = sel.run.S.map((value, k) => `${k ? 'L' : 'M'}${x(value / n).toFixed(2)},${y(sel.run.I[k]! / n).toFixed(2)}`).join(' ');
        const threshold = sel.gamma / sel.beta;
        const thresholdX = x(Math.min(1, threshold));
        const px = x(current.s), py = y(current.i);
        return <svg viewBox="0 0 960 520" width={width} height={height} role="img" aria-label={t('S-I phase plane. The vertical nullcline marks when infections stop growing.', 'Plano de fase S-I. La nulclina vertical marca cuándo dejan de crecer los contagios.')} tabIndex={0} onPointerMove={nearest} onFocus={() => scrub(peakIndex)} onKeyDown={nearest} data-phase-plane="">
          <title>{t('S-I phase plane with live trajectory and threshold', 'Plano de fase S-I con trayectoria en vivo y umbral')}</title>
          {[0, .25, .5, .75, 1].map((tick) => <g key={`x${tick}`}><line x1={x(tick)} x2={x(tick)} y1="24" y2="458" stroke="var(--color-border)"/><text x={x(tick)} y="482" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="13">{formatNumber(tick * 100, lang, { decimals: 0 })}%</text></g>)}
          {[0, .25, .5, .75, 1].map((tick) => <g key={`y${tick}`}><line x1="90" x2="928" y1={y(tick * maxI)} y2={y(tick * maxI)} stroke="var(--color-border)"/><text x="82" y={y(tick * maxI) + 4} textAnchor="end" fill="var(--color-fg-subtle)" fontSize="13">{formatNumber(tick * maxI * 100, lang, { decimals: 1 })}%</text></g>)}
          <line x1={thresholdX} x2={thresholdX} y1="24" y2="458" stroke="var(--color-warn)" strokeWidth="2" strokeDasharray="7 5"/><text x={threshold > 1 ? thresholdX - 7 : thresholdX + 7} y="42" textAnchor={threshold > 1 ? 'end' : 'start'} fill="var(--color-warn)" fontSize="13">{threshold > 1 ? 'S/N = γ/β (>100%)' : 'S/N = γ/β'}</text>
          <path d={path} fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinejoin="round"/>
          <circle cx={px} cy={py} r="8" fill="var(--color-bad)" stroke="var(--color-bg)" strokeWidth="3" data-linked-cursor-marker="" data-linked-cursor-position={index}/>
          <text x="500" y="512" textAnchor="middle" fill="var(--color-fg)" fontSize="14">{t('Susceptible fraction S/N', 'Fracción susceptible S/N')}</text>
          <text transform="translate(18 242) rotate(-90)" textAnchor="middle" fill="var(--color-fg)" fontSize="14">{t('Infected fraction I/N', 'Fracción contagiada I/N')}</text>
        </svg>;
      }}
    </Stage>
    <p className="caos-phase-readout" aria-live="polite" data-phase-readout="">{t('Day', 'Día')} <strong>{formatNumber(current.day, lang, { decimals: 2 })}</strong> · S/N <strong>{formatNumber(current.s * 100, lang, { decimals: 2 })}%</strong> · I/N <strong>{formatNumber(current.i * 100, lang, { decimals: 3 })}%</strong> · {t('threshold', 'umbral')} <strong>{formatNumber(sel.gamma / sel.beta * 100, lang, { decimals: 2 })}%</strong></p>
    <p className="caos-plot-note">{t('Move over the trajectory or use the arrow keys. Infection growth stops where S/N crosses γ/β.', 'Desplace el puntero por la trayectoria o use las flechas. El crecimiento infeccioso se detiene cuando S/N cruza γ/β.')}</p>
  </PlotCard>;
}

function ParityView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  const stateKey = useWorkbenchState()?.stateKey;
  const cmp = useMemo(() => {
    if (!sel) return null;
    const at = atTimes(sel.run, sel.data.trace.t);
    const diff = at.I.map((v, i) => v - sel.data.trace.I[i]);
    const worst = Math.max(...diff.map(Math.abs));
    const p = sel.data.manifest.params;
    const asBaked = sel.beta === p.beta && sel.gamma === p.gamma && sel.coverage === 0;
    return { diff, worst, asBaked };
  }, [sel]);
  if (!sel || !cmp) return <Pending label={LOADING} />;
  const s = sel.data.trace.summary;
  const expect = sel.data.manifest.expect;
  const metric = (key: string, label: BiText, replay: number, live: number, decimals: number) => {
    const range = expect[key];
    return {
      key,
      label,
      replay: formatNumber(replay, lang, { decimals }),
      live: formatNumber(live, lang, { decimals }),
      range: range ? `${formatNumber(range[0], lang, { decimals })} - ${formatNumber(range[1], lang, { decimals })}` : '',
      inside: range ? live >= range[0] && live <= range[1] : null,
    };
  };
  const rows = [
    metric('peak_I', { en: 'Peak infected', es: 'Pico de contagiados' }, s.peak_I, sel.run.peakI, 2),
    metric('t_peak', { en: 'Peak day', es: 'Día del pico' }, s.t_peak, sel.run.tPeak, 2),
    metric('attack_rate', { en: 'Attack rate', es: 'Tasa de ataque' }, s.attack_rate, sel.run.attackRate, 4),
  ];
  return (
    <>
      <PlotCard title={{ en: 'The two engines on this case', es: 'Los dos motores en este caso' }} lane="live" provenance="synthetic" dataKey={stateKey}>
        <Verdict
          compact
          title={{ en: 'Parity of the engines', es: 'Paridad de los motores' }}
          tone={cmp.asBaked ? (cmp.worst <= 0.0051 ? 'good' : 'bad') : 'neutral'}
          verdict={
            cmp.asBaked
              ? cmp.worst <= 0.0051
                ? { en: `The live engine reproduces the replay to ${formatNumber(cmp.worst, 'en', { decimals: 4 })} people (the trace rounding).`, es: `El motor en vivo reproduce la reproducción con ${formatNumber(cmp.worst, 'es', { decimals: 4 })} personas (el redondeo de la traza).` }
                : { en: 'The live engine departs from the replay: the two engines disagree.', es: 'El motor en vivo se aparta de la reproducción: los dos motores no coinciden.' }
              : { en: 'The rail values differ from the baked case, so the live run departs from the replay by design.', es: 'Los valores del panel difieren del caso precalculado, así que la corrida en vivo se aparta de la reproducción por diseño.' }
          }
        />
        <table className="caos-table">
          <thead>
            <tr>
              <th>{pick({ en: 'Summary', es: 'Resumen' }, lang)}</th>
              <th>{pick({ en: 'Replay (Python)', es: 'Reproducción (Python)' }, lang)}</th>
              <th>{pick({ en: 'Live (TypeScript)', es: 'En vivo (TypeScript)' }, lang)}</th>
              <th>{pick({ en: 'Expected range', es: 'Rango esperado' }, lang)}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <td>{pick(r.label, lang)}</td>
                <td>{r.replay}</td>
                <td>{r.live}</td>
                <td>{r.range ? `${r.range} ${r.inside ? pick({ en: '(live inside)', es: '(en vivo dentro)' }, lang) : pick({ en: '(live outside)', es: '(en vivo fuera)' }, lang)}` : pick({ en: 'not stated', es: 'no declarado' }, lang)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </PlotCard>
      <PlotCard fill title={{ en: 'Infected, live minus replay', es: 'Contagiados, en vivo menos reproducción' }} lane="live" provenance="synthetic" dataKey={stateKey}>
        <UPlotChart
          title={{ en: 'Infected, live minus replay', es: 'Contagiados, en vivo menos reproducción' }}
          height="fill"
          x={{ values: sel.data.trace.t, label: { en: 'Day', es: 'Día' }, unit: 'd' }}
          y={{ label: { en: 'Difference', es: 'Diferencia' }, unit: { en: 'people', es: 'personas' } }}
          series={[{ label: { en: 'Live minus replay', es: 'En vivo menos reproducción' }, values: cmp.diff, color: '--color-magenta' }]}
        />
      </PlotCard>
    </>
  );
}

/** The final-size relation against the engine run to the case horizon, over a range of R0 around the case. */
function FinalSizeView({ sel }: { sel: Selection | null }) {
  const stateKey = useWorkbenchState()?.stateKey;
  const curve = useMemo(() => {
    if (!sel) return null;
    const p = sel.data.manifest.params;
    const r0s = Array.from({ length: 49 }, (_, k) => 0.4 + k * 0.1);
    const theory = r0s.map(finalSize);
    const engine = r0s.map((r0) => simulate({ ...p, beta: r0 * sel.gamma, gamma: sel.gamma }).attackRate);
    const r0 = sel.beta / sel.gamma;
    return { r0s, theory, engine, r0, gap: Math.abs(sel.run.attackRate - finalSize(r0)) };
  }, [sel]);
  if (!sel || !curve) return <Pending label={LOADING} />;
  const days = sel.data.manifest.params.days;
  const seeded = sel.data.manifest.params.I0 > 0;
  return (
    <>
      {/* The verdict stands on its own above the chart: a titled card around one line would take the drawing's height. */}
      <Verdict
        compact
        title={{ en: 'Against the final-size relation', es: 'Contra la relación de tamaño final' }}
        tone={sel.coverage > 0 || !seeded ? 'neutral' : curve.gap <= 0.02 ? 'good' : 'warn'}
        verdict={
          !seeded
            ? { en: 'No initial infection: nothing spreads, while the relation assumes a seed of infection.', es: 'Sin contagio inicial: nada se propaga, mientras la relación supone una semilla de contagio.' }
            : sel.coverage > 0
            ? { en: 'Immunisation changes the initial susceptible share; the relation below is for a fully susceptible population.', es: 'La inmunización cambia la fracción susceptible inicial; la relación de abajo es para una población totalmente susceptible.' }
            : curve.gap <= 0.02
              ? { en: `The run ends within ${formatNumber(curve.gap * 100, 'en', { decimals: 1 })} points of the final size.`, es: `La corrida termina a ${formatNumber(curve.gap * 100, 'es', { decimals: 1 })} puntos del tamaño final.` }
              : { en: `The run is ${formatNumber(curve.gap * 100, 'en', { decimals: 1 })} points from the final size: the ${days}-day horizon ends first, or R0 is near 1.`, es: `La corrida está a ${formatNumber(curve.gap * 100, 'es', { decimals: 1 })} puntos del tamaño final: el horizonte de ${days} días termina antes, o R0 está cerca de 1.` }
        }
      />
      <PlotCard fill title={{ en: 'Share ever infected against R0', es: 'Fracción alguna vez contagiada contra R0' }} lane="live" provenance="synthetic" dataKey={stateKey}>
        <UPlotChart
          title={{ en: 'Share ever infected against R0', es: 'Fracción alguna vez contagiada contra R0' }}
          height="fill"
          x={{ values: curve.r0s, label: { en: 'Basic reproduction number', es: 'Número reproductivo básico' } }}
          y={{ label: { en: 'Attack rate', es: 'Tasa de ataque' }, range: [0, 1] }}
          series={[
            { label: { en: 'Final-size relation', es: 'Relación de tamaño final' }, values: curve.theory, color: '--color-accent' },
            { label: { en: `Engine at ${days} days`, es: `Motor a ${days} días` }, values: curve.engine, color: '--color-warn', dash: [5, 4] },
          ]}
          marks={[{ x: curve.r0, label: { en: 'this case', es: 'este caso' } }]}
        />
      </PlotCard>
    </>
  );
}

/** Peak and attack rate of the case under each immunisation variant, run live, on the shell's bar chart: margins
 * measured from the labels, the variant on screen highlighted, values in the interface language. */
export function CompareView({ sel }: { sel: Selection | null }) {
  const stateKey = useWorkbenchState()?.stateKey;
  const rows = useMemo(() => {
    if (!sel) return null;
    const p = sel.data.manifest.params;
    return COVERAGE.map((v) => ({ v, run: simulate({ ...p, beta: sel.beta, gamma: sel.gamma, vaccinated: v.share }) }));
  }, [sel]);
  if (!sel || !rows) return <Pending label={LOADING} />;
  const bars = (value: (r: NonNullable<typeof rows>[number]) => number) =>
    rows.map((r) => ({ id: r.v.id, label: r.v.label, value: value(r), highlight: r.v.share === sel.coverage }));
  return (
    <ViewsRow>
      <PlotCard fill title={{ en: 'Attack rate by immunisation', es: 'Tasa de ataque por inmunización' }} lane="live" provenance="synthetic" dataKey={stateKey}>
        <BarChart
          height="fill"
          title={{ en: 'Attack rate by immunisation', es: 'Tasa de ataque por inmunización' }}
          axis={{ label: { en: 'Attack rate', es: 'Tasa de ataque' }, format: { percent: true, decimals: 1 } }}
          data={bars((r) => r.run.attackRate)}
        />
      </PlotCard>
      <PlotCard fill title={{ en: 'Peak infected by immunisation', es: 'Pico de contagiados por inmunización' }} lane="live" provenance="synthetic" dataKey={stateKey}>
        <BarChart
          height="fill"
          title={{ en: 'Peak infected by immunisation', es: 'Pico de contagiados por inmunización' }}
          axis={{ label: { en: 'Peak infected', es: 'Pico de contagiados' }, unit: { en: 'people', es: 'personas' }, format: { decimals: 0 } }}
          data={bars((r) => r.run.peakI)}
        />
      </PlotCard>
    </ViewsRow>
  );
}

/** The write-up of the case: what it is, its parameters, the model, what each view shows. */
export function ContextView({ sel }: { sel: Selection | null }) {
  const lang = useShellLang();
  const location = useLocation();
  if (!sel) return <Pending label={LOADING} />;
  const m = sel.data.manifest;
  const p = m.params;
  const t = (en: string, es: string) => (lang === 'es' ? es : en);
  return (
    <>
      <ReadinessNote ids={CASE_ROWS} />
      <h2>{m.title[lang]}</h2>
      <p>
        {t('Category', 'Categoría')}: {m.category[lang]}. {t('What a reader should see', 'Lo que el lector debería ver')}: {m.expected_band[lang]}
      </p>
      <table className="caos-table">
        <tbody>
          <tr><td>{t('Contact rate', 'Tasa de contacto')}</td><td>{formatNumber(p.beta, lang, { decimals: 2 })} 1/d</td></tr>
          <tr><td>{t('Recovery rate', 'Tasa de recuperación')}</td><td>{formatNumber(p.gamma, lang, { decimals: 2 })} 1/d</td></tr>
          <tr><td>{t('Basic reproduction number', 'Número reproductivo básico')}</td><td>{formatNumber(p.beta / p.gamma, lang, { decimals: 2 })}</td></tr>
          <tr><td>{t('Population', 'Población')}</td><td>{formatNumber(p.N, lang, { decimals: 0 })}</td></tr>
          <tr><td>{t('Initial infected', 'Contagiados iniciales')}</td><td>{formatNumber(p.I0, lang, { decimals: 0 })}</td></tr>
          <tr><td>{t('Horizon', 'Horizonte')}</td><td>{p.days} d</td></tr>
        </tbody>
      </table>
      <h3>{t('The model', 'El modelo')}</h3>
      <Equation
        tex="\frac{dS}{dt} = -\beta \frac{S I}{N}, \quad \frac{dI}{dt} = \beta \frac{S I}{N} - \gamma I, \quad \frac{dR}{dt} = \gamma I"
        caption={t('The SIR equations; both engines integrate them with forward Euler at a quarter-day step.', 'Las ecuaciones SIR; ambos motores las integran con Euler explícito a un paso de un cuarto de día.')}
      />
      <h3>{t('How to read the views', 'Cómo leer las vistas')}</h3>
      <p>
        {t(
          'Dynamics shows the live run with the rail values and, dashed, the replay the pipeline baked for this case. Validation compares the two engines on the baked parameters and the run against the final-size relation. Compare immunisation re-runs the case with a share of the population immune from the start; the herd threshold is 1 - 1/R0.',
          'Dinámica muestra la corrida en vivo con los valores del panel y, segmentada, la reproducción que el pipeline precalculó para este caso. Validación compara los dos motores con los parámetros precalculados y la corrida contra la relación de tamaño final. Comparar inmunización vuelve a correr el caso con una fracción de la población inmune desde el inicio; el umbral de rebaño es 1 - 1/R0.',
        )}
      </p>
      <p><Link to={`/story/context?${new URLSearchParams({ case: m.case_id, from: `${location.pathname}${location.search}` }).toString()}`}>{t('Open the guided case story', 'Abrir el recorrido guiado del caso')}</Link></p>
      <p>
        {t('Engine', 'Motor')}: {m.engine.model}, {m.engine.package} {m.engine.version}. {t('Data', 'Datos')}: {m.real_or_synthetic === 'synthetic' ? t('synthetic', 'sintéticos') : t('real', 'reales')}.
      </p>
    </>
  );
}
