"""複数の情報源を横断して取得・分析するアグリゲーション層。

スコアは「ソース別加算」: 各ソースの炎上記事数を合計して総スコアとする。
ソース別の内訳（per_source）も保持し、レポートやCLIで内訳を表示できる。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .analyzer import FlameResult, analyze
from .sources.base import Source


@dataclass
class MultiResult:
    """複数ソースを横断した分析結果。"""

    total: FlameResult                                       # 全ソース結合の集計
    per_source: dict[str, FlameResult] = field(default_factory=dict)  # ソース別の集計
    errors: dict[str, str] = field(default_factory=dict)     # 取得に失敗したソース

    @property
    def score(self) -> int:
        """総炎上スコア = 各ソースの炎上記事数の合計（=結合集計の炎上記事数）。"""
        return self.total.score

    @property
    def source_scores(self) -> dict[str, int]:
        """ソース別の炎上スコア（炎上記事数）。"""
        return {name: r.score for name, r in self.per_source.items()}

    @property
    def source_articles(self) -> dict[str, int]:
        """ソース別の取得記事数。"""
        return {name: r.total_articles for name, r in self.per_source.items()}

    @property
    def all_failed(self) -> bool:
        """全ソースが失敗し、1件も取得できなかったか。"""
        return self.total.total_articles == 0 and bool(self.errors)


def fetch_and_analyze(
    name: str,
    sources: list[Source],
    *,
    limit: int = 50,
    keywords: list[str] | None = None,
) -> MultiResult:
    """各ソースから取得・分析し、結合結果とソース別内訳を返す。

    1つのソースが例外を投げても他のソースは継続し、errors に記録する。
    """
    per_source: dict[str, FlameResult] = {}
    errors: dict[str, str] = {}
    all_articles = []
    combined_keywords: Counter[str] = Counter()

    for source in sources:
        try:
            articles = source.fetch(name, limit=limit)
        except Exception as e:  # noqa: BLE001 — 1ソースの失敗で全体を止めない
            errors[source.name] = f"{type(e).__name__}: {e}"
            continue
        result = analyze(articles, keywords)
        per_source[source.name] = result
        all_articles.extend(articles)
        combined_keywords.update(result.keyword_counts)

    total = analyze(all_articles, keywords)
    return MultiResult(total=total, per_source=per_source, errors=errors)
