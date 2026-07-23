"""Shared test fixtures: a fake async DB session and a client factory.

Route tests run fully offline — the DB session dependency is overridden with an
in-memory fake, and the LLM boundary is monkeypatched per test.
"""

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_session
from app.main import app


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    """Minimal stand-in for AsyncSession covering what the routers use."""

    def __init__(self, get_map=None, execute_values=None):
        # get_map maps (ModelClassName, pk) -> object (or missing -> None)
        self.get_map = get_map or {}
        self.execute_values = list(execute_values or [])
        self.added = []
        self._counter = 100

    async def get(self, model, pk):
        return self.get_map.get((model.__name__, pk))

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            self._counter += 1
            obj.id = self._counter

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            self._counter += 1
            obj.id = self._counter

    async def execute(self, stmt):
        value = self.execute_values.pop(0) if self.execute_values else None
        return FakeResult(value)


@pytest.fixture
def client_factory():
    """Return a factory that builds a TestClient wired to a given fake session."""

    def make(session: FakeSession) -> TestClient:
        async def _override():
            yield session

        app.dependency_overrides[get_session] = _override
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()
