from textwrap import dedent

from waddle.metadata import (
    ChapterMarker,
    ShowNotesEntry,
    SRTEntry,
    extract_metadata,
    parse_annotated_srt,
)


def test_parse_annotated_srt_01():
    annotated_srt = (
        dedent("""\
        1
        00:00:00.490 --> 00:00:02.430
        shun: ラバーダックFMへようこそ

        2
        00:00:02.430 --> 00:00:05.970
        shun: このポッドキャストは大学で出会った3人のホストが

        3
        00:00:05.970 --> 00:00:08.650
        shun: 自分たちの興味のあるコンピューターサイエンスや

        4
        00:00:08.650 --> 00:00:10.410
        shun: プログラミングのトピックについて

        5
        00:00:10.410 --> 00:00:13.190
        shun: 自由気ままに語り合うポッドキャストです\n\n""")
    )  # NOTE: SRT-entry must end with two newlines
    result = parse_annotated_srt(annotated_srt)
    assert len(result) == 5
    assert all(isinstance(item, SRTEntry) for item in result)


def test_parse_annotated_srt_02():
    annotated_srt = dedent("""\
        # イントロ
        1
        00:00:00.490 --> 00:00:02.430
        shun: ラバーダックFMへようこそ

        2
        00:00:02.430 --> 00:00:05.970
        shun: このポッドキャストは大学で出会った3人のホストが

        3
        00:00:05.970 --> 00:00:08.650
        shun: 自分たちの興味のあるコンピューターサイエンスや

        4
        00:00:08.650 --> 00:00:10.410
        shun: プログラミングのトピックについて

        5
        00:00:10.410 --> 00:00:13.190
        shun: 自由気ままに語り合うポッドキャストです\n\n""")
    result = parse_annotated_srt(annotated_srt)
    assert len(result) == 6
    assert isinstance(result[0], ChapterMarker)
    assert result[0].title == "イントロ"
    assert result[0].level == 1


def test_parse_annotated_srt_03():
    annotated_srt = dedent("""\
    14
    00:00:36.070 --> 00:00:38.810
    shun: じゃあ甲太郎くんからお願いします

    ## Kotaro: さくらインターネット

    15
    00:00:39.750 --> 00:00:53.870
    kotaro: はいそうですね最近見てたのだと桜インターネットに人がいっぱい座れてますねってことが会社内でも話題になってました

    - [ガバメントクラウドの高すぎるハードル、国産勢唯一さくらインターネットの挑戦 | 日経クロステック（xTECH）](https://xtech.nikkei.com/atcl/nxt/column/18/03074/012300002/))
    """)  # noqa: E501
    result = parse_annotated_srt(annotated_srt)
    assert len(result) == 4
    assert isinstance(result[1], ChapterMarker)
    assert result[1].title == "Kotaro: さくらインターネット"
    assert result[1].level == 2
    assert isinstance(result[3], ShowNotesEntry)
    assert (
        result[3].text
        == "- [ガバメントクラウドの高すぎるハードル、国産勢唯一さくらインターネットの挑戦 | 日経クロステック（xTECH）](https://xtech.nikkei.com/atcl/nxt/column/18/03074/012300002/))"
    )


def test_extract_metadata_01():
    annotated_srt = dedent("""
        # イントロ

        1
        00:00:00.000 --> 00:00:02.000
        shun: ラバーダックFMへようこそ

        # ニュース/コンテンツ

        2
        00:00:02.000 --> 00:00:05.000
        shun: では、各々が最近興味を持ったニュースやコンテンツを紹介していきます

        ## Kotaro: さくらインターネット

        3
        00:00:05.000 --> 00:00:10.000
        kotaro: 桜インターネットに人が吸われてますね

        - [ガバメントクラウドの高すぎるハードル、国産勢唯一さくらインターネットの挑戦 | 日経クロステック（xTECH）](https://xtech.nikkei.com/atcl/nxt/column/18/03074/012300002/)

        ## Masa: LLM

        4
        00:00:10.000 --> 00:00:15.000
        masa: 最近AI関連、LLM関連で読んで面白かった論文がありました。

        - [[2307.03172] Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)
        - [[2406.16008] Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization](https://arxiv.org/abs/2406.16008)

        # アウトロ

        5
        00:00:15.000 --> 00:00:20.000
        shun: それでは、今回はこの辺で\n\n""")
    entries = parse_annotated_srt(annotated_srt)
    chapters, show_notes = extract_metadata(entries)
    assert len(chapters) == 5
    assert chapters[0].title == "イントロ"
    assert chapters[0].start == 0.0
    assert chapters[0].end == 2.0
    assert chapters[1].title == "ニュース/コンテンツ"
    assert chapters[2].title == "Kotaro: さくらインターネット"
    assert chapters[3].title == "Masa: LLM"
    assert chapters[4].title == "アウトロ"

    assert (
        show_notes.strip()
        == dedent("""
        - [ガバメントクラウドの高すぎるハードル、国産勢唯一さくらインターネットの挑戦 | 日経クロステック（xTECH）](https://xtech.nikkei.com/atcl/nxt/column/18/03074/012300002/)
        - [[2307.03172] Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)
        - [[2406.16008] Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization](https://arxiv.org/abs/2406.16008)\n
        """).strip()
    )


def test_extract_metadata_02():
    annotated_srt = dedent("""
        # Chapter with no srt entries
        ## ↑ gets ignored and this will be the first chapter

        1
        00:00:00.000 --> 00:00:02.000
        alice: Hello

        # This also will be ignored
    """)
    entries = parse_annotated_srt(annotated_srt)
    chapters, show_notes = extract_metadata(entries)
    assert len(chapters) == 1
    assert chapters[0].title.startswith("↑ gets ignored")
    assert show_notes == ""


def test_extract_metadata_03():
    annotated_srt = dedent("""
        1
        00:00:00.000 --> 00:00:02.000
        alice: Hello

        Can write Markdown here.

        - List 1
        - List 2
          - Sublist 1

        2
        00:00:02.000 --> 00:00:04.000
        bob: Hi

        - The list continues here

        ;
        > `;` can be used to insert newline
        > empty lines are ignored otherwise
        ;
        ; Can also write something here
        ;

        3
        00:00:04.000 --> 00:00:06.000
        alice: How are you?\n\n

        The last line will be included in the show notes.""")
    entries = parse_annotated_srt(annotated_srt)
    chapters, show_notes = extract_metadata(entries)
    assert len(chapters) == 0
    assert (
        show_notes.strip()
        == dedent("""
        Can write Markdown here.
        - List 1
        - List 2
          - Sublist 1
        - The list continues here

        > `;` can be used to insert newline
        > empty lines are ignored otherwise

        Can also write something here

        The last line will be included in the show notes.""").strip()
    )
