# The specification area

Where a product states what it will build and proves the statement can fail. It is written before any code
(ADR-0075) and kept current with it: a guard fails when a part is missing or disagrees with the repository.
The area is `docs/design/` (the design), `docs/contracts/` (the contracts as code) and `tests/` (the tests, with
`tests/adversarial/` for the planted defects).

## The order

1. **Research basis.** What was researched before the plan and what it decided: each claim with a source (a DOI or a
   URL), at least three sources, and the list of what stayed UNVERIFIED (it may say none). Section `Research basis`
   of [`SDD.md`](SDD.md). Checked by `scripts/check_sdd.py`.
2. **Sizing, summarised.** The product dimensioned before it is built: its components, its boundaries, the
   technology and version matrix and the resources of each stage. The sizing's coordination records (the parallel
   units, who owns them) live with the product's coordination, not here; this repository holds the product's own
   design facts. Sections `Sizing and contracts`, `Technology and versions` and `Resources` of [`SDD.md`](SDD.md).
   Checked by `scripts/check_sdd.py` (the resources table has no empty cell and no TBD) and
   `scripts/check_tech_matrix.py` (the technology table is the pinned dependencies, version for version).
3. **Contracts.** One row per boundary and per model slot in [`../contracts/catalog.md`](../contracts/catalog.md), one
   schema file each, an example, a test on each side, the missing-data behavior and a provider. A contract is mutable
   and versioned: its version follows its schema by semver, its history is a row per version, and
   [`../contracts/versions.lock.json`](../contracts/versions.lock.json) holds the digest of each schema. Checked by
   `scripts/check_contracts.py`, `scripts/check_skeleton.py`, `scripts/check_readiness.py` and
   `scripts/check_contract_versions.py`.
4. **Requirements.** Per feature, `features/<feature>/requirements.md`: `| ID | statement | gate |`, every statement
   with SHALL, every gate a test or guard that exists. Checked by `scripts/check_sdd.py`.
5. **Tests, red first.** Each requirement and edge case becomes a test that fails for the right reason before the
   code exists (`tests/`, `frontend/src/**/*.test.ts`); the code that follows is the minimum that turns them green.
6. **Adversarial validation.** Per feature, `features/<feature>/validation.md`: `| requirement | adversarial check |
   gate |`, one row per requirement, the check stated as what was planted or refuted ("a NaN parameter is rejected")
   and the gate the test that plants it. The guards are attacked too: `tests/adversarial/` copies the repository,
   plants one defect, runs the guard and asserts the exit code and the message. Checked by `scripts/check_sdd.py`
   and `python -m pytest tests/adversarial -q`.

## Where each part lives

| part | file | guard |
|---|---|---|
| research basis | `docs/design/SDD.md`, `Research basis` | `scripts/check_sdd.py` |
| sizing summary, technology, resources | `docs/design/SDD.md`, `Sizing and contracts`, `Technology and versions`, `Resources` | `scripts/check_sdd.py`, `scripts/check_tech_matrix.py` |
| contracts, providers, states | `docs/contracts/catalog.md`, `docs/contracts/schemas/` | `scripts/check_contracts.py`, `scripts/check_skeleton.py`, `scripts/check_readiness.py` |
| contract versions and history | `docs/contracts/catalog.md` (`History`), `docs/contracts/versions.lock.json` | `scripts/check_contract_versions.py` |
| requirements | `docs/design/features/<feature>/requirements.md` | `scripts/check_sdd.py` |
| adversarial validation | `docs/design/features/<feature>/validation.md`, `tests/adversarial/` | `scripts/check_sdd.py`, `tests/adversarial/` |

## Changing a contract

Edit the schema, bump the version in the catalog by the semver rule (removed or renamed field, narrowed type or new
required field: major; new optional field: minor; description or example: patch), add the History row, then
`python scripts/check_contract_versions.py --update` and `python data-pipeline/run.py readiness`, and update both sides
in the same pull request. The check fails on a schema that changed under the same version, a version that went
down, a lock that is not current, and a row without a History entry for its version.

CI runs the checks above in the `checks` job (seconds, ADR-0074); the product's own tests and the bake run locally.
