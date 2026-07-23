# Voice-to-Structured-Data Agent

🚧 Work in progress.

A pipeline that turns call/meeting transcripts into structured, actionable output: a CRM entry, a task list, and a follow-up email draft.

## Idea

Sales and support calls generate information that usually stays trapped in a transcript. This agent extracts the structure (participants, decisions, action items) from a transcript and generates three concrete deliverables from it: a CRM-ready entry, a task list with owners, and a follow-up email draft.

## Planned Architecture

- **Ingestion** — accepts raw audio (transcribed via Whisper) or plain text transcripts
- **Extraction layer** — LLM-based structured extraction: entities, decisions, action items
- **Generation layer** — CRM entry, task list, and follow-up email, all generated from the same extracted structure (not re-reading the raw transcript per output)
- **Postgres** — stores transcripts, extracted data, and generated outputs
- **FastAPI** — `/transcribe`, `/extract`, `/generate` endpoints

## Tech Stack

- Python, FastAPI
- PostgreSQL
- Docker / docker-compose
- OpenAI (transcription + extraction/generation)

## Status

Currently building out the extraction layer. Setup instructions, example input/output, and eval results will be added as the project progresses.

## License

MIT