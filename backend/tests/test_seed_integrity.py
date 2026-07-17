import sys
import os
import ast
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.assignments.schemas import AssignmentConfigV1

SEEDS_DIR = BACKEND_ROOT / "app" / "db" / "seeds"

def get_assignment_seed_dirs() -> list[Path]:
    if not SEEDS_DIR.exists():
        return []
    return [d for d in SEEDS_DIR.iterdir() if d.is_dir() and d.name != "shared"]

@pytest.mark.parametrize("seed_dir", get_assignment_seed_dirs(), ids=lambda d: d.name)
def test_seed_directory_integrity(seed_dir: Path) -> None:
    config_file = seed_dir / "config_json.example.json"
    assert config_file.exists(), f"Missing config_json.example.json in {seed_dir.name}"

    # 1. Parse and validate config schema
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    try:
        AssignmentConfigV1.model_validate(config_data)
    except ValidationError as exc:
        pytest.fail(f"Config validation failed for {seed_dir.name}: {exc}")

    # 2. Check that all files referenced in config artifacts exist in the seed folder or shared
    artifacts = config_data.get("artifacts", {})
    for art_name, art_config in artifacts.items():
        filename = art_config.get("display_filename")
        if filename:
            ref_file = seed_dir / filename
            shared_file = SEEDS_DIR / "shared" / filename
            if art_config.get("type") == "model_solution" and not ref_file.exists():
                ref_file = seed_dir / "model_solution.py"
            assert ref_file.exists() or shared_file.exists(), (
                f"Artifact '{art_name}' file '{filename}' listed in config is missing from both the "
                f"seed folder '{seed_dir.name}' and the shared seeds folder."
            )

    # 3. Static checks on all Python files in the seed folder
    py_files = list(seed_dir.glob("*.py"))
    for py_file in py_files:
        # Exclude temporary or scratch files
        if py_file.name.startswith("temp_") or py_file.name.startswith("."):
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            code_content = f.read()

        try:
            tree = ast.parse(code_content, filename=str(py_file))
        except SyntaxError as exc:
            pytest.fail(f"Syntax error in seed Python file {py_file.name}: {exc}")

        # Check A: No unquoted self-referencing return type annotations in class definitions
        class SelfReferenceVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.current_class = None
                self.errors = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                if self.current_class and node.returns:
                    if isinstance(node.returns, ast.Name) and node.returns.id == self.current_class:
                        self.errors.append(
                            f"{py_file.name}:{node.lineno}: Return annotation for '{node.name}' "
                            f"uses unquoted self-reference '{self.current_class}', causing runtime NameError. "
                            f"Use '\"{self.current_class}\"' (quoted string) instead."
                        )
                self.generic_visit(node)

        visitor = SelfReferenceVisitor()
        visitor.visit(tree)
        if visitor.errors:
            pytest.fail("\n".join(visitor.errors))

        is_test_file = (
            py_file.name == "tests.py"
            or py_file.name.startswith("test_")
            or py_file.name.endswith("_tests.py")
            or py_file.name.endswith("_test.py")
        )
        is_typed_assignment = seed_dir.name.startswith("ds") or "lab6" in seed_dir.name
        if is_typed_assignment and not is_test_file:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip standard dunder methods
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue
                    if not node.returns:
                        pytest.fail(
                            f"{py_file.name}:{node.lineno}: Function '{node.name}' is missing a return "
                            f"type annotation (e.g. '-> None')."
                        )
