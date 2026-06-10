"""情報源の共通インターフェース。

後続PRで Reddit / Bluesky などを追加する際も、この Source プロトコルに
合わせて実装すれば analyzer / cli からは同一に扱える。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Article:
    """1件の記事／投稿。"""

    title: str
    summary: str = ""
    link: str = ""
    published: str = ""
    source: str = ""

    @property
    def text(self) -> str:
        """ネガワード判定に使う結合テキスト（タイトル＋要約）。"""
        return f"{self.title} {self.summary}".strip()


class Source(Protocol):
    """情報源プロトコル。"""

    name: str

    def fetch(self, query: str, limit: int = 50) -> list[Article]:
        """クエリ（通常は企業名）で記事を取得する。"""
        ...
