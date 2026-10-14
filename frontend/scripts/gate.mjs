// The measured gate on this build (caos-shell-gate, ADR-0078): serves dist/ as GitHub Pages does and walks every
// route, tab and case at five sizes, both themes and both languages, and requires Focus mode in the App. The expected brand is the product name from
// product.json, so the gate refuses to measure any other subject. Extra arguments are passed through, for example
//   npm run gate -- --sizes 1280x800 --themes light   (a quick pass while working)
//   npm run gate -- --url https://<domain>           (the deployed origin, after a deploy)
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const product = JSON.parse(readFileSync(join(here, '..', '..', 'product.json'), 'utf8'));
const require = createRequire(import.meta.url);
const bin = join(dirname(require.resolve('@fasl-work/caos-app-shell/package.json')), 'bin', 'caos-shell-gate.mjs');
const extra = process.argv.slice(2);
const target = extra.includes('--url') ? [] : ['--serve', join(here, '..', 'dist')];
if (process.env.VITE_BASE && !extra.includes('--url')) target.push('--base-path', process.env.VITE_BASE);
const out = ['--out', join(here, '..', 'gate-output')];
// --require-focus is always in effect (shell 0.14.0, ADR-0070): an App built from the template must carry Focus mode (G18), and no
// extra argument turns the requirement off.
const run = spawnSync(process.execPath, [bin, ...target, '--expect-brand', product.name, '--require-focus', ...out, ...extra], { stdio: 'inherit' });
process.exit(run.status ?? 1);
