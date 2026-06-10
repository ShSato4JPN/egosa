from egosa.keywords import NEGATIVE_KEYWORDS, count_hits


def test_count_hits_basic():
    text = "A社が不祥事で炎上、株価は急落した"
    hits = count_hits(text)
    assert hits.get("不祥事") == 1
    assert hits.get("炎上") == 1
    assert hits.get("急落") == 1


def test_count_hits_multiple_occurrences():
    text = "炎上 炎上 また炎上"
    assert count_hits(text)["炎上"] == 3


def test_count_hits_no_negative():
    text = "新製品が好評で売上が過去最高を更新"
    assert count_hits(text) == {}


def test_count_hits_empty():
    assert count_hits("") == {}


def test_keyword_list_nonempty_and_unique():
    assert NEGATIVE_KEYWORDS
    assert len(NEGATIVE_KEYWORDS) == len(set(NEGATIVE_KEYWORDS))
