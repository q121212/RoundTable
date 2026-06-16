"""Lightweight, deterministic guards on the project's layering rules.

These parse source with the stdlib `ast` module (no imports executed, no
external dependencies) and fail if a future change reintroduces a forbidden
dependency direction or turns the store facade back into a logic module.

See docs/architecture.md for the rules these enforce.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
STORE = APP / "store"


def _imports(path):
    """Parse a module and classify its imports.

    Returns (store_siblings, imports_store_facade, app_absolute) where:
      * store_siblings   = sibling store submodules imported via `from ._x import`
      * imports_store_facade = True if it imports the package facade
        (`from . import ...` from inside store, or absolute `app.store`)
      * app_absolute     = absolute app.* modules imported (e.g. app.main)
    """
    tree = ast.parse(path.read_text())
    siblings = set()
    facade = False
    app_absolute = set()
    inside_store = path.parent.name == "store"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 1:
                if node.module is None and inside_store:
                    facade = True  # `from . import X` -> the store package __init__
                elif node.module and node.module.startswith("_"):
                    siblings.add(node.module)
            elif node.level == 0 and node.module:
                if node.module == "app.store":
                    facade = True
                if node.module == "app.main" or node.module.startswith("app.main."):
                    app_absolute.add(node.module)
                if node.module == "app.store" or node.module.startswith("app.store."):
                    app_absolute.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.main" or alias.name.startswith("app.main."):
                    app_absolute.add(alias.name)
                if alias.name == "app.store" or alias.name.startswith("app.store."):
                    app_absolute.add(alias.name)
    return siblings, facade, app_absolute


def _store_submodules():
    return sorted(p.stem for p in STORE.glob("_*.py"))


def test_store_init_is_facade_only():
    """store/__init__.py may only contain a docstring and import/re-export
    statements — never function or class definitions or other logic."""
    tree = ast.parse((STORE / "__init__.py").read_text())
    offending = [
        type(node).__name__
        for node in tree.body
        if not isinstance(node, (ast.Import, ast.ImportFrom))
        and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
    ]
    assert offending == [], "store/__init__.py must be facade-only; found statements: %s" % offending


def test_no_store_submodule_imports_the_facade():
    offenders = [p.name for p in STORE.glob("_*.py") if _imports(p)[1]]
    assert offenders == [], "store submodules must not import the app.store facade: %s" % offenders


def test_no_store_submodule_imports_app_main():
    offenders = {p.name: _imports(p)[2] for p in STORE.glob("*.py") if _imports(p)[2]}
    # The facade re-exports submodules; nothing under app/store may import app.main.
    main_importers = {k: v for k, v in offenders.items() if any("app.main" in m for m in v)}
    assert main_importers == {}, "app/store must never import app.main: %s" % main_importers


def test_store_submodule_graph_is_acyclic():
    graph = {m: _imports(STORE / (m + ".py"))[0] for m in _store_submodules()}
    color = dict.fromkeys(graph, 0)  # 0=white 1=gray 2=black

    def visits(node):
        color[node] = 1
        for dep in graph.get(node, ()):
            if color.get(dep, 0) == 1:
                return True
            if color.get(dep, 0) == 0 and visits(dep):
                return True
        color[node] = 2
        return False

    cyclic = any(color[m] == 0 and visits(m) for m in graph)
    assert not cyclic, "import cycle detected among app.store submodules"


def test_forbidden_store_edges():
    """Layer-violating edges that would reintroduce the notifications<->tickets
    cycle or make the read layer non-read-only."""
    forbidden = {
        "_read_models": {"_tickets", "_projects", "_notification_outbox", "_action_log"},
        "_notification_outbox": {"_tickets"},
        "_action_log": {"_tickets"},
    }
    for module, banned in forbidden.items():
        siblings = _imports(STORE / (module + ".py"))[0]
        bad = siblings & banned
        assert not bad, "%s must not import %s" % (module, ", ".join(sorted(bad)))


def test_db_and_security_stay_infra_only():
    """db.py and security.py are low-level infra and must not depend on app.main
    or the store domain modules."""
    for fname in ["db.py", "security.py"]:
        tree = ast.parse((APP / fname).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                assert node.module not in {"main", "store"} and not node.module.startswith("store."), (
                    "app/%s must not import app.%s" % (fname, node.module)
                )
        _, _, app_absolute = _imports(APP / fname)
        assert app_absolute == set(), "app/%s must not import %s" % (fname, app_absolute)
