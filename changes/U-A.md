### Added
- `frontend/scripts/gen-contract-types.mjs`: generates `frontend/src/lib/contract.gen.ts` from `docs/contracts/api.openapi.json` with openapi-typescript 7.13.0; `npm run contracts:types` writes it, `npm run contracts:check` (and `npm run build`) fails when it is not current.
- Two-sided document tests: `tests/contracts/test_documents.py` (committed bake, a fresh sandbox bake and the provider tree against the schema files, the OpenAPI document, one negative test per schema) and `tests/contracts/test_params_record.py` (contract 1 against its schema, bounds equal `RANGES`); `frontend/src/lib/api.contract.test.ts` (generated response bodies equal the document types).
- `scripts/check_contracts.py` and `scripts/check_skeleton.py`: the catalog and skeleton checks of CAOS_MANAGE, vendored at bd0251f2.
- `requirements-dev.txt`: jsonschema, openapi-spec-validator, and fastapi and httpx for the API contract tests (the API lane stays dormant).

### Changed
- `frontend/src/lib/contract.types.ts`: every exported type is an alias of the generated types (names kept); `SCHEMAS` is tied to the generated `schema` constants; the descriptors are tied to the generated types by `satisfies`; `UNAVAILABLE`, `UnavailableBody` and `NotFoundBody` added.
- `frontend/src/lib/contract.test.ts`: the same assertions run on the committed bake and on the provider tree (the swap), readiness included.
- `npm run build` starts with the currency check of the generated types.
