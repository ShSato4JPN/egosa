"""はてなブックマークの検索RSSから企業名で記事を取得する情報源。

認証不要の公開RSS。ネット上の「ネタ」「炎上」記事の検知と相性が良い。
エンドポイント: https://b.hatena.ne.jp/q/<query>?mode=rss
"""

from __future__ import annotations

import urllib.parse
import urllib.request

import feedparser

from .base import Article

_RSS_BASE = "https://b.hatena.ne.jp/q/"
_USER_AGENT = "egosa/0.1 (personal reputation checker; +https://github.com/ShSato4JPN/egosa)"
_TIMEOUT_SEC = 15


def _build_url(query: str, min_users: int) -> str:
    """検索クエリからはてブ検索RSSのURLを組み立てる。

    Args:
        query: 検索語（企業名）。
        min_users: 最低ブックマーク数（少ないほど広く拾う）。
    """
    quoted = urllib.parse.quote(query, safe="")
    params = {
        "mode": "rss",
        "sort": "recent",  # 新着順
        "users": str(min_users),
        "safe": "on",
    }
    return f"{_RSS_BASE}{quoted}?{urllib.parse.urlencode(params)}"


class HatenaBookmarkSource:
    """はてなブックマーク検索RSSをソースとして扱うクラス。"""

    name = "hatena"

    def __init__(self, timeout: int = _TIMEOUT_SEC, min_users: int = 1) -> None:
        self.timeout = timeout
        self.min_users = min_users

    def fetch(self, query: str, limit: int = 50) -> list[Article]:
        """企業名ではてブ記事を取得し Article のリストを返す。

        ネットワークエラー時は例外を送出する（呼び出し側でハンドリングする）。
        """
        url = _build_url(query, self.min_users)
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            raw = resp.read()

        feed = feedparser.parse(raw)
        articles: list[Article] = []
        for entry in feed.entries[:limit]:
            articles.append(
                Article(
                    title=getattr(entry, "title", "") or "",
                    summary=getattr(entry, "summary", "") or "",
                    link=getattr(entry, "link", "") or "",
                    published=getattr(entry, "published", "") or "",
                    source=self.name,
                )
            )
        return articles
