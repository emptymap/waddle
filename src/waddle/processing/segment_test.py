from waddle.processing.segment import SegmentsProcessor


def test_merge_raw_timeline_01():
    segments = [(0, 100), (200, 300)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 100), (200, 300)]


def test_merge_raw_timeline_02():
    segments = [(0, 100), (100, 200), (200, 300)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 300)]


def test_merge_raw_timeline_03():
    segments = [(0, 300), (200, 400), (500, 600)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 400), (500, 600)]


def test_merge_raw_timeline_04():
    segments = []
    assert SegmentsProcessor._merge_raw_timeline(segments) == []
