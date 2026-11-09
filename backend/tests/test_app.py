"""App-level contract tests: the app imports and its route table is unchanged."""

from pathlib import Path

SNAPSHOT = Path(__file__).parent / "snapshots" / "routes.txt"


def _route_table(app) -> list[str]:
    """Same format as the snapshot: ``[methods] path endpoint_name``, sorted."""
    rows = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        endpoint = getattr(route, "endpoint", None)
        name = endpoint.__name__ if endpoint is not None else ""
        rows.append((route.path, sorted(methods or ["WS"]), name))
    rows.sort(key=lambda row: (row[0], row[1]))
    return [f"{methods} {path} {name}".rstrip() for path, methods, name in rows]


def test_app_imports():
    from app.main import app

    assert app.routes


def test_route_table_matches_snapshot():
    """Protects the HTTP/WS API contract the frontend depends on.

    If a route change is intentional, regenerate tests/snapshots/routes.txt.
    """
    from app.main import app

    expected = [line.rstrip() for line in SNAPSHOT.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert _route_table(app) == expected
