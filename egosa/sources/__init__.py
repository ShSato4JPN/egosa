"""評判の情報源（ソース）。差し替え可能なインターフェースで提供する。"""

from __future__ import annotations

from ..config import get_bluesky_credentials
from .base import Source
from .bluesky import BlueskySource
from .google_news import GoogleNewsSource
from .hatena import HatenaBookmarkSource


def default_sources() -> list[Source]:
    """既定で使うソース一覧を返す。

    google_news と hatena は認証不要で常に有効。Bluesky は `.env` / 環境変数に
    認証情報（BLUESKY_HANDLE / BLUESKY_APP_PASSWORD）がある場合のみ追加する
    （未設定なら自動的にスキップ）。
    """
    sources: list[Source] = [GoogleNewsSource(), HatenaBookmarkSource()]

    handle, password = get_bluesky_credentials()
    if handle and password:
        sources.append(BlueskySource(handle, password))

    return sources


__all__ = [
    "Source",
    "GoogleNewsSource",
    "HatenaBookmarkSource",
    "BlueskySource",
    "default_sources",
]
