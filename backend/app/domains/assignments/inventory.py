"""Server-managed reference inventory, bound to instructor inputs rather than student files."""
from __future__ import annotations

import hashlib
import json

from pydantic import ValidationError

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import get_artifact_content
from app.domains.grading.report_contract import RUNTIME_ID, ValidatedManifest
from app.domains.grading.runner_gen import generate_runner_script
from app.domains.grading.runtime import load_fallback_helper


def execution_fingerprint(db, assignment) -> str:
    config = AssignmentConfigV1.model_validate(assignment.config.config)
    files = {}
    for key, artifact in sorted(config.artifacts.items()):
        content = get_artifact_content(db, assignment.course.code, assignment.slug, key)
        if content is None:
            raise ValueError("Required instructor asset unavailable")
        files[key] = {"filename": artifact.display_filename or key, "type": artifact.type,
                      "sha256": hashlib.sha256(content[0]).hexdigest()}
    cases = {item.key: {"inputs": item.inputs, "outputs": item.outputs}
             for item in config.scoring_items if item.item_type == "pytest"
             and item.inputs is not None and item.outputs is not None}
    payload = {"bundle": config.bundle.model_dump(), "files": files, "cases": cases,
               "keys": sorted(item.key for item in config.scoring_items if item.item_type == "pytest"),
               "dependencies": sorted(config.dependencies), "runtime": RUNTIME_ID,
               "helper": hashlib.sha256(load_fallback_helper()).hexdigest(),
               "runner": hashlib.sha256(generate_runner_script([], {}, "").encode()).hexdigest()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inventory_status(db, assignment) -> str:
    if assignment.language != "python":
        return "ready"
    record = assignment.config.validated_test_manifest if assignment.config else None
    if record is None:
        return "missing"
    try:
        manifest = ValidatedManifest.model_validate(record)
        return "ready" if manifest.fingerprint == execution_fingerprint(db, assignment) else "stale"
    except (ValueError, ValidationError):
        return "stale"
