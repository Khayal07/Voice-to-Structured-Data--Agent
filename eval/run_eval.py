"""Run the extraction eval over the labeled dataset and write a report.

For each transcript we run the real extraction service, then use the LLM judge to
match predicted action items / decisions against the hand-labeled ground truth.
From the match results we compute recall (coverage of true items) and precision
(1 - precision approximates the hallucination rate).

Usage:
    python -m eval.run_eval            # full run, writes report.md + report.json
    python -m eval.run_eval --examples 2

Requires a real OPENAI_API_KEY in the environment / .env.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.schemas.extraction import ExtractedCall
from app.services.extraction import extract_call
from app.services.generation.pipeline import generate_all
from eval.judge import judge_match

DATASET_DIR = Path(__file__).parent / "dataset"
REPORT_MD = Path(__file__).parent / "report.md"
REPORT_JSON = Path(__file__).parent / "report.json"

Matcher = Callable[[str, list[str]], Awaitable[int]]


async def score_category(
    predicted: list[str], gt: list[str], matcher: Matcher
) -> dict[str, Any]:
    """Score one category (action_items or decisions) for one transcript.

    Pure aside from `matcher`, which is injected so this is unit-testable offline.
    """
    matched_gt: set[int] = set()
    true_positives = 0
    false_positives: list[str] = []

    for item in predicted:
        idx = await matcher(item, gt)
        if idx >= 0:
            true_positives += 1
            matched_gt.add(idx)
        else:
            false_positives.append(item)

    precision = true_positives / len(predicted) if predicted else 1.0
    recall = len(matched_gt) / len(gt) if gt else 1.0
    missed = [gt[i] for i in range(len(gt)) if i not in matched_gt]

    return {
        "predicted_count": len(predicted),
        "gt_count": len(gt),
        "true_positives": true_positives,
        "matched_gt": len(matched_gt),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "false_positives": false_positives,
        "missed": missed,
    }


def _micro(rows: list[dict[str, Any]], key_tp: str, key_den: str) -> float:
    tp = sum(r[key_tp] for r in rows)
    den = sum(r[key_den] for r in rows)
    return round(tp / den, 3) if den else 1.0


def load_dataset() -> list[tuple[str, str, dict]]:
    """Return (name, transcript_text, ground_truth) tuples sorted by filename."""
    pairs = []
    for txt in sorted(DATASET_DIR.glob("*.txt")):
        gt = json.loads(txt.with_suffix(".json").read_text(encoding="utf-8"))
        pairs.append((txt.stem, txt.read_text(encoding="utf-8"), gt))
    return pairs


async def evaluate(examples: int) -> dict[str, Any]:
    dataset = load_dataset()
    per_transcript: list[dict[str, Any]] = []
    ai_rows: list[dict[str, Any]] = []
    dec_rows: list[dict[str, Any]] = []
    pooled_rows: list[dict[str, Any]] = []
    example_blocks: list[dict[str, Any]] = []

    for i, (name, transcript, gt) in enumerate(dataset):
        extracted: ExtractedCall = await extract_call(transcript)

        pred_actions = [a.description for a in extracted.action_items]
        gt_actions = [a["description"] for a in gt.get("action_items", [])]
        pred_decisions = [d.description for d in extracted.decisions]
        gt_decisions = [d["description"] for d in gt.get("decisions", [])]

        ai_score = await score_category(pred_actions, gt_actions, judge_match)
        dec_score = await score_category(pred_decisions, gt_decisions, judge_match)

        # Category-agnostic ("pooled") score: the decision vs action-item boundary is
        # fuzzy, so we also match every predicted item against every ground-truth item
        # regardless of category. This measures "was this fact captured at all" and is
        # the headline metric; the per-category numbers are kept as diagnostics.
        pooled_score = await score_category(
            pred_actions + pred_decisions, gt_actions + gt_decisions, judge_match
        )

        ai_rows.append(ai_score)
        dec_rows.append(dec_score)
        pooled_rows.append(pooled_score)

        per_transcript.append(
            {
                "name": name,
                "scenario": gt.get("scenario", ""),
                "items": pooled_score,
                "action_items": ai_score,
                "decisions": dec_score,
            }
        )

        if i < examples:
            outputs = await generate_all(extracted)
            example_blocks.append(
                {
                    "name": name,
                    "transcript": transcript,
                    "extracted": extracted.model_dump(mode="json"),
                    "outputs": outputs.model_dump(mode="json"),
                }
            )

    summary = {
        "items": {
            "precision": _micro(pooled_rows, "true_positives", "predicted_count"),
            "recall": _micro(pooled_rows, "matched_gt", "gt_count"),
        },
        "action_items": {
            "precision": _micro(ai_rows, "true_positives", "predicted_count"),
            "recall": _micro(ai_rows, "matched_gt", "gt_count"),
        },
        "decisions": {
            "precision": _micro(dec_rows, "true_positives", "predicted_count"),
            "recall": _micro(dec_rows, "matched_gt", "gt_count"),
        },
    }

    return {
        "summary": summary,
        "per_transcript": per_transcript,
        "examples": example_blocks,
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Extraction Evaluation Report",
        "",
        "Precision = share of predicted items that match a real ground-truth item "
        "(so `1 - precision` ≈ hallucination rate). "
        "Recall = share of ground-truth items that were captured. "
        "Matching is decided by an LLM judge.",
        "",
        "The headline metric is **Items (pooled)**: because the decision vs "
        "action-item boundary is fuzzy, every predicted item is matched against every "
        "ground-truth item regardless of category. The per-category rows below are "
        "kept as diagnostics.",
        "",
        "## Summary (micro-averaged)",
        "",
        "| Metric | Precision | Recall |",
        "| --- | --- | --- |",
        f"| **Items (pooled)** | **{_pct(s['items']['precision'])}** "
        f"| **{_pct(s['items']['recall'])}** |",
        f"| Action items only | {_pct(s['action_items']['precision'])} "
        f"| {_pct(s['action_items']['recall'])} |",
        f"| Decisions only | {_pct(s['decisions']['precision'])} "
        f"| {_pct(s['decisions']['recall'])} |",
        "",
        "## Per-transcript breakdown (pooled items)",
        "",
        "| Transcript | Scenario | Precision | Recall |",
        "| --- | --- | --- | --- |",
    ]
    for t in report["per_transcript"]:
        it = t["items"]
        lines.append(
            f"| {t['name']} | {t['scenario']} | {_pct(it['precision'])} | "
            f"{_pct(it['recall'])} |"
        )

    # Hallucinations / misses detail (category-agnostic)
    lines += ["", "### Hallucinations & misses", ""]
    for t in report["per_transcript"]:
        fps = t["items"]["false_positives"]
        miss = t["items"]["missed"]
        lines.append(
            f"- **{t['name']}** — hallucinated: {fps or 'none'}; missed: {miss or 'none'}"
        )

    # Examples
    if report["examples"]:
        lines += ["", "## Example before / after", ""]
        for ex in report["examples"]:
            outputs = ex["outputs"]
            lines += [
                f"### {ex['name']}",
                "",
                "**Transcript (input):**",
                "",
                "```",
                ex["transcript"].strip(),
                "```",
                "",
                "**Extracted structure:**",
                "",
                "```json",
                json.dumps(ex["extracted"], indent=2),
                "```",
                "",
                "**Generated CRM entry:**",
                "",
                "```json",
                json.dumps(outputs["crm"], indent=2),
                "```",
                "",
                "**Generated tasks:**",
                "",
                "```json",
                json.dumps(outputs["tasks"], indent=2),
                "```",
                "",
                "**Generated follow-up email:**",
                "",
                "```",
                f"To: {outputs['email']['to']}",
                f"Subject: {outputs['email']['subject']}",
                "",
                outputs["email"]["body"],
                "```",
                "",
            ]
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the extraction eval.")
    parser.add_argument(
        "--examples",
        type=int,
        default=2,
        help="Number of transcripts to include as full before/after examples.",
    )
    args = parser.parse_args()

    key = get_settings().openai_api_key
    if not key or key.startswith("sk-your-key"):
        raise SystemExit(
            "OPENAI_API_KEY is not set to a real key. Set it in your environment "
            "or .env before running the eval."
        )

    report = await evaluate(args.examples)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")

    s = report["summary"]["items"]
    print(f"Wrote {REPORT_MD} and {REPORT_JSON}")
    print(f"Pooled items precision {_pct(s['precision'])}, recall {_pct(s['recall'])}")


if __name__ == "__main__":
    asyncio.run(main())
