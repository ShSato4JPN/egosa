"""Google News RSS から企業名でニュースを取得する情報源。

APIキー不要・公式RSS。スクレイピングではなく公開RSSエンドポイントを利用する。
"""

from __future__ import annotations

import urllib.parse
import urllib.request

import feedparser

from .base import Article

# 日本語・日本リージョンのGoogle Newsを指定。
_RSS_ENDPOINT = "https://news.google.com/rss/search"
_HL = "ja"
_GL = "JP"
_CEID = "JP:ja"

_USER_AGENT = "egosa/0.1 (personal reputation checker; +https://github.com/ShSato4JPN/egosa)"
_TIMEOUT_SEC = 15


def _build_url(query: str) -> str:
    """検索クエリからRSS URLを組み立てる。"""
    params = {
        "q": query,
        "hl": _HL,
        "gl": _GL,
        "ceid": _CEID,
    }
    return f"{_RSS_ENDPOINT}?{urllib.parse.urlencode(params)}"


class GoogleNewsSource:
    """Google News RSS をソースとして扱うクラス。"""

    name = "google_news"

    def __init__(self, timeout: int = _TIMEOUT_SEC) -> None:
        self.timeout = timeout

    def fetch(self, query: str, limit: int = 50) -> list[Article]:
        """企業名でニュースを取得し Article のリストを返す。

        ネットワークエラー時は例外を送出する（呼び出し側でハンドリングする）。
        """
        url = _build_url(query)
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (httpsのみ)
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
