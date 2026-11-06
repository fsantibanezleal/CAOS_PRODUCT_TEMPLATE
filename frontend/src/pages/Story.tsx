import { BarChart, PlotCard, SceneCallouts, StoryFrame, formatNumber, pick, useLinkedView, useShellLang, type SceneCalloutDef, type StoryStep } from '@fasl-work/caos-app-shell';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useMemo, useState } from 'react';
import { loadCase, loadIndex, useArtifact } from '../api/artifacts';
import { simulate } from '../engine/sir';
import { caseAbsent } from '../readiness/readiness';
import { useReadiness } from '../readiness/useReadiness';
import { EulerStepView, PhasePlaneView, SystemDiagramView } from '../workbench/views';
import { COVERAGE, type Selection } from '../workbench/model';
import './story.css';

function StoryCompareView({ sel }: { sel: Selection }) {
  const lang = useShellLang();
  const [metric, setMetric] = useState<'attack' | 'peak'>('attack');
  const t = (en: string, es: string) => lang === 'es' ? es : en;
  const rows = useMemo(() => COVERAGE.map((variant) => {
    const run = simulate({ ...sel.data.manifest.params, beta: sel.beta, gamma: sel.gamma, vaccinated: variant.share });
    return { id: variant.id, label: variant.label, value: metric === 'attack' ? run.attackRate : run.peakI, highlight: variant.share === sel.coverage };
  }), [metric, sel]);
  return <div className="template-story-compare">
    <div className="template-story-metric" role="group" aria-label={t('Choose comparison measure', 'Elegir medida de comparación')}>
      <button type="button" aria-pressed={metric === 'attack'} onClick={() => setMetric('attack')}>{t('Attack rate', 'Tasa de ataque')}</button>
      <button type="button" aria-pressed={metric === 'peak'} onClick={() => setMetric('peak')}>{t('Peak infections', 'Pico de contagios')}</button>
    </div>
    <PlotCard fill title={{ en: metric === 'attack' ? 'Attack rate by immunisation' : 'Peak infections by immunisation', es: metric === 'attack' ? 'Tasa de ataque por inmunización' : 'Pico de contagios por inmunización' }} lane="live" provenance="synthetic">
      <BarChart height="fill" title={{ en: metric === 'attack' ? 'Attack rate by immunisation' : 'Peak infections by immunisation', es: metric === 'attack' ? 'Tasa de ataque por inmunización' : 'Pico de contagios por inmunización' }} axis={{ label: metric === 'attack' ? { en: 'Attack rate', es: 'Tasa de ataque' } : { en: 'Peak infections', es: 'Pico de contagios' }, ...(metric === 'attack' ? { format: { percent: true, decimals: 1 } } : { unit: { en: 'people', es: 'personas' }, format: { decimals: 0 } }) }} data={rows}/>
    </PlotCard>
  </div>;
}

function readout(sel: Selection, lang: 'en' | 'es') {
  const p = sel.data.manifest.params;
  const peak = sel.run.peakI;
  const r0 = sel.beta / sel.gamma;
  return { peak: formatNumber(peak, lang, { decimals: 0 }), day: formatNumber(sel.run.tPeak, lang, { decimals: 1 }), r0: formatNumber(r0, lang, { decimals: 2 }), attack: formatNumber(sel.run.attackRate * 100, lang, { decimals: 1 }), final: formatNumber(sel.run.R.at(-1) ?? 0, lang, { decimals: 0 }), population: formatNumber(p.N, lang, { decimals: 0 }) };
}

