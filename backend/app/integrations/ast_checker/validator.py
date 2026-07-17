"""AST-based concept whitelist validator for student submissions.

Parses student Python source code using the ``ast`` module, detects which
programming concepts are present, and compares them against an allowed
whitelist.  Security-sensitive constructs (dangerous imports, eval/exec, etc.)
are always blocked regardless of the whitelist.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Concept-to-node mapping
# ---------------------------------------------------------------------------

CONCEPT_DETAILS: dict[str, dict] = {
    "loops": {
        "title": "Loops",
        "syntax_patterns": ["for loops", "while loops", "async for loops"],
        "nodes": (ast.For, ast.While, ast.AsyncFor),
    },
    "conditionals": {
        "title": "Conditionals",
        "syntax_patterns": [
            "if / elif / else statements",
            "Comparison operators (<, >, ==, etc.)",
            "Ternary inline if expressions",
        ],
        "nodes": (ast.If, ast.Compare, ast.IfExp),
    },
    "functions": {
        "title": "Functions",
        "syntax_patterns": [
            "Custom function declarations (def)",
            "Custom async function declarations (async def)",
        ],
        "nodes": (ast.FunctionDef, ast.AsyncFunctionDef),
    },
    "variables": {
        "title": "Variables",
        "syntax_patterns": [
            "Variable declarations & assignments",
            "Type-annotated variable assignments",
        ],
        "nodes": (ast.Assign, ast.AnnAssign),
    },
    "classes": {
        "title": "Classes",
        "syntax_patterns": ["Class definitions (class)"],
        "nodes": (ast.ClassDef,),
    },
    "inheritance": {
        "title": "Inheritance",
        "syntax_patterns": ["Class definitions inheriting from base classes"],
        "nodes": (),
    },
    "abstract-classes": {
        "title": "Abstract Classes",
        "syntax_patterns": ["Defining or inheriting from ABC, using @abstractmethod"],
        "nodes": (),
    },
    "properties": {
        "title": "Properties",
        "syntax_patterns": ["Using @property decorator or property() function"],
        "nodes": (),
    },
    "generators": {
        "title": "Generators",
        "syntax_patterns": ["Using yield or yield from in functions"],
        "nodes": (ast.Yield, ast.YieldFrom),
    },
    "testing": {
        "title": "Testing",
        "syntax_patterns": ["Importing pytest, writing test_ functions"],
        "nodes": (),
    },
    "exceptions": {
        "title": "Exceptions",
        "syntax_patterns": ["try/except blocks, raising exceptions, custom exceptions"],
        "nodes": (ast.Try, ast.Raise),
    },
    "pygame": {
        "title": "Pygame",
        "syntax_patterns": ["Importing or using pygame library"],
        "nodes": (),
    },
    "dataclasses": {
        "title": "Data Classes",
        "syntax_patterns": ["Using @dataclass decorator"],
        "nodes": (),
    },
    "protocols": {
        "title": "Protocols",
        "syntax_patterns": ["Inheriting from Protocol, using @runtime_checkable"],
        "nodes": (),
    },
    "type-hints": {
        "title": "Type Hints",
        "syntax_patterns": ["Function annotations, variable annotations, typing imports"],
        "nodes": (ast.AnnAssign,),
    },
    "operator-overloading": {
        "title": "Operator Overloading",
        "syntax_patterns": ["Defining special methods like __add__, __eq__, etc."],
        "nodes": (),
    },
    "file-io": {
        "title": "File I/O",
        "syntax_patterns": [
            "Opening files with open()",
            "Reading/writing files with .read()/.write()/.readlines()",
            "using 'with open()' context managers",
        ],
        "nodes": (),
    },
    "image-processing": {
        "title": "Image Processing",
        "syntax_patterns": [
            "Importing PIL / Pillow library",
            "Executing operations using Image, ImageDraw, ImageFilter",
        ],
        "nodes": (),
    },
}

CONCEPT_NODE_MAP: dict[str, tuple[type, ...]] = {
    k: v["nodes"] for k, v in CONCEPT_DETAILS.items() if v["nodes"]
}

# ---------------------------------------------------------------------------
# Security deny-lists
# ---------------------------------------------------------------------------

BLOCKED_IMPORTS: frozenset[str] = frozenset(
    {
        "subprocess",
        "os",
        "shutil",
        "socket",
        "http",
        "urllib",
        "ctypes",
        "multiprocessing",
        "importlib",
    }
)

BLOCKED_CALLS: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "__import__",
        "compile",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
    }
)

# Methods whose invocation signals the ``file-io`` concept.
_FILE_IO_METHODS: frozenset[str] = frozenset(
    {
        "read",
        "write",
        "readlines",
        "writelines",
    }
)


# ---------------------------------------------------------------------------
# Result data-classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ASTFinding:
    """A single finding emitted by the AST checker.

    Attributes:
        code: A machine-readable identifier, e.g. ``concept_warning`` or
            ``concept_blocked``.
        message: A human-readable explanation of the finding.
        line: The 1-based line number in the source, or ``None`` when the
            line is not applicable (e.g. syntax errors reported without a
            location).
    """

    code: str
    message: str
    line: int | None = None


@dataclass(slots=True)
class ASTCheckResult:
    """Aggregate result of checking a student submission.

    Attributes:
        detected_concepts: The set of concept keys found in the source.
        warnings: Findings with code ``concept_warning`` – concepts that
            are used but not on the allowed list.
        blocked: Findings with code ``concept_blocked`` or ``syntax_error``
            – security violations or unparsable code.
        is_blocked: Convenience flag – ``True`` when *blocked* is non-empty.
    """

    detected_concepts: set[str] = field(default_factory=set)
    warnings: list[ASTFinding] = field(default_factory=list)
    blocked: list[ASTFinding] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return len(self.blocked) > 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _call_name(node: ast.Call) -> str | None:
    """Return the simple name of a call target, or ``None``.

    Handles plain names (``open(...)``) and single-level attribute access
    (``Image.open(...)``).
    """
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _import_module_roots(node: ast.Import | ast.ImportFrom) -> list[str]:
    """Return the top-level module names touched by an import statement."""
    if isinstance(node, ast.ImportFrom):
        if node.module:
            return [node.module.split(".")[0]]
        return []
    # ast.Import
    return [alias.name.split(".")[0] for alias in node.names]


# ---------------------------------------------------------------------------
# Core walker
# ---------------------------------------------------------------------------


def _walk(tree: ast.AST) -> tuple[set[str], list[ASTFinding], list[ASTFinding]]:
    """Walk *tree* and return ``(detected, warnings_list, blocked_list)``.

    *warnings_list* is populated later by the caller once the whitelist is
    known – here we only collect *detected* concepts and *blocked* findings.
    """

    detected: set[str] = set()
    blocked: list[ASTFinding] = []

    for node in ast.walk(tree):
        # ---- simple concept nodes (loops, conditionals, functions, vars) --
        for concept, node_types in CONCEPT_NODE_MAP.items():
            if isinstance(node, node_types):
                # Special check: raise StopIteration is allowed for iterators (Module 4)
                # and should not trigger the 'exceptions' concept.
                if concept == "exceptions" and isinstance(node, ast.Raise):
                    is_stop_iteration = False
                    if node.exc:
                        if isinstance(node.exc, ast.Name) and node.exc.id == "StopIteration":
                            is_stop_iteration = True
                        elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name) and node.exc.func.id == "StopIteration":
                            is_stop_iteration = True
                    if is_stop_iteration:
                        continue
                detected.add(concept)

        # ---- imports -------------------------------------------------
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            roots = _import_module_roots(node)
            for root in roots:
                if root in BLOCKED_IMPORTS:
                    blocked.append(
                        ASTFinding(
                            code="concept_blocked",
                            message=f"Blocked import: '{root}'",
                            line=node.lineno,
                        )
                    )
                if root == "PIL":
                    detected.add("image-processing")
                if root == "pygame":
                    detected.add("pygame")
                if root == "pytest":
                    detected.add("testing")
                if root == "dataclasses":
                    detected.add("dataclasses")
                if root in ("typing", "typing_extensions"):
                    detected.add("type-hints")

        # ---- ClassDef ------------------------------------------------
        if isinstance(node, ast.ClassDef):
            detected.add("classes")
            if len(node.bases) > 0:
                detected.add("inheritance")
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "ABC":
                        detected.add("abstract-classes")
                    elif isinstance(base, ast.Attribute) and base.attr == "ABC":
                        detected.add("abstract-classes")
                    elif isinstance(base, ast.Name) and base.id == "Protocol":
                        detected.add("protocols")
                    elif isinstance(base, ast.Attribute) and base.attr == "Protocol":
                        detected.add("protocols")
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "dataclass":
                    detected.add("dataclasses")
                elif isinstance(dec, ast.Attribute) and dec.attr == "dataclass":
                    detected.add("dataclasses")
                elif isinstance(dec, ast.Name) and dec.id == "runtime_checkable":
                    detected.add("protocols")
                elif isinstance(dec, ast.Attribute) and dec.attr == "runtime_checkable":
                    detected.add("protocols")

        # ---- FunctionDef / AsyncFunctionDef --------------------------
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                detected.add("type-hints")
            for arg in node.args.args:
                if arg.annotation is not None:
                    detected.add("type-hints")
            for arg in node.args.kwonlyargs:
                if arg.annotation is not None:
                    detected.add("type-hints")
            if node.args.vararg and node.args.vararg.annotation is not None:
                detected.add("type-hints")
            if node.args.kwarg and node.args.kwarg.annotation is not None:
                detected.add("type-hints")

            if node.name.startswith("test_"):
                detected.add("testing")

            special_operator_methods = {
                "__add__", "__radd__", "__iadd__",
                "__sub__", "__rsub__", "__isub__",
                "__mul__", "__rmul__", "__imul__",
                "__truediv__", "__rtruediv__", "__itruediv__",
                "__floordiv__", "__rfloordiv__", "__ifloordiv__",
                "__mod__", "__rmod__", "__imod__",
                "__pow__", "__rpow__", "__ipow__",
                "__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__",
                "__and__", "__rand__", "__iand__",
                "__or__", "__ror__", "__ior__",
                "__xor__", "__rxor__", "__ixor__",
                "__lshift__", "__rlshift__", "__ilshift__",
                "__rshift__", "__rrshift__", "__irshift__",
                "__neg__", "__pos__", "__abs__", "__invert__",
            }
            if node.name in special_operator_methods:
                detected.add("operator-overloading")

            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "property":
                    detected.add("properties")
                elif isinstance(dec, ast.Attribute) and dec.attr == "property":
                    detected.add("properties")
                elif isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                    detected.add("abstract-classes")
                elif isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod":
                    detected.add("abstract-classes")

        # ---- calls ---------------------------------------------------
        if isinstance(node, ast.Call):
            name = _call_name(node)

            # Security-blocked calls
            if name and name in BLOCKED_CALLS:
                blocked.append(
                    ASTFinding(
                        code="concept_blocked",
                        message=f"Blocked call: '{name}()'",
                        line=node.lineno,
                    )
                )

            # file-io: direct ``open(...)`` call
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                detected.add("file-io")

            # file-io: ``.read()``, ``.write()``, etc.
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in _FILE_IO_METHODS:
                    detected.add("file-io")

            # image-processing: calls on PIL objects (e.g. Image.open)
            if isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name
            ):
                if node.func.value.id in ("Image", "ImageDraw", "ImageFilter"):
                    detected.add("image-processing")

            # properties: call to property()
            if isinstance(node.func, ast.Name) and node.func.id == "property":
                detected.add("properties")

        # ---- with-item open() ----------------------------------------
        if isinstance(node, ast.withitem):
            ctx = node.context_expr
            if isinstance(ctx, ast.Call):
                if isinstance(ctx.func, ast.Name) and ctx.func.id == "open":
                    detected.add("file-io")

    return detected, [], blocked


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_student_code(
    source_code: str,
    allowed_concepts: list[str],
) -> ASTCheckResult:
    """Parse *source_code* and validate against *allowed_concepts*.

    Parameters:
        source_code: The raw Python source text submitted by the student.
        allowed_concepts: Concept keys (e.g. ``["variables", "loops"]``)
            that the student is permitted to use.  Any detected concept
            **not** on this list will produce a ``concept_warning`` finding.

    Returns:
        An :class:`ASTCheckResult` summarising detected concepts, warnings,
        and blocked findings.
    """

    # ----- 1. Parse -------------------------------------------------------
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return ASTCheckResult(
            blocked=[
                ASTFinding(
                    code="syntax_error",
                    message=f"Could not parse source: {exc.msg}",
                    line=exc.lineno,
                )
            ],
        )

    # ----- 2. Walk the AST ------------------------------------------------
    detected, _, blocked = _walk(tree)

    # ----- 3. Build warnings for concepts not in the whitelist ------------
    allowed_set = set(allowed_concepts)
    warnings: list[ASTFinding] = []
    for concept in sorted(detected - allowed_set):
        warnings.append(
            ASTFinding(
                code="concept_warning",
                message=f"Concept '{concept}' is not in the allowed list",
            )
        )

    return ASTCheckResult(
        detected_concepts=detected,
        warnings=warnings,
        blocked=blocked,
    )


def get_concepts_metadata() -> dict[str, dict]:
    """Return JSON-serializable concept definitions and checked rules."""
    return {
        k: {
            "key": k,
            "title": v["title"],
            "syntax_patterns": v["syntax_patterns"],
            "nodes": [node.__name__ for node in v["nodes"]],
        }
        for k, v in CONCEPT_DETAILS.items()
    }
