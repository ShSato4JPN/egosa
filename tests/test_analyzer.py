from egosa.analyzer import analyze
from egosa.sources.base import Article


def _articles():
    return [
        Article(title="A社、不祥事で炎上", summary="謝罪会見を開いた"),
        Article(title="A社、業績好調で増益", summary="売上が過去最高"),
        Article(title="A社製品にリコール", summary="欠陥が見つかった"),
    ]


def test_analyze_counts_flagged_articles():
    result = analyze(_articles())
    assert result.total_articles == 3
    # 炎上記事は1番目と3番目の2件。
    assert result.flagged_articles == 2
    assert result.score == 2


def test_analyze_keyword_counts():
    result = analyze(_articles())
    assert result.keyword_counts.get("不祥事") == 1
    assert result.keyword_counts.get("炎上") == 1
    assert result.keyword_counts.get("謝罪") == 1
    assert result.keyword_counts.get("リコール") == 1
    assert result.keyword_counts.get("欠陥") == 1


def test_analyze_ratio():
    result = analyze(_articles())
    assert abs(result.ratio - 2 / 3) < 1e-9


def test_analyze_empty():
    result = analyze([])
    assert result.total_articles == 0
    assert result.score == 0
    assert result.ratio == 0.0
