"""Pipeline ordering, concurrency, and verdict resolution."""

from conftest import FakeDetector

from agentcitadel.guard.pipeline import GuardPipeline, resolve
from agentcitadel.types import GuardResult, Verdict


async def test_results_follow_detector_order() -> None:
    pipeline = GuardPipeline([FakeDetector(name="a"), FakeDetector(name="b")])
    results = await pipeline.run("hello")

    assert [r.detector for r in results] == ["a", "b"]


async def test_every_detector_sees_content() -> None:
    a, b = FakeDetector(name="a"), FakeDetector(name="b", verdict=Verdict.BLOCK)
    await GuardPipeline([a, b]).run("payload")

    assert a.seen == ["payload"]
    assert b.seen == ["payload"]


async def test_empty_pipeline_allows() -> None:
    assert await GuardPipeline([]).run("anything") == []
    assert resolve([]) is Verdict.ALLOW


def _result(verdict: Verdict) -> GuardResult:
    return GuardResult(verdict=verdict, detector="x", reason="test")


def test_block_beats_flag_and_allow() -> None:
    assert resolve([_result(Verdict.ALLOW), _result(Verdict.BLOCK)]) is Verdict.BLOCK
    assert resolve([_result(Verdict.BLOCK), _result(Verdict.ALLOW)]) is Verdict.BLOCK


def test_flag_beats_allow() -> None:
    assert resolve([_result(Verdict.ALLOW), _result(Verdict.FLAG)]) is Verdict.FLAG
