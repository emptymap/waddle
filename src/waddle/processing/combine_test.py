from waddle.processing.combine import merge_timelines, adjust_pos_to_timeline


def test_merge_timelines_01():
    # separated
    segments = [
        [(0, 100)],
        [(200, 300)],
    ]
    assert merge_timelines(segments) == [(0, 100), (200, 300)]


def test_merge_timelines_02():
    # connected
    segments = [
        [(0, 100)],
        [(100, 200)],
        [(200, 300)],
    ]
    assert merge_timelines(segments) == [(0, 300)]


def test_merge_timelines_03():
    segments = [
        [(0, 100)],
        [(200, 300)],
        [(400, 500)],
    ]
    assert merge_timelines(segments) == [(0, 100), (200, 300), (400, 500)]


def test_merge_timelines_04():
    # overlapping
    segments = [
        [(200, 400)],
        [(0, 300)],
    ]
    assert merge_timelines(segments) == [(0, 400)]


def adjust_pos_to_timeline_01():
    segments = [(0, 100), (200, 300)]
    assert adjust_pos_to_timeline(segments, 0) == 0
    assert adjust_pos_to_timeline(segments, 50) == 50
    assert adjust_pos_to_timeline(segments, 100) == 100
    assert adjust_pos_to_timeline(segments, 150) == 100
    assert adjust_pos_to_timeline(segments, 200) == 100
    assert adjust_pos_to_timeline(segments, 250) == 150
    assert adjust_pos_to_timeline(segments, 300) == 200
    assert adjust_pos_to_timeline(segments, 350) == 200
    assert adjust_pos_to_timeline(segments, 400) == 200


def adjust_pos_to_timeline_02():
    segments = [(100, 300), (400, 500)]
    assert adjust_pos_to_timeline(segments, 100) == 0
    assert adjust_pos_to_timeline(segments, 300) == 200
    assert adjust_pos_to_timeline(segments, 400) == 200
    assert adjust_pos_to_timeline(segments, 450) == 250
    assert adjust_pos_to_timeline(segments, 500) == 300
