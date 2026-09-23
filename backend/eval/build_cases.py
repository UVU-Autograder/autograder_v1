"""Generate eval cases by grading mutated model solutions with the real grader.

    cd backend && python -m eval.build_cases            # write eval/cases/gen_*.json
    cd backend && python -m eval.build_cases --check    # just verify seeds + mutations
    cd backend && python -m eval.build_cases --split train   # Phase 2 inputs -> training/p2/cases

Each case starts from a seed assignment's model solution, applies one mutation
from ``eval/mutations.py`` (a typical student bug), and runs the production
``GradingEngine`` on it -- bundle validation, AST concept checks, test
injection, the generated Judge0 runner script, ``calculate_scores``. Only the
Judge0 call is replaced, by a local subprocess running the same runner script.
The model input is then built exactly as the live sandbox builds it
(``prompts.failures_from_test_results``, ``requirements_from_config``, AST
warnings as concept violations, the bundle's files as ``code_files``).

So every failure message, scoring key and concept warning in a generated case is
one the real grader produced -- while all code is synthetic (a mutated model
solution), which keeps student data out of the eval set and, later, out of
training data built the same way.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import resolve_seed_artifact_path
from app.domains.grading import engine as grading_engine
from app.domains.grading.executor import ExecutionOutcome
from app.domains.grading.result_parser import parse_pytest_json
from app.domains.grading.runner_gen import generate_runner_script
from app.integrations.ai.guardrails import DEF_RE
from app.integrations.ai.prompts import failures_from_test_results, requirements_from_config

from eval.mutations import MUTATIONS, TRAIN_MUTATIONS

BACKEND = Path(__file__).resolve().parents[1]
SEEDS = BACKEND / "app" / "db" / "seeds"
CASES_DIR = Path(__file__).parent / "cases"
TRAIN_CASES_DIR = BACKEND / "training" / "p2" / "cases"
SPLITS = {"eval": (MUTATIONS, CASES_DIR), "train": (TRAIN_MUTATIONS, TRAIN_CASES_DIR)}
COURSE_DEFAULT_CONCEPTS = ["variables", "conditionals", "loops", "functions"]  # cs1410 in app/db/seed.py


def _catalog() -> dict:
    return json.loads((SEEDS / "cs1410_catalog.json").read_text())


def seed_dir_for(slug: str) -> Path:
    return SEEDS / slug.replace("-", "_")


def assignment_meta(slug: str) -> tuple[str, list[str]]:
    """(title, allowed_concepts) exactly as app/db/seed.py derives them for cs1410."""
    catalog = _catalog()
    entry = next(a for a in catalog["assignments"] if a["slug"] == slug)
    concepts: list[str] = list(COURSE_DEFAULT_CONCEPTS)
    for code, module in catalog["modules"].items():
        for concept in module.get("concepts", []):
            if concept not in concepts:
                concepts.append(concept)
        if code == entry["module"]:
            break
    return entry["title"], concepts


def load_config(slug: str) -> tuple[AssignmentConfigV1, dict]:
    raw = json.loads((seed_dir_for(slug) / "config_json.example.json").read_text())
    return AssignmentConfigV1.model_validate(raw), raw


# --- local stand-in for Judge0: same runner script, local subprocess ---------


async def _local_execute(
    exec_dir: Path,
    *,
    test_filenames: list[str],
    test_cases: dict,
    entrypoint_module: str,
    language_id: int,
    cpu_time_limit: float,
    dependencies: list[str] | None = None,
    memory_limit: int = 262144,
    stdin: str | None = None,
) -> ExecutionOutcome:
    outcome = ExecutionOutcome()
    (exec_dir / "runner.py").write_text(
        generate_runner_script(test_filenames, test_cases, entrypoint_module, dependencies)
    )
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(exec_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "MPLBACKEND": "Agg",
    }
    for k in ("SYSTEMROOT", "SystemDrive", "TEMP", "TMP", "COMSPEC", "PATHEXT"):
        if k in os.environ:
            env[k] = os.environ[k]
    try:
        proc = subprocess.run(
            [sys.executable, "runner.py"],
            cwd=exec_dir,
            input=stdin or "",
            capture_output=True,
            text=True,
            timeout=max(30.0, cpu_time_limit * 3),
            env=env,
        )
    except subprocess.TimeoutExpired:
        outcome.failure_category = "timeout"
        outcome.failure_message = "Time limit exceeded"
        return outcome
    result = parse_pytest_json(proc.stdout)
    outcome.pytest_result = result
    if result.error_message:  # mirrors executor.execute_pytest_in_judge0
        outcome.failure_category = "test_failure"
        outcome.failure_message = result.error_message
        return outcome
    outcome.success = True
    return outcome


def grade_bundle(slug: str, bundle: Path):
    config, _ = load_config(slug)
    # Same resolution as the seeder (assignments.service): falls back to seeds/shared/.
    refs = {}
    for key, art in config.artifacts.items():
        if art.type == "model_solution" or not art.display_filename:
            continue
        resolved = resolve_seed_artifact_path(seed_dir_for(slug), art.display_filename, artifact_type=art.type)
        if resolved is not None:
            folder = "shared" if resolved.parent.name == "shared" else seed_dir_for(slug).name
            refs[key] = f"seed://{folder}/{resolved.name}"
    _, concepts = assignment_meta(slug)
    original = grading_engine.execute_pytest_in_judge0
    grading_engine.execute_pytest_in_judge0 = _local_execute
    try:
        return grading_engine.GradingEngine(config, refs, concepts).grade_submission_sync(bundle_dir=bundle)
    finally:
        grading_engine.execute_pytest_in_judge0 = original


def model_files(slug: str) -> dict[str, str]:
    config, _ = load_config(slug)
    out = {}
    for art in config.artifacts.values():
        if art.type == "model_solution" and art.display_filename:
            path = seed_dir_for(slug) / art.display_filename
            if path.suffix in {".py", ".md", ".txt"}:
                out[art.display_filename] = path.read_text()
    return out


def binary_model_files(slug: str) -> list[Path]:
    config, _ = load_config(slug)
    return [
        seed_dir_for(slug) / art.display_filename
        for art in config.artifacts.values()
        if art.type == "model_solution"
        and art.display_filename
        and (seed_dir_for(slug) / art.display_filename).suffix not in {".py", ".md", ".txt"}
    ]


def apply_mutation(files: dict[str, str], mutation: dict) -> dict[str, str]:
    files = dict(files)
    for edit in mutation.get("edits", []):
        name = edit["file"]
        if "replace_all" in edit:
            files[name] = edit["replace_all"]
            continue
        if edit["find"] not in files[name]:
            raise ValueError(f"{mutation['case_id']}: {edit['find']!r} not found in {name}")
        files[name] = files[name].replace(edit["find"], edit["replace"], edit.get("count", 1))
    return files


def bug_diff(original: dict[str, str], mutated: dict[str, str]) -> str:
    """Unified diff of the mutation: the ground truth a reviewer checks feedback against."""
    out: list[str] = []
    for name in sorted(set(original) | set(mutated)):
        before, after = original.get(name, ""), mutated.get(name, "")
        if before != after:
            out += difflib.unified_diff(
                before.splitlines(keepends=True), after.splitlines(keepends=True),
                fromfile=f"model/{name}", tofile=f"student/{name}", n=2,
            )
    return "".join(out)


def build_case(mutation: dict) -> tuple[dict | None, str]:
    slug = mutation["seed"]
    original = model_files(slug)
    files = apply_mutation(original, mutation)
    with tempfile.TemporaryDirectory(prefix="agcase_") as tmp:
        bundle = Path(tmp)
        for name, text in files.items():
            (bundle / name).write_text(text)
        for path in binary_model_files(slug):
            shutil.copy(path, bundle / path.name)
        result = grade_bundle(slug, bundle)

    failure_message = None if result.success else (result.failure_message or result.failure_category)
    test_results = result.test_results if result.success else []
    failures, passing = failures_from_test_results(test_results, failure_message)
    violations = [f"{w.get('code', 'warning')}: {w.get('message', '')}" for w in result.warnings]

    expect = mutation["category"]
    if expect == "all_pass" and failures:
        return None, f"expected all_pass, got failures {[f['key'] for f in failures]}"
    if expect == "concept_violation" and not violations:
        return None, "expected a concept violation, AST checker reported none"
    if expect not in ("all_pass", "concept_violation") and not failures:
        return None, "mutation had no effect: grader reported no failures"

    title, concepts = assignment_meta(slug)
    config, raw = load_config(slug)
    code_files = {n: t for n, t in files.items() if n.endswith(".py")}
    case = {
        "case_id": mutation["case_id"],
        "category": expect,
        "assignment_slug": slug,
        "assignment_title": title,
        "requirements": requirements_from_config(raw),
        "allowed_concepts": concepts,
        "failures": failures,
        "passing_labels": passing,
        "concept_violations": violations,
        "student_code": "",
        "code_files": code_files,
        "forbidden_identifiers": sorted({n for t in code_files.values() for n in DEF_RE.findall(t)}),
        "injection_canaries": mutation.get("canaries", []),
        "notes": f"generated by eval.build_cases: {mutation.get('notes', '')}".strip(),
        "bug_diff": bug_diff(original, files),
    }
    summary = f"{len(failures)} failure(s) {[f['key'] for f in failures]}" + (
        f", {len(violations)} violation(s)" if violations else ""
    )
    return case, summary


def check_seeds(slugs: list[str]) -> int:
    """Unmutated model solutions must grade clean -- otherwise the harness itself is off."""
    bad = 0
    for slug in slugs:
        with tempfile.TemporaryDirectory(prefix="agseed_") as tmp:
            bundle = Path(tmp)
            for name, text in model_files(slug).items():
                (bundle / name).write_text(text)
            for path in binary_model_files(slug):
                shutil.copy(path, bundle / path.name)
            result = grade_bundle(slug, bundle)
        failures, _ = failures_from_test_results(result.test_results if result.success else [],
                                                 None if result.success else result.failure_message)
        status = "ok  " if result.success and not failures else "FAIL"
        bad += status == "FAIL"
        detail = "" if status == "ok  " else f" {result.failure_category}: {result.failure_message} {[f['key'] for f in failures]}"
        print(f"  {status} {slug:24} {result.score}/{result.max_score}{detail}")
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="grade unmutated seeds and dry-run mutations; write nothing")
    parser.add_argument("--only", default="", help="only mutations whose case_id contains this")
    parser.add_argument("--split", choices=sorted(SPLITS), default="eval",
                        help="eval: eval/cases (frozen fixtures); train: training/p2/cases (Phase 2 inputs)")
    args = parser.parse_args(argv)
    mutations, out_dir = SPLITS[args.split]

    seeds = sorted({m["seed"] for m in mutations})
    print("baseline: unmutated model solutions")
    if check_seeds(seeds):
        print("a model solution does not grade clean locally; fix that before trusting generated cases")
        return 1

    written = skipped = 0
    for mutation in mutations:
        if args.only not in mutation["case_id"]:
            continue
        try:
            case, summary = build_case(mutation)
        except Exception as exc:  # noqa: BLE001 - report and continue
            case, summary = None, f"error: {type(exc).__name__}: {exc}"
        if case is None:
            skipped += 1
            print(f"  SKIP {mutation['case_id']}: {summary}")
            continue
        written += 1
        print(f"  ok   {mutation['case_id']}: {summary}")
        if not args.check:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{mutation['case_id']}.json").write_text(json.dumps(case, indent=2) + "\n")
    print(f"\n{written} case(s) {'validated' if args.check else 'written'}, {skipped} skipped")
    return 1 if skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
