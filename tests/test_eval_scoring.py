"""Offline tests for the eval scoring math (LLM judge stubbed)."""

from eval.run_eval import score_category


def make_matcher(mapping: dict[str, int]):
    """Build an async matcher that returns a fixed index per predicted string."""

    async def matcher(pred: str, candidates: list[str]) -> int:
        return mapping.get(pred, -1)

    return matcher


async def test_perfect_match():
    gt = ["send proposal", "book demo"]
    predicted = ["send proposal", "book demo"]
    matcher = make_matcher({"send proposal": 0, "book demo": 1})
    score = await score_category(predicted, gt, matcher)
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["false_positives"] == []
    assert score["missed"] == []


async def test_hallucination_lowers_precision():
    gt = ["send proposal"]
    predicted = ["send proposal", "buy the customer a car"]  # 2nd is invented
    matcher = make_matcher({"send proposal": 0})  # invented -> -1
    score = await score_category(predicted, gt, matcher)
    assert score["precision"] == 0.5
    assert score["recall"] == 1.0
    assert score["false_positives"] == ["buy the customer a car"]


async def test_miss_lowers_recall():
    gt = ["send proposal", "book demo"]
    predicted = ["send proposal"]  # missed "book demo"
    matcher = make_matcher({"send proposal": 0})
    score = await score_category(predicted, gt, matcher)
    assert score["precision"] == 1.0
    assert score["recall"] == 0.5
    assert score["missed"] == ["book demo"]


async def test_empty_predictions_with_gt_is_zero_recall():
    score = await score_category([], ["x"], make_matcher({}))
    assert score["recall"] == 0.0
    assert score["precision"] == 1.0  # no false positives when nothing predicted
