"""Route-level and error-path tests (offline: fake DB session, mocked LLM)."""

from app.db.models import Extraction, Transcript
from app.errors import LLMRateLimitError, StructuredOutputError
from app.routers import extract as extract_router
from app.routers import generate as generate_router
from app.schemas.extraction import ExtractedCall
from app.schemas.generation import (
    CRMContact,
    CRMEntry,
    DealStage,
    FollowUpEmail,
    GenerateResponse,
    Priority,
    Task,
)
from tests.conftest import FakeSession

EXTRACTED = ExtractedCall.model_validate(
    {
        "participants": [{"name": "Alice", "is_primary_contact": True}],
        "summary": "Short call.",
        "key_points": ["a"],
        "decisions": [],
        "action_items": [
            {"description": "Send it", "owner": "Bob", "source_quote": "I'll send it"}
        ],
        "sentiment": "positive",
        "outcome": "Will send",
        "primary_contact_name": "Alice",
    }
)

GENERATED = GenerateResponse(
    crm=CRMEntry(
        contact=CRMContact(name="Alice"),
        deal_stage=DealStage.qualification,
        sentiment="positive",
        notes="notes",
        next_step="Send it",
        open_action_count=1,
    ),
    tasks=[
        Task(owner="Bob", description="Send it", due_date=None, priority=Priority.medium)
    ],
    email=FollowUpEmail(to="Alice", subject="Hi", body="Thanks.\n[Your name]"),
)


# --- demo UI -----------------------------------------------------------------
def test_index_serves_html(client_factory):
    client = client_factory(FakeSession())
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Voice" in r.text


# --- /extract ----------------------------------------------------------------
def test_extract_new_transcript_ok(client_factory, monkeypatch):
    async def fake_extract(_):
        return EXTRACTED

    monkeypatch.setattr(extract_router, "extract_call", fake_extract)
    client = client_factory(FakeSession())
    r = client.post("/extract", json={"transcript": "Alice: hi. Bob: I'll send it."})
    assert r.status_code == 200
    body = r.json()
    assert body["transcript_id"] and body["extraction_id"]
    assert body["extracted_call"]["primary_contact_name"] == "Alice"


def test_extract_unknown_transcript_id_404(client_factory):
    client = client_factory(FakeSession(get_map={}))
    r = client.post("/extract", json={"transcript_id": 999})
    assert r.status_code == 404


def test_extract_requires_input_422(client_factory):
    client = client_factory(FakeSession())
    r = client.post("/extract", json={})
    assert r.status_code == 422  # pydantic one-of validator


def test_extract_too_long_413(client_factory):
    client = client_factory(FakeSession())
    r = client.post("/extract", json={"transcript": "x" * 100_001})
    assert r.status_code == 413


def test_extract_structured_output_error_maps_to_502(client_factory, monkeypatch):
    async def boom(_):
        raise StructuredOutputError("bad output")

    monkeypatch.setattr(extract_router, "extract_call", boom)
    client = client_factory(FakeSession())
    r = client.post("/extract", json={"transcript": "hi"})
    assert r.status_code == 502
    assert "detail" in r.json()


def test_extract_rate_limit_maps_to_503(client_factory, monkeypatch):
    async def limited(_):
        raise LLMRateLimitError("slow down")

    monkeypatch.setattr(extract_router, "extract_call", limited)
    client = client_factory(FakeSession())
    r = client.post("/extract", json={"transcript": "hi"})
    assert r.status_code == 503


# --- /generate ---------------------------------------------------------------
def test_generate_inline_ok_not_persisted(client_factory, monkeypatch):
    async def fake_generate(_):
        return GENERATED

    monkeypatch.setattr(generate_router, "generate_all", fake_generate)
    client = client_factory(FakeSession())
    r = client.post(
        "/generate", json={"extracted_call": EXTRACTED.model_dump(mode="json")}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["generated_output_id"] is None  # inline input is not persisted
    assert body["result"]["email"]["to"] == "Alice"
    assert len(body["result"]["tasks"]) == 1


def test_generate_from_stored_extraction_ok(client_factory, monkeypatch):
    async def fake_generate(_):
        return GENERATED

    monkeypatch.setattr(generate_router, "generate_all", fake_generate)
    extraction = Extraction(
        id=7, transcript_id=1, data=EXTRACTED.model_dump(mode="json"), model="gpt-4o"
    )
    session = FakeSession(get_map={("Extraction", 7): extraction})
    client = client_factory(session)
    r = client.post("/generate", json={"extraction_id": 7})
    assert r.status_code == 200
    assert r.json()["generated_output_id"] is not None  # persisted


def test_generate_unknown_extraction_404(client_factory):
    client = client_factory(FakeSession(get_map={}))
    r = client.post("/generate", json={"extraction_id": 123})
    assert r.status_code == 404


# --- /calls ------------------------------------------------------------------
def test_get_call_found_without_extraction(client_factory):
    transcript = Transcript(id=5, source_type="text", content="hello")
    session = FakeSession(get_map={("Transcript", 5): transcript}, execute_values=[None])
    client = client_factory(session)
    r = client.get("/calls/5")
    assert r.status_code == 200
    body = r.json()
    assert body["transcript"] == "hello"
    assert body["extraction"] is None


def test_get_call_404(client_factory):
    client = client_factory(FakeSession(get_map={}))
    r = client.get("/calls/404")
    assert r.status_code == 404
