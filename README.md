# Voice-to-Structured-Data Agent

Turn call/meeting transcripts (or audio) into structured, actionable output: a
**CRM entry**, a **task list**, and a **follow-up email draft** — generated from a
single extracted structure so the three deliverables stay consistent and cheap.

Sales and support calls generate information that usually stays trapped in a
transcript. This service extracts the structure once (participants, decisions,
action items, sentiment) and derives every deliverable from that structure rather
than re-reading the raw transcript per output.

## Architecture

```mermaid
flowchart LR
    A[Audio file] -->|POST /transcribe<br/>Whisper| B[Transcript]
    T[Plain-text transcript] --> B
    B -->|POST /extract<br/>gpt-4o + JSON schema| C[ExtractedCall<br/>participants, decisions,<br/>action items, sentiment]
    C -->|POST /generate| D{Three generators<br/>consume the structure}
    D --> E[CRM entry]
    D --> F[Task list]
    D --> G[Follow-up email]
    B --> P[(Postgres)]
    C --> P
    E --> P
    F --> P
    G --> P
    P -->|GET /calls/id| Q[Queryable past calls]
```

- **Ingestion** — accept raw audio (Whisper transcription) or plain-text transcripts.
- **Extraction** — one LLM call with structured JSON-schema output produces
  `ExtractedCall`. Every decision/action item carries a `source_quote` to anchor it
  to the transcript and discourage hallucination.
- **Generation** — three focused generators (CRM / tasks / email) each consume the
  `ExtractedCall` structure (never the raw transcript) and run concurrently.
- **Persistence** — every stage is stored in Postgres and linked by foreign key, so
  past calls are queryable.

## Project layout

```
app/
  main.py            FastAPI app + lifespan (table creation) + /health
  config.py          Settings (OpenAI key, models, DB URL)
  db/                Async SQLAlchemy engine, session, ORM models
  schemas/           Pydantic: ExtractedCall, CRM/task/email, API envelopes
  services/          openai_client, extraction, transcription, generation/
  prompts/           Prompt templates per layer
  routers/           /transcribe, /extract, /generate, /calls
eval/                Labeled dataset, LLM judge, run_eval.py -> report
tests/               Unit + integration tests (LLM mocked, run offline)
```

## Setup

Prerequisites: Docker + Docker Compose (and an OpenAI API key for the LLM features).

1. Create your local env file and add a real key:

   ```bash
   cp .env.example .env
   # edit .env and set OPENAI_API_KEY=sk-...
   ```

2. Start the API and Postgres:

   ```bash
   docker compose up --build
   ```

3. Check it's alive:

   ```bash
   curl http://localhost:8000/health
   # {"status":"ok","openai_configured":true,"extraction_model":"gpt-4o","database_connected":true}
   ```

Interactive API docs are at `http://localhost:8000/docs`.

### Environment variables (`.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | Whisper + gpt-4o calls | _(required)_ |
| `OPENAI_EXTRACTION_MODEL` | Extraction/generation/judge model | `gpt-4o` |
| `OPENAI_TRANSCRIBE_MODEL` | Transcription model | `whisper-1` |
| `DATABASE_URL` | Async Postgres URL | `postgresql+asyncpg://postgres:postgres@db:5432/voice_agent` |

`.env` is git-ignored; `.env.example` (committed) holds placeholders only.

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/transcribe` | Audio upload → transcript text (stored) |
| `POST` | `/extract` | Transcript (or `transcript_id`) → `ExtractedCall` (stored) |
| `POST` | `/generate` | `extraction_id` or inline structure → CRM + tasks + email |
| `GET` | `/calls/{transcript_id}` | Stored transcript + latest extraction + outputs |
| `GET` | `/health` | Liveness + DB/config check |

Typical flow with `curl`:

```bash
# 1. Extract structure from a transcript
curl -s -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Priya: We want to decide by end of quarter. Marcus: I will send a proposal by Wednesday."}'
# -> {"extraction_id": 1, "transcript_id": 1, "extracted_call": { ... }}

# 2. Generate the three deliverables from that extraction
curl -s -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"extraction_id": 1}'

# 3. Retrieve everything stored for that call
curl -s http://localhost:8000/calls/1

