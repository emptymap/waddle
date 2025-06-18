from typing import List, Tuple

from waddle.processing.segment import merge_segments


def test_merge_segments_01() -> None:
    segments: List[Tuple[int, int]] = [(0, 100), (200, 300)]
    assert merge_segments(segments) == [(0, 100), (200, 300)]


def test_merge_segments_02() -> None:
    segments: List[Tuple[int, int]] = [(0, 100), (100, 200), (200, 300)]
    assert merge_segments(segments) == [(0, 300)]


def test_merge_segments_03() -> None:
    segments: List[Tuple[int, int]] = [(0, 300), (200, 400), (500, 600)]
    assert merge_segments(segments) == [(0, 400), (500, 600)]


def test_merge_segments_04() -> None:
    segments: List[Tuple[int, int]] = []
    assert merge_segments(segments) == []
