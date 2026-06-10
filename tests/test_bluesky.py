import pytest

from egosa.sources.bluesky import BlueskySource, _post_url


def _fake_http(responses):
    """URLに応じて canned レスポンスを返す _http_json 差し替え関数を作る。"""
    calls = []

    def _http_json(url, *, data=None, token=None):
        calls.append({"url": url, "data": data, "token": token})
        if "createSession" in url:
            return responses["session"]
        if "searchPosts" in url:
            return responses["search"]
        raise AssertionError(f"unexpected url: {url}")

    _http_json.calls = calls
    return _http_json


def test_fetch_parses_posts(monkeypatch):
    src = BlueskySource("alice.bsky.social", "app-pass")
    fake = _fake_http(
        {
            "session": {"accessJwt": "JWT123"},
            "search": {
                "posts": [
                    {
                        "uri": "at://did:plc:xx/app.bsky.feed.post/3kabc",
                        "author": {"handle": "bob.bsky.social"},
                        "record": {"text": "A社が炎上してる", "createdAt": "2026-01-01T00:00:00Z"},
                    },
                    {
                        "uri": "at://did:plc:yy/app.bsky.feed.post/3kdef",
                        "author": {"handle": "carol.bsky.social"},
                        "record": {"text": "普通の投稿"},
                    },
                ]
            },
        }
    )
    monkeypatch.setattr(src, "_http_json", fake)

    articles = src.fetch("A社", limit=10)
    assert len(articles) == 2
    assert articles[0].title == "A社が炎上してる"
    assert articles[0].source == "bluesky"
    assert articles[0].link == "https://bsky.app/profile/bob.bsky.social/post/3kabc"
    # 認証は1回だけ、検索にトークンが渡る。
    assert fake.calls[0]["data"] == {"identifier": "alice.bsky.social", "password": "app-pass"}
    assert fake.calls[1]["token"] == "JWT123"


def test_login_cached(monkeypatch):
    src = BlueskySource("alice.bsky.social", "app-pass")
    fake = _fake_http({"session": {"accessJwt": "JWT"}, "search": {"posts": []}})
    monkeypatch.setattr(src, "_http_json", fake)

    src.fetch("X")
    src.fetch("Y")
    # createSession は最初の1回のみ。
    session_calls = [c for c in fake.calls if "createSession" in c["url"]]
    assert len(session_calls) == 1


def test_login_failure_raises(monkeypatch):
    src = BlueskySource("alice.bsky.social", "wrong")
    fake = _fake_http({"session": {}, "search": {"posts": []}})  # accessJwt 無し
    monkeypatch.setattr(src, "_http_json", fake)
    with pytest.raises(RuntimeError):
        src.fetch("X")


def test_post_url_fallback():
    assert _post_url("", "https://example.com/x") == "https://example.com/x"
    assert _post_url("bob", "at://did/app.bsky.feed.post/abc") == "https://bsky.app/profile/bob/post/abc"