export function Story() {
  const lang = useShellLang();
  const { step = 'context' } = useParams();
  const [query] = useSearchParams();
  const navigate = useNavigate();
  const sharedCursor = useLinkedView((state) => state.cursor);
  const selectedState = useLinkedView((state) => state.selectedId);
  const selectState = useLinkedView((state) => state.select);
  const readiness = useReadiness();
  const index = useArtifact((state) => loadIndex(state), []);
  const caseId = query.get('case') ?? (index.state === 'ready' ? index.data.default_case : null);
  const indexEntry = index.state === 'ready' && caseId ? index.data.cases.find((entry) => entry.case_id === caseId) ?? null : null;
  const loaded = useArtifact((state) => caseId ? loadCase(caseId, state) : new Promise<never>(() => undefined), [caseId]);
  const data = loaded.state === 'ready' && loaded.data.manifest.case_id === caseId ? loaded.data : null;
  const sel: Selection | null = useMemo(() => data ? { data, beta: data.manifest.params.beta, gamma: data.manifest.params.gamma, coverage: 0, run: simulate(data.manifest.params) } : null, [data]);
  const unavailable = index.state === 'unavailable' ? index.reason : index.state === 'error' ? index.error : loaded.state === 'unavailable' ? loaded.reason : loaded.state === 'error' ? loaded.error : null;
  const absent = data && indexEntry ? caseAbsent(readiness ?? null, data.manifest.case_id, indexEntry.manifest_path) : false;
  const from = query.get('from');
  const safeFrom = from && from.startsWith('/app') && !from.startsWith('//') && !from.includes('\\') ? from : null;
  const fallback = `/app?case=${encodeURIComponent(caseId ?? '')}`;
  const t = (en: string, es: string) => lang === 'es' ? es : en;

  if (!sel || absent) return <section className="template-story-state" data-state={absent || unavailable ? 'unavailable' : 'loading'}>
    <h1>{t('Guided case story', 'Recorrido guiado del caso')}</h1>
    <p>{unavailable ? pick(unavailable, lang) : absent ? t('This case is listed as not available in the release evidence.', 'Este caso figura como no disponible en la evidencia de la versión.') : t('Loading the selected case artifacts.', 'Cargando los artefactos del caso seleccionado.')}</p>
    <a href={fallback}>{t('Return to the workbench', 'Volver al banco de trabajo')}</a>
  </section>;

  const values = readout(sel, lang);
  const source = { en: `Live TypeScript run · ${sel.data.manifest.case_id}`, es: `Ejecución TypeScript en vivo · ${sel.data.manifest.case_id}` };
  const definitions: Record<string, SceneCalloutDef[]> = {
    context: [
      { id: 'r0', eyebrow: { en: 'BASIC R₀', es: 'R₀ BÁSICO' }, value: values.r0, unit: { en: 'ratio', es: 'razón' }, state: sel.beta > sel.gamma ? 'warning' : 'normal', anchor: { x: .72, y: .42 }, source },
      { id: 'population', eyebrow: { en: 'POPULATION', es: 'POBLACIÓN' }, value: values.population, unit: { en: 'people', es: 'personas' }, state: 'normal', anchor: { x: .2, y: .54 }, source: { en: 'Case manifest · initial conditions', es: 'Manifiesto del caso · condiciones iniciales' } },
      { id: 'horizon', eyebrow: { en: 'PEAK DAY', es: 'DÍA DEL PICO' }, value: values.day, unit: { en: 'days', es: 'días' }, state: 'selected', anchor: { x: .52, y: .5 }, source },
    ],
    phase: [
      { id: 'susceptible', eyebrow: { en: 'S AT PEAK', es: 'S EN EL PICO' }, value: formatNumber(sel.run.S[sel.run.t.indexOf(sel.run.tPeak)] ?? 0, lang, { decimals: 0 }), unit: { en: 'people', es: 'personas' }, state: 'normal', anchor: { x: .22, y: .58 }, source },
      { id: 'infected', eyebrow: { en: 'PEAK INFECTED', es: 'PICO DE CONTAGIADOS' }, value: values.peak, unit: { en: 'people', es: 'personas' }, state: 'warning', anchor: { x: .55, y: .2 }, source },
      { id: 'threshold', eyebrow: { en: 'GROWTH THRESHOLD', es: 'UMBRAL DE CRECIMIENTO' }, value: formatNumber(sel.gamma / sel.beta * 100, lang, { decimals: 1 }), unit: '% S/N', state: 'selected', anchor: { x: Math.max(.04, Math.min(.96, sel.gamma / sel.beta)), y: .42 }, source: { en: 'Derived from dI/dt = 0: S/N = γ/β', es: 'Derivado de dI/dt = 0: S/N = γ/β' } },
    ],
    decision: [
      { id: 'attack', eyebrow: { en: 'ATTACK RATE', es: 'TASA DE ATAQUE' }, value: values.attack, unit: '%', state: 'normal', anchor: { x: .24, y: .52 }, source },
      { id: 'peak', eyebrow: { en: 'PEAK INFECTED', es: 'PICO DE CONTAGIADOS' }, value: values.peak, unit: { en: 'people', es: 'personas' }, state: 'warning', anchor: { x: .53, y: .3 }, source },
      { id: 'coverage', eyebrow: { en: 'SCENARIOS', es: 'ESCENARIOS' }, value: '3', unit: { en: 'immunisation levels', es: 'niveles de inmunización' }, state: 'selected', anchor: { x: .78, y: .55 }, source: { en: 'Re-run from identical initial case', es: 'Reejecución desde el mismo caso inicial' } },
    ],
    method: [
      { id: 'step', eyebrow: { en: 'MODEL STEP', es: 'PASO DEL MODELO' }, value: formatNumber(sharedCursor ?? 0, lang, { decimals: 0 }), unit: { en: 'Euler updates', es: 'pasos de Euler' }, state: 'selected', anchor: { x: .5, y: .86 }, source: { en: 'Live engine · Δt = 0.25 day', es: 'Motor en vivo · Δt = 0,25 días' } },
      { id: 'infections', eyebrow: { en: 'NEW INFECTIONS', es: 'NUEVOS CONTAGIOS' }, value: formatNumber(sel.beta * sel.run.S[Math.min(sel.run.S.length - 1, sharedCursor ?? 0)]! * sel.run.I[Math.min(sel.run.I.length - 1, sharedCursor ?? 0)]! / sel.data.manifest.params.N * .25, lang, { decimals: 2 }), unit: { en: 'people / step', es: 'personas / paso' }, state: 'warning', anchor: { x: .31, y: .37 }, source: { en: 'βSIΔt/N · forward Euler', es: 'βSIΔt/N · Euler explícito' } },
      { id: 'balance', eyebrow: { en: 'MASS BALANCE', es: 'BALANCE POBLACIONAL' }, value: '0', unit: { en: 'people residual', es: 'residuo de personas' }, state: 'normal', anchor: { x: .72, y: .61 }, source: { en: 'S + I + R conserved by the update', es: 'S + I + R conservado por la actualización' } },
    ],
  };

  const steps: StoryStep[] = [
    { id: 'context', number: 1, verb: { en: 'Read the outbreak', es: 'Leer el brote' }, headline: { en: `R₀ is ${values.r0} in this case`, es: `R₀ es ${values.r0} en este caso` }, summary: { en: 'The boxes show compartment populations at one model day; arrows show the equation-derived flows.', es: 'Los bloques muestran las poblaciones por compartimento en un día; las flechas muestran los flujos derivados de las ecuaciones.' }, href: '', accent: 1, stage: null, panel: null },
    { id: 'phase', number: 2, verb: { en: 'Find the turning point', es: 'Encontrar el punto de giro' }, headline: { en: `I peaks at ${values.peak} on day ${values.day}`, es: `I alcanza ${values.peak} en el día ${values.day}` }, summary: { en: 'The nullcline S/N = γ/β marks where infections stop growing.', es: 'La nulclina S/N = γ/β marca dónde dejan de crecer los contagios.' }, href: '', accent: 2, stage: null, panel: null },
    { id: 'decision', number: 3, verb: { en: 'Compare interventions', es: 'Comparar intervenciones' }, headline: { en: `The reference attack rate is ${values.attack}%`, es: `La tasa de ataque de referencia es ${values.attack}%` }, summary: { en: 'All three scenarios use the same case, horizon and live engine.', es: 'Los tres escenarios usan el mismo caso, horizonte y motor en vivo.' }, href: '', accent: 3, stage: null, panel: null },
    { id: 'method', number: 4, verb: { en: 'Inspect one update', es: 'Inspeccionar un paso' }, headline: { en: 'Euler advances by 0.25 day per step', es: 'Euler avanza 0,25 días en cada paso' }, summary: { en: 'The selected cursor exposes compartment updates, flows and the population residual.', es: 'El cursor expone las actualizaciones, los flujos y el residuo poblacional.' }, href: '', accent: 4, stage: null, panel: null },
  ];
  const params = new URLSearchParams({ case: sel.data.manifest.case_id });
  if (safeFrom) params.set('from', safeFrom);
  const views = [<div className="template-story-card" key="system"><SystemDiagramView sel={sel}/></div>, <div className="template-story-card" key="phase"><PhasePlaneView sel={sel}/></div>, <div className="template-story-card" key="compare"><StoryCompareView sel={sel}/></div>, <div className="template-story-card" key="euler"><EulerStepView sel={sel}/></div>];
  const cursorIndex = Math.max(0, Math.min(sel.run.t.length - 1, sharedCursor ?? sel.run.I.reduce((best, value, index) => value > sel.run.I[best]! ? index : best, 0)));
  const scrubbed = { day: formatNumber(sel.run.t[cursorIndex]!, lang, { decimals: 2 }), susceptible: formatNumber(sel.run.S[cursorIndex]!, lang, { decimals: 0 }), infected: formatNumber(sel.run.I[cursorIndex]!, lang, { decimals: 0 }) };
  const statePicker = <div className="template-story-state-picker" aria-label={t('Select a compartment', 'Seleccionar un compartimento')}>{(['S', 'I', 'R'] as const).map((id) => <button key={id} type="button" data-linked-id={id} data-linked-view="panel" data-linked-selected={(selectedState ?? 'I') === id ? 'true' : 'false'} aria-pressed={(selectedState ?? 'I') === id} onClick={() => selectState(id, 'panel')}>{id} · {id === 'S' ? t('Susceptible', 'Susceptibles') : id === 'I' ? t('Infectious', 'Contagiados') : t('Recovered', 'Recuperados')}</button>)}</div>;
  const panels = [
    <><p>{t('The case starts with', 'El caso comienza con')} <strong>{values.population} {t('people', 'personas')}</strong> {t('and a basic reproduction ratio of', 'y una razón de reproducción básica de')} <strong>{values.r0}</strong>.</p><p>{t('At the linked day', 'En el día enlazado')} <strong>{scrubbed.day}</strong>: S = <strong>{scrubbed.susceptible}</strong>, I = <strong>{scrubbed.infected}</strong>.</p>{statePicker}<small>{t('Source: case manifest and synthetic replay trace.', 'Fuente: manifiesto del caso y traza de reproducción sintética.')}</small></>,
    <><p>{t('The trajectory turns when susceptible fraction crosses', 'La trayectoria gira cuando la fracción susceptible cruza')} <strong>S/N = γ/β = {formatNumber(sel.gamma / sel.beta * 100, lang, { decimals: 2 })}%</strong>.</p><p>{t('At the linked day', 'En el día enlazado')} <strong>{scrubbed.day}</strong>: S = <strong>{scrubbed.susceptible}</strong>, I = <strong>{scrubbed.infected}</strong>.</p>{statePicker}<small>{t('Threshold is derived from the model equation; the trajectory is a live synthetic calculation.', 'El umbral se deriva de la ecuación del modelo; la trayectoria es un cálculo sintético en vivo.')}</small></>,
    <><p>{t('Compare zero, 30% and 60% immunisation using the same initial case parameters.', 'Compare 0%, 30% y 60% de inmunización con los mismos parámetros iniciales.')}</p><p>{t('The current case reaches', 'El caso actual alcanza')} <strong>{values.attack}% {t('attack rate', 'de tasa de ataque')}</strong> {t('and', 'y')} <strong>{values.peak} {t('peak infections', 'contagios máximos')}</strong> {t('without immunisation.', 'sin inmunización.')}</p><p>{t('The shared cursor remains on day', 'El cursor compartido permanece en el día')} <strong>{scrubbed.day}</strong>.</p>{statePicker}<small>{t('Scenarios are recomputed by the live TypeScript engine; all inputs are synthetic.', 'Los escenarios se recalculan con el motor TypeScript en vivo; todos los datos son sintéticos.')}</small></>,
    <><p>{t('The shared cursor selects step', 'El cursor compartido selecciona el paso')} <strong>{cursorIndex}</strong> {t('of the live forward-Euler trace.', 'de la traza Euler explícita en vivo.')}</p><p>ΔS = −βSIΔt/N · ΔI = βSIΔt/N − γIΔt · ΔR = γIΔt</p><p>{t('Euler is first order; this view displays the exact discrete update and its balance residual from the same selected run.', 'Euler es de primer orden; esta vista muestra la actualización discreta exacta y su residuo de balance del mismo cálculo.')}</p>{statePicker}<small>{t('Source: live TypeScript engine, DT = 0.25 day; synthetic case values are recomputed in the browser.', 'Fuente: motor TypeScript en vivo, DT = 0,25 días; los valores sintéticos se recalculan en el navegador.')}</small></>,
  ];
  steps.forEach((item, i) => {
    item.href = `/story/${item.id}?${params.toString()}`;
    item.stage = <div className="template-story-stage"><SceneCallouts items={definitions[item.id]!} placement="header" className="template-story-callouts"/><div className="template-story-drawing">{views[i]}</div></div>;
    item.panel = <section className="template-story-evidence"><h2>{pick(item.verb, lang)}</h2>{panels[i]}<p><strong>{pick(sel.data.manifest.title, lang)}</strong> · {sel.data.manifest.case_id}</p><span className="badge" data-provenance="synthetic">{t('Synthetic case replay', 'Reproducción de caso sintético')}</span></section>;
  });
  return <StoryFrame className="template-story" steps={steps} activeId={steps.some((item) => item.id === step) ? step : 'context'} onStepChange={(next) => navigate(`/story/${next}?${params.toString()}`)} onExit={() => navigate(safeFrom ?? fallback)}/>;
}
