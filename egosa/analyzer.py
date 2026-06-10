"""記事リストからネガティブワードを集計し、炎上スコアを算出する。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .keywords import count_hits
from .sources.base import Article


@dataclass
class FlameResult:
    """炎上分析の結果。"""

    total_articles: int                                  # 取得した記事総数
    flagged_articles: int                                # ネガワードを含む記事数
    keyword_counts: dict[str, int] = field(default_factory=dict)  # ワード別の合計出現数
    flagged: list[tuple[Article, dict[str, int]]] = field(default_factory=list)  # ヒット記事とそのワード

    @property
    def score(self) -> int:
        """炎上スコア = ネガワードを含む記事数。"""
        return self.flagged_articles

    @property
    def ratio(self) -> float:
        """炎上記事の比率（0.0〜1.0）。記事0件なら0.0。"""
        if self.total_articles == 0:
            return 0.0
        return self.flagged_articles / self.total_articles


def analyze(articles: list[Article], keywords: list[str] | None = None) -> FlameResult:
    """記事リストを分析して FlameResult を返す。

    Args:
        articles: 分析対象の記事。
        keywords: ネガティブワード辞書（未指定なら既定）。

    Returns:
        FlameResult。
    """
    total_counts: Counter[str] = Counter()
    flagged: list[tuple[Article, dict[str, int]]] = []

    for article in articles:
        hits = count_hits(article.text, keywords)
        if hits:
            flagged.append((article, hits))
            total_counts.update(hits)

    return FlameResult(
        total_articles=len(articles),
        flagged_articles=len(flagged),
        keyword_counts=dict(total_counts.most_common()),
        flagged=flagged,
    )
