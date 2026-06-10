"""Bluesky（AT Protocol）の検索APIから企業名で投稿を取得する情報源。

公式API。アプリパスワード（Settings > App Passwords で発行）で認証する。
認証情報は `.env` / 環境変数から読み込み、コードには含めない。

- 認証:   POST {service}/xrpc/com.atproto.server.createSession
- 投稿検索: GET  {service}/xrpc/app.bsky.feed.searchPosts?q=...&limit=...
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .base import Article

_DEFAULT_SERVICE = "https://bsky.social"
_USER_AGENT = "egosa/0.1 (personal reputation checker; +https://github.com/ShSato4JPN/egosa)"
_TIMEOUT_SEC = 15


class BlueskySource:
    """Bluesky 検索APIをソースとして扱うクラス。

    認証はインスタンス内で遅延実行し、accessJwt をキャッシュする。
    """

    name = "bluesky"

    def __init__(
        self,
        handle: str,
        app_password: str,
        *,
        service: str = _DEFAULT_SERVICE,
        timeout: int = _TIMEOUT_SEC,
    ) -> None:
        self.handle = handle
        self.app_password = app_password
        self.service = service.rstrip("/")
        self.timeout = timeout
        self._jwt: str | None = None

    # --- HTTP ヘルパ（テストではここを差し替え可能） ---
    def _http_json(self, url: str, *, data: dict | None = None, token: str | None = None) -> dict:
        """JSON API を叩いて辞書を返す。data 指定時は POST、無ければ GET。"""
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            return json.loads(resp.read())

    def _login(self) -> str:
        """createSession で accessJwt を取得（キャッシュ）。"""
        if self._jwt:
            return self._jwt
        url = f"{self.service}/xrpc/com.atproto.server.createSession"
        result = self._http_json(
            url, data={"identifier": self.handle, "password": self.app_password}
        )
        jwt = result.get("accessJwt")
        if not jwt:
            raise RuntimeError("Bluesky 認証に失敗しました（accessJwt が取得できません）")
        self._jwt = jwt
        return jwt

    def fetch(self, query: str, limit: int = 50) -> list[Article]:
        """企業名で投稿を検索し Article のリストを返す。

        ネットワーク／認証エラー時は例外を送出する（呼び出し側でハンドリング）。
        """
        token = self._login()
        # searchPosts の limit は 1〜100。
        params = {"q": query, "limit": str(max(1, min(limit, 100)))}
        url = f"{self.service}/xrpc/app.bsky.feed.searchPosts?{urllib.parse.urlencode(params)}"
        result = self._http_json(url, token=token)

        articles: list[Article] = []
        for post in result.get("posts", [])[:limit]:
            record = post.get("record") or {}
            text = record.get("text", "") or ""
            author = (post.get("author") or {}).get("handle", "")
            uri = post.get("uri", "") or ""
            articles.append(
                Article(
                    title=text,                       # 投稿本文をタイトル扱い（ワード判定対象）
                    summary="",
                    link=_post_url(author, uri),
                    published=record.get("createdAt", "") or "",
                    source=self.name,
                )
            )
        return articles


def _post_url(handle: str, uri: str) -> str:
    """at:// URI から bsky.app の投稿URLを組み立てる（失敗時は uri をそのまま返す）。"""
    # uri 例: at://did:plc:xxxx/app.bsky.feed.post/3kabc...
    if handle and uri.startswith("at://"):
        rkey = uri.rsplit("/", 1)[-1]
        return f"https://bsky.app/profile/{handle}/post/{rkey}"
    return uri
