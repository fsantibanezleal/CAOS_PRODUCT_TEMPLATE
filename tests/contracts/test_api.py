"""Catalog row api 1.0.0: the dormant FastAPI app serves every committed document as docs/contracts/api.openapi.json
declares, answers 503 with the declared state when a document is absent, 404 for an unknown case or artifact, and never
leaves the derived root. DATA_DIR selects the tree (the swap test runs the same assertions on the provider fixture tree
and on the bake)."""
from __future__ import annotations

import sys

import pytest
from contract_schemas import DERIVED_ROOTS, OPENAPI, ROOT, load_json, response_errors

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, str(ROOT))

UNAVAILABLE_INDEX = {"en": "The pipeline has not baked this build.", "es": "El pipeline no ha generado esta versión."}
UNAVAILABLE_READINESS = {"en": "The readiness document is not in this build.",
                         "es": "El documento de disponibilidad no está en esta versión."}


def client(monkeypatch: pytest.MonkeyPatch, data_dir) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    from app.main import create_app

    return TestClient(create_app())


def get_checked(c: TestClient, path: str, template: str, expect: int):
    """GET ``path``, require ``expect`` and the body the OpenAPI document declares for ``template``."""
    r = c.get(path)
    assert r.status_code == expect, f"{path}: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert response_errors(template, "get", expect, body) == [], path
    return body


def test_routes_match_the_openapi_document(monkeypatch, tmp_path):
    app = client(monkeypatch, tmp_path).app
    # the app's own generated schema lists every route the app serves (included routers are wrapped in fastapi 0.143)
    served = {(p, m.upper()) for p, ops in app.openapi()["paths"].items() for m in ops}
    declared = {(p, m.upper()) for p, ops in load_json(OPENAPI)["paths"].items() for m in ops}
    assert served == declared


def assert_serves_everything(c: TestClient) -> int:
    assert get_checked(c, "/health", "/health", 200) == {"status": "ok"}
    get_checked(c, "/healthz", "/healthz", 200)
    index = get_checked(c, "/api/cases", "/api/cases", 200)
    assert index["cases"]
    n_artifacts = 0
    for e in index["cases"]:
        m = get_checked(c, f"/api/cases/{e['case_id']}/manifest", "/api/cases/{case_id}/manifest", 200)
        paths = [m["artifact"]["path"]] if "artifact" in m else [a["path"] for a in m["artifacts"]]
        for rel in paths:
            get_checked(c, f"/api/artifacts/{rel}", "/api/artifacts/{rel_path}", 200)
            n_artifacts += 1
    ready = get_checked(c, "/api/readiness", "/api/readiness", 200)
    api = next(e for e in ready["contracts"] if e["id"] == "api")
    assert (api["state"], api["provenance"], api["reason"]) == ("available", "real", None)
    return n_artifacts


def test_responses_match_the_openapi_document(monkeypatch):
    assert assert_serves_everything(client(monkeypatch, DERIVED_ROOTS["bake"])) >= 5


def test_swap_fixture_tree_and_bake(monkeypatch):
    for which in ("fixture", "bake"):
        assert assert_serves_everything(client(monkeypatch, DERIVED_ROOTS[which])) >= 1, which


def test_503_when_documents_are_absent(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)
    for path, template, reason in (("/api/cases", "/api/cases", UNAVAILABLE_INDEX),
                                   ("/api/cases/EX01_subcritical/manifest", "/api/cases/{case_id}/manifest",
                                    UNAVAILABLE_INDEX),
                                   ("/api/readiness", "/api/readiness", UNAVAILABLE_READINESS)):
        body = get_checked(c, path, template, 503)
        assert body == {"detail": {"state": "missing", "reason": reason}}, path
    assert "cases" not in c.get("/api/cases").json()  # never the old empty-index body


def test_404_bodies_and_nothing_outside_the_root(monkeypatch):
    c = client(monkeypatch, DERIVED_ROOTS["bake"])
    assert get_checked(c, "/api/cases/NOPE/manifest", "/api/cases/{case_id}/manifest", 404) == {"detail": "unknown case"}
    for bad in ("..%5Cindex", ".hidden", "..", "%2e%2e"):
        r = c.get(f"/api/cases/{bad}/manifest")
        assert r.status_code == 404 and response_errors("/api/cases/{case_id}/manifest", "get", 404, r.json()) == [], bad
    for rel in ("EX01_subcritical/nope.json", "../../VERSION", "..%2F..%2FVERSION", "%2e%2e/%2e%2e/package.json",
                "..%5C..%5CVERSION", "manifests/..%2F..%2F..%2FVERSION", "manifests/.gitkeep", "manifests",
                "EX01_subcritical", "readiness.json.txt"):
        r = c.get(f"/api/artifacts/{rel}")
        assert r.status_code == 404, rel
        assert r.json() == {"detail": "no such artifact"} or response_errors(
            "/api/artifacts/{rel_path}", "get", 404, r.json()) == [], rel
    assert c.get("/api/artifacts/EX01_subcritical/trace.json").status_code == 200


def test_get_only(monkeypatch):
    c = client(monkeypatch, DERIVED_ROOTS["bake"])
    for method in ("post", "put", "patch", "delete"):
        assert getattr(c, method)("/api/cases").status_code == 405, method
