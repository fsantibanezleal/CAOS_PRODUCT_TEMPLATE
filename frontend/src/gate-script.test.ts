// The gate this build runs (scripts/gate.mjs) fails an App without Focus mode: --require-focus is always in effect, whatever
// extra arguments a run passes (WB-014; shell 0.14.0, ADR-0070).
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const gate = readFileSync(new URL('../scripts/gate.mjs', import.meta.url), 'utf8');
const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')) as { scripts: Record<string, string> };

describe('the gate script', () => {
  it('passes --require-focus to the shell gate, so every App built from the template must carry Focus mode', () => {
    expect(gate).toMatch(/'--require-focus'/);
  });

  it('adversarial: the runner of the previous release, without the flag, or with the flag after the pass-through arguments, is refused (WB-014)', () => {
    const holds = (source: string) => source.includes("'--require-focus'") && source.indexOf("'--require-focus'") < source.indexOf('...extra');
    expect(holds(gate)).toBe(true);
    expect(holds(gate.replace("'--require-focus', ", ''))).toBe(false);
    expect(holds(gate.replace("'--require-focus', ...out, ...extra", "...out, ...extra, '--require-focus'"))).toBe(false);
  });

  it('puts --require-focus before the pass-through arguments and the npm script does not drop it', () => {
    expect(gate.indexOf("'--require-focus'")).toBeLessThan(gate.indexOf('...extra'));
    expect(pkg.scripts.gate).toBe('node scripts/gate.mjs');
  });
});
