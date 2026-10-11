"""GET-only endpoints serving the committed documents unchanged (read-only), as docs/contracts/api.openapi.json
declares. A document that does not exist yet is a declared state: 503 with state missing and its reason, never an
empty body that looks like data. No write paths."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..services import content

router = APIRouter(prefix="/api")

NOT_BAKED = {"en": "The pipeline has not baked this build.", "es": "El pipeline no ha generado esta versión."}
NO_READINESS = {"en": "The readiness document is not in this build.",
                "es": "El documento de disponibilidad no está en esta versión."}


def _unavailable(reason: dict[str, str]) -> HTTPException:
    return HTTPException(status_code=503, detail={"state": "missing", "reason": reason})


@router.get("/cases")
def list_cases() -> Any:
    """The index (contract 2): every baked case and the path of its manifest."""
    index = content.load_index()
    if index is None:
        raise _unavailable(NOT_BAKED)
    return index


@router.get("/cases/{case_id}/manifest")
def get_manifest(case_id: str) -> Any:
    if content.load_index() is None:
        raise _unavailable(NOT_BAKED)
    m = content.load_manifest(case_id)
    if m is None:
        raise HTTPException(status_code=404, detail="unknown case")
    return m


@router.get("/artifacts/{rel_path:path}")
def get_artifact(rel_path: str) -> Any:
    """Any artifact a manifest names, by its path under data/derived (for example `<case>/<variant>.json`)."""
    art = content.load_artifact(rel_path)
    if art is None:
        raise HTTPException(status_code=404, detail="no such artifact")
    return art


@router.get("/readiness")
def get_readiness() -> Any:
    """What is real in this build: the committed readiness document, with the api row available."""
    doc = content.load_readiness()
    if doc is None:
        raise _unavailable(NO_READINESS)
    return doc
