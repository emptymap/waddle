from waddle.processing.segment import merge_segments


def test_merge_segments_01():
    segments = [(0, 100), (200, 300)]
    assert merge_segments(segments) == [(0, 100), (200, 300)]


def test_merge_segments_02():
    segments = [(0, 100), (100, 200), (200, 300)]
    assert merge_segments(segments) == [(0, 300)]


def test_merge_segments_03():
    segments = [(0, 300), (200, 400), (500, 600)]
    assert merge_segments(segments) == [(0, 400), (500, 600)]


def test_merge_segments_04():
    segments = []
    assert merge_segments(segments) == []