# (optional) transcribe audio first
curl -s -X POST http://localhost:8000/transcribe -F "file=@call.mp3"
```

## Example

**Input transcript:**

```
Priya (Northwind Analytics): We're evaluating platforms to replace our reporting stack.
Marcus (DataForge): What's your timeline and budget?
Priya: Decision by end of quarter, budget around 60k a year, about 40 users.
Marcus: I'll send a tailored proposal by Wednesday, with two customer references.
Priya: Great. I'll loop in our head of data Aisha for the technical deep-dive next week.
```

**Extracted structure (`/extract`):**

```json
{
  "participants": [
    {"name": "Priya", "role": "buyer", "organization": "Northwind Analytics", "is_primary_contact": true},
    {"name": "Marcus", "role": "vendor", "organization": "DataForge", "is_primary_contact": false}
  ],
  "summary": "Northwind is evaluating platforms to replace their reporting stack. Marcus will send a proposal; a technical deep-dive is planned.",
  "key_points": ["~40 users", "~60k/year budget", "Decision by end of quarter"],
  "decisions": [
    {"description": "Decision to be made by end of quarter", "source_quote": "Decision by end of quarter"}
  ],
  "action_items": [
    {"description": "Send a tailored proposal with two customer references", "owner": "Marcus", "due_date_raw": "Wednesday", "due_date_iso": null, "source_quote": "I'll send a tailored proposal by Wednesday"},
    {"description": "Loop in head of data Aisha for the technical deep-dive", "owner": "Priya", "due_date_raw": "next week", "due_date_iso": null, "source_quote": "loop in our head of data Aisha ... next week"}
  ],
  "sentiment": "positive",
  "outcome": "Proposal to follow; deep-dive scheduled",
  "primary_contact_name": "Priya"
}
```

**Generated deliverables (`/generate`):**

```json
{
  "crm": {
    "contact": {"name": "Priya", "organization": "Northwind Analytics", "role": "buyer", "email": null},
    "deal_stage": "qualification",
    "sentiment": "positive",
    "notes": "Evaluating a replacement for their reporting stack. ~40 users, ~60k/year budget, decision by end of quarter.",
    "next_step": "Send the tailored proposal by Wednesday",
    "open_action_count": 2
  },
  "tasks": [
    {"owner": "Marcus", "description": "Send tailored proposal with two customer references", "due_date": null, "priority": "high"},
    {"owner": "Priya", "description": "Loop in Aisha for the technical deep-dive", "due_date": null, "priority": "medium"}
  ],
  "email": {
    "to": "Priya",
    "subject": "Following up on our call — proposal to follow",
    "body": "Hi Priya,\n\nThanks for the time today. To recap, you're evaluating a replacement for your reporting stack (~40 users, targeting a decision by end of quarter). Next steps:\n\n- I'll send a tailored proposal by Wednesday, including two customer references.\n- You'll loop in Aisha for a technical deep-dive next week.\n\nBest,\n[Your name]"
  }
}
```

## Testing

Unit + integration tests mock the LLM boundary, so they run offline and free:

```bash
pip install -r requirements.txt
pytest
```

Covers structured-output schema validation, malformed-output handling, the
extraction service, the full transcript → CRM + tasks + email pipeline, and the
eval scoring math.

## Evaluation

The eval measures how well extraction captures reality on a small labeled dataset
(`eval/dataset/`, ~5 synthetic transcripts with hand-labeled action items and
decisions). An **LLM judge** semantically matches predicted items to ground truth:

- **Recall** — share of ground-truth items that were captured.
- **Precision** — share of predicted items that match a real item; `1 - precision`
  approximates the hallucination rate.

Run it (needs a real `OPENAI_API_KEY`; makes API calls):

```bash
python -m eval.run_eval
```

Outputs `eval/report.md` and `eval/report.json` with per-category and per-transcript
precision/recall, a list of hallucinations/misses, and full before/after examples.

## Tech stack

Python · FastAPI · Pydantic · async SQLAlchemy + PostgreSQL · OpenAI
(Whisper + gpt-4o structured outputs) · Docker Compose · pytest.

## License

MIT
