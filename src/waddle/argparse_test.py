import pytest

from waddle.argparse import create_waddle_parser


def test_ss_0():
    parser = create_waddle_parser()
    args = parser.parse_args(["single", "audio", "-ss", "00:00:10,050"])
    assert args.ss == 10.05


def test_ss_1():
    parser = create_waddle_parser()
    args = parser.parse_args(["single", "audio", "-ss", "30.5"])
    assert args.ss == 30.5


def test_ss_2():
    parser = create_waddle_parser()
    args = parser.parse_args(["single", "audio", "-ss", "99:59:59,999"])
    assert args.ss == 359999.999


def test_ss_3():
    parser = create_waddle_parser()
    args = parser.parse_args(["single", "audio", "-ss", "0"])
    assert args.ss == 0.0


def test_ss_4():
    parser = create_waddle_parser()
    args = parser.parse_args(["single", "audio", "-ss", "0.0"])
    assert args.ss == 0.0


def test_ss_5():
    parser = create_waddle_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["single", "audio", "-ss", "00:00:00:00"])


def test_ss_6():
    parser = create_waddle_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["single", "audio", "-ss", "00:00:00.123.53"])
