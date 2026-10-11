# Requirements: contracts, providers and declared states (ADR-0080)

EARS (Mavin et al., RE'09, doi:10.1109/RE.2009.9). Every requirement names the gate that fails when it is violated.
The contracts are the rows of [`docs/contracts/catalog.md`](../../../contracts/catalog.md); the states and their
reasons are its section Missing-data states.

| ID | Requirement | Gate |
|---|---|---|
| CT-001 | THE pipeline SHALL write every document (index, manifest, trace) valid against its schema file, in a fresh bake and in the committed one. | `tests/contracts/test_documents.py::test_manifests_validate` |
| CT-002 | THE provider tree SHALL satisfy the same schemas and cross-field rules as the bake. | `tests/contracts/test_documents.py::test_fixture_tree_validates` |
| CT-003 | IF a document drifts from its schema (an extra key, a missing key, a wrong type), THEN THE contract tests SHALL fail. | `tests/contracts/test_documents.py::test_drifted_documents_are_rejected` |
| CT-004 | THE schema of contract 1 SHALL hold the same bounds as the code that applies it. | `tests/contracts/test_params_record.py::test_schema_valid_records_are_accepted` |
| CT-005 | WHEN a schema file changes, THE web build SHALL fail until the generated types are regenerated. | `frontend/scripts/gen-contract-types.mjs`, run by `npm run build` |
| CT-006 | THE web SHALL read the committed bake and the provider tree with the same assertions. | `frontend/src/lib/contract.test.ts::the readiness document conforms and lists the catalog rows in order` |
| CT-007 | THE generated API response bodies SHALL be the document types. | `frontend/src/lib/api.contract.test.ts::200 bodies` |
| CT-008 | THE bake SHALL write a readiness document equal to a fresh computation from the catalog and the repository. | `tests/contracts/test_readiness.py::test_committed_readiness_is_current` |
| CT-009 | IF a manifest the index lists is absent, THEN THE readiness SHALL say partial for case-manifest and list its path. | `tests/contracts/test_readiness.py::test_state_partial_manifests` |
| CT-010 | WHILE the bake was made by another version than VERSION, THE readiness SHALL say stale with both versions. | `tests/contracts/test_readiness.py::test_state_stale` |
| CT-011 | WHILE a catalog row is active, THE readiness SHALL say provider and name the provider. | `tests/contracts/test_readiness.py::test_state_provider_through_a_catalog_copy` |
| CT-012 | IF no valid surrogate bundle is released, THEN THE baseline SHALL answer and THE readiness SHALL say training with provenance baseline. | `tests/contracts/test_readiness.py::test_state_training_without_a_bundle` |
| CT-013 | WHILE a newer surrogate is training (the marker exists), THE readiness SHALL say training with provenance real. | `tests/contracts/test_readiness.py::test_state_training_with_the_marker` |
| CT-014 | IF no bake exists, THEN THE readiness SHALL say missing for the artifact rows. | `tests/contracts/test_readiness.py::test_state_missing_without_an_index` |
| CT-015 | IF the catalog changes and the readiness is not recomputed, THEN THE readiness check SHALL fail. | `tests/contracts/test_readiness.py::test_check_readiness_fails_on_a_changed_catalog` |
| CT-016 | THE readiness check SHALL run without the pipeline's dependencies (CI installs none). | `tests/contracts/test_readiness.py::test_check_readiness_runs_without_numpy` |
| CT-017 | THE baseline and the trained bundle SHALL pass the same slot assertions. | `tests/contracts/test_surrogate.py::test_swap_baseline_and_trained` |
| CT-018 | WHEN the bake runs with `--no-train` and no valid bundle, THE pipeline SHALL never train and SHALL report the baseline. | `tests/contracts/test_surrogate.py::test_no_train_without_a_bundle_reports_the_baseline` |
| CT-019 | THE API SHALL answer every route with the body the OpenAPI document declares. | `tests/contracts/test_api.py::test_responses_match_the_openapi_document` |
| CT-020 | IF a document the API serves is absent, THEN THE API SHALL answer 503 with state missing and the reason, never an empty body. | `tests/contracts/test_api.py::test_503_when_documents_are_absent` |
| CT-021 | THE API SHALL never serve a file outside the derived root. | `tests/contracts/test_api.py::test_404_bodies_and_nothing_outside_the_root` |
| CT-022 | THE site SHALL label a view with the most severe state of its rows, in the order missing, partial, training, provider, stale, available. | `frontend/src/readiness/readiness.test.ts::order: missing, partial, training, provider, stale, available; the most severe wins` |
| CT-023 | IF the readiness document cannot be read, THEN THE site SHALL keep every view working and say readiness unknown. | `frontend/src/readiness/readiness.test.ts::a fetch that fails resolves to null, names the cause on the console, and is asked for once` |
| CT-024 | IF the readiness lists a case's trace as absent, THEN THE site SHALL say not available yet with the reason and never fetch it. | `frontend/src/readiness/readiness.test.ts::loadCase rejects with ArtifactUnavailable naming the path and the reason, and never fetches the trace` |
| CT-025 | WHILE the branch is main, THE CI SHALL fail when a catalog row is still served by a provider. | `.github/workflows/ci.yml`, step "Rows still served by a provider" |
