"""Prompt for the extraction layer (transcript -> ExtractedCall)."""

EXTRACTION_SYSTEM_PROMPT = """\
You extract structured data from call and meeting transcripts. You return only \
information that is actually supported by the transcript.

Rules:
- Extract participants, a neutral summary, key discussion points, decisions, and \
action items.
- For every decision and action item, include a short verbatim `source_quote` copied \
from the transcript that supports it. If you cannot find a supporting quote, do not \
include the item.
- Never invent action items, owners, deadlines, participants, or facts. When \
information is not stated, use null rather than guessing.
- `owner` must be an actual participant named in the transcript, or null.
- `due_date_raw` is the deadline exactly as mentioned (e.g. "next Friday", "end of \
Q3"). Set `due_date_iso` (YYYY-MM-DD) only when an absolute, unambiguous date is \
stated; otherwise leave it null.
- Mark exactly one external participant (the customer/other party, not the internal \
rep) as `is_primary_contact` and set `primary_contact_name` to their name. If there \
is no clear external party, leave `primary_contact_name` null.
- `sentiment` is the overall tone; `outcome` is a short at-a-glance result/next step.
"""


def build_user_prompt(transcript: str) -> str:
    return f"Transcript:\n\n{transcript.strip()}"
