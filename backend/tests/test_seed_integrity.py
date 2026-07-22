import ast
import json
import sys
from pathlib import Path

import pytest
import packaging
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.seed import SEEDS_DIR, resolve_seed_artifact_path
from app.db.seeds.shared.python_autograder_helpers import import_student_modules
from app.domains.assignments.schemas import AssignmentConfigV1

TYPED_ASSIGNMENTS = frozenset(
    {"ds1", "ds2", "ds3", "ds4", "ds5", "ds6", "ds7", "ds8", "ds9", "ds10", "lab6"}
)


class SelfReferenceVisitor(ast.NodeVisitor):
    """Flag unquoted self-referencing return annotations that raise NameError at runtime."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.current_class: str | None = None
        self.errors: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if (
            self.current_class
            and node.returns
            and isinstance(node.returns, ast.Name)
            and node.returns.id == self.current_class
        ):
            self.errors.append(
                f"{self.filename}:{node.lineno}: Return annotation for '{node.name}' "
                f"uses unquoted self-reference '{self.current_class}', causing runtime NameError. "
                f"Use '\"{self.current_class}\"' (quoted string) instead."
            )
        self.generic_visit(node)


def get_assignment_seed_dirs() -> list[Path]:
    if not SEEDS_DIR.exists():
        return []
    return [d for d in SEEDS_DIR.iterdir() if d.is_dir() and d.name != "shared"]


@pytest.mark.parametrize("seed_dir", get_assignment_seed_dirs(), ids=lambda d: d.name)
def test_seed_directory_integrity(seed_dir: Path) -> None:
    config_file = seed_dir / "config_json.example.json"
    assert config_file.exists(), f"Missing config_json.example.json in {seed_dir.name}"

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    try:
        config = AssignmentConfigV1.model_validate(config_data)
    except ValidationError as exc:
        pytest.fail(f"Config validation failed for {seed_dir.name}: {exc}")

    artifacts = config_data.get("artifacts", {})
    model_filenames = {
        artifact.display_filename
        for artifact in config.artifacts.values()
        if artifact.type == "model_solution" and artifact.display_filename
    }
    assert config.bundle.entrypoint in model_filenames, (
        f"{seed_dir.name} is missing model solution artifact for entrypoint '{config.bundle.entrypoint}'"
    )

    for req in config.bundle.file_requirements:
        if req.paths:
            assert any(p in model_filenames for p in req.paths), (
                f"{seed_dir.name} is missing model solution artifact for file requirement '{req.label}' (none of {req.paths} found)"
            )


    for art_name, art_config in artifacts.items():
        filename = art_config.get("display_filename")
        if not filename:
            continue
        resolved = resolve_seed_artifact_path(
            seed_dir,
            filename,
            artifact_type=art_config.get("type"),
        )
        assert resolved is not None, (
            f"Artifact '{art_name}' file '{filename}' listed in config is missing from both the "
            f"seed folder '{seed_dir.name}' and the shared seeds folder."
        )

    py_files = list(seed_dir.glob("*.py"))
    for py_file in py_files:
        if py_file.name.startswith("temp_") or py_file.name.startswith("."):
            continue

        code_content = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(code_content, filename=str(py_file))
        except SyntaxError as exc:
            pytest.fail(f"Syntax error in seed Python file {py_file.name}: {exc}")

        visitor = SelfReferenceVisitor(py_file.name)
        visitor.visit(tree)
        if visitor.errors:
            pytest.fail("\n".join(visitor.errors))

        is_test_file = (
            py_file.name == "tests.py"
            or py_file.name.startswith("test_")
            or py_file.name.endswith("_tests.py")
            or py_file.name.endswith("_test.py")
        )
        if seed_dir.name in TYPED_ASSIGNMENTS and not is_test_file:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue
                    if not node.returns:
                        pytest.fail(
                            f"{py_file.name}:{node.lineno}: Function '{node.name}' is missing a return "
                            f"type annotation (e.g. '-> None')."
                        )


def test_student_module_import_restores_packaging_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    system_packaging = packaging
    (tmp_path / "packaging.py").write_text("MARKER = 'student'\n")
    (tmp_path / "dessert.py").write_text(
        "import packaging\nMARKER = packaging.MARKER\n"
    )
    monkeypatch.chdir(tmp_path)

    student_packaging, dessert = import_student_modules("packaging", "dessert")

    assert student_packaging.MARKER == "student"
    assert dessert.MARKER == "student"
    assert sys.modules["packaging"] is system_packaging
