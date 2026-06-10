from egosa.sources import BlueskySource, default_sources


def _disable_env(monkeypatch, tmp_path):
    monkeypatch.delenv("BLUESKY_HANDLE", raising=False)
    monkeypatch.delenv("BLUESKY_APP_PASSWORD", raising=False)
    monkeypatch.setattr("egosa.config.DEFAULT_ENV_PATH", tmp_path / "nope.env")


def test_default_sources_skip_bluesky_when_unset(monkeypatch, tmp_path):
    _disable_env(monkeypatch, tmp_path)
    names = [s.name for s in default_sources()]
    assert names == ["google_news", "hatena"]
    assert "bluesky" not in names


def test_default_sources_include_bluesky_when_set(monkeypatch, tmp_path):
    _disable_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BLUESKY_HANDLE", "alice.bsky.social")
    monkeypatch.setenv("BLUESKY_APP_PASSWORD", "app-pass")
    sources = default_sources()
    names = [s.name for s in sources]
    assert names == ["google_news", "hatena", "bluesky"]
    assert isinstance(sources[-1], BlueskySource)
