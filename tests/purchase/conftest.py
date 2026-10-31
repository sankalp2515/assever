import pytest
import os

if not os.environ.get("DATABASE_URL"):
    collect_ignore_glob = ["test_*.py"]  # Dedicated Docker job supplies the required PostgreSQL/provider services.


@pytest.fixture(autouse=True)
def component_boundary(monkeypatch, request):
    # Pure component cases intentionally create unbound synthetic roots. HTTP
    # integration cases use the running gateway with workflow binding enforced.
    if request.node.path.name != "test_gateway.py":
        monkeypatch.setenv("INTEGRATED_REQUIRE_WORKFLOW", "0")
