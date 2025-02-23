from waddle.processing.combine import adjust_pos_to_timeline, merge_timelines


def test_adjust_pos_to_timeline_starting_from_zero():
    """Test adjust_pos_to_timeline where segments start from 0."""
    segments = [(0, 200), (300, 500)]
    assert adjust_pos_to_timeline(segments, 0) == 0, "Boundary adjustment at 0 failed."
    assert adjust_pos_to_timeline(segments, 100) == 100, "Boundary adjustment at 100 failed."
    assert adjust_pos_to_timeline(segments, 199) == 199, "Boundary adjustment at 199 failed."
    assert adjust_pos_to_timeline(segments, 200) == 200, "Boundary adjustment at 200 failed."
    assert adjust_pos_to_timeline(segments, 250) == 200, "Boundary adjustment at 250 failed."
    assert adjust_pos_to_timeline(segments, 300) == 200, "Boundary adjustment at 300 failed."
    assert adjust_pos_to_timeline(segments, 350) == 250, "Boundary adjustment at 350 failed."
    assert adjust_pos_to_timeline(segments, 500) == 400, "Boundary adjustment at 500 failed."


def test_adjust_pos_to_timeline_starting_from_nonzero():
    segments = [(100, 300), (400, 500)]
    assert adjust_pos_to_timeline(segments, 0) == 0, "Boundary adjustment at 0 failed."
    assert adjust_pos_to_timeline(segments, 99) == 0, "Boundary adjustment at 99 failed."
    assert adjust_pos_to_timeline(segments, 100) == 0, "Boundary adjustment at 100 failed."
    assert adjust_pos_to_timeline(segments, 299) == 199, "Boundary adjustment at 299 failed."
    assert adjust_pos_to_timeline(segments, 300) == 200, "Boundary adjustment at 300 failed."
    assert adjust_pos_to_timeline(segments, 350) == 200, "Boundary adjustment at 350 failed."
    assert adjust_pos_to_timeline(segments, 400) == 200, "Boundary adjustment at 400 failed."
    assert adjust_pos_to_timeline(segments, 450) == 250, "Boundary adjustment at 450 failed."
    assert adjust_pos_to_timeline(segments, 500) == 300, "Boundary adjustment at 500 failed."
    assert adjust_pos_to_timeline(segments, 501) == 300, "Boundary adjustment at 501 failed."


def test_adjust_pos_to_timeline_one_item():
    segments = [(0, 100)]
    assert adjust_pos_to_timeline(segments, 0) == 0, "Boundary adjustment at 0 failed."
    assert adjust_pos_to_timeline(segments, 50) == 50, "Boundary adjustment at 50 failed."
    assert adjust_pos_to_timeline(segments, 100) == 100, "Boundary adjustment at 100 failed."
    assert adjust_pos_to_timeline(segments, 101) == 100, "Boundary adjustment at 101 failed."


def test_merge_timelines_separated_segments():
    """Test merging timelines where segments are completely separate."""
    segments = [
        [(0, 100)],
        [(200, 300)],
    ]
    expected = [(0, 100), (200, 300)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_continuous_segments():
    """Test merging timelines where segments are directly connected."""
    segments = [
        [(0, 100)],
        [(100, 200)],
        [(200, 300)],
    ]
    expected = [(0, 300)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_non_overlapping_segments():
    """Test merging timelines with non-overlapping segments."""
    segments = [
        [(0, 100)],
        [(200, 300)],
        [(400, 500)],
    ]
    expected = [(0, 100), (200, 300), (400, 500)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_overlapping_segments():
    """Test merging timelines where segments overlap."""
    segments = [
        [(200, 400)],
        [(0, 300)],
    ]
    expected = [(0, 400)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"
