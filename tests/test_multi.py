from egosa.multi import fetch_and_analyze
from egosa.sources.base import Article


class FakeSource:
    def __init__(self, name, articles=None, fail=False):
        self.name = name
        self._articles = articles or []
        self._fail = fail

    def fetch(self, query, limit=50):
        if self._fail:
            raise RuntimeError("down")
        return self._articles


def test_score_is_sum_of_sources():
    s1 = FakeSource("a", [Article(title="炎上", source="a"), Article(title="平穏", source="a")])
    s2 = FakeSource("b", [Article(title="減益で赤字", source="b")])
    multi = fetch_and_analyze("X", [s1, s2])
    # ソース別: a=1, b=1 → 合計2
    assert multi.source_scores == {"a": 1, "b": 1}
    assert multi.score == 2
    assert multi.total.total_articles == 3


def test_one_source_failure_is_recorded_others_continue():
    s1 = FakeSource("a", [Article(title="炎上", source="a")])
    s2 = FakeSource("b", fail=True)
    multi = fetch_and_analyze("X", [s1, s2])
    assert multi.score == 1
    assert "b" in multi.errors
    assert not multi.all_failed


def test_all_sources_fail():
    s1 = FakeSource("a", fail=True)
    s2 = FakeSource("b", fail=True)
    multi = fetch_and_analyze("X", [s1, s2])
    assert multi.all_failed
    assert set(multi.errors) == {"a", "b"}
