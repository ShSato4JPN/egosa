"""評判の情報源（ソース）。差し替え可能なインターフェースで提供する。"""

from __future__ import annotations

from .base import Source
from .google_news import GoogleNewsSource
from .hatena import HatenaBookmarkSource


def default_sources() -> list[Source]:
    """既定で使う認証不要のソース一覧を返す。"""
    return [GoogleNewsSource(), HatenaBookmarkSource()]


__all__ = ["Source", "GoogleNewsSource", "HatenaBookmarkSource", "default_sources"]
