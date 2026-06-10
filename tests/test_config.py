import os

from egosa.config import get_bluesky_credentials, load_dotenv


def test_load_dotenv_sets_vars(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        '# comment\n'
        'BLUESKY_HANDLE=alice.bsky.social\n'
        'BLUESKY_APP_PASSWORD="abcd-efgh"\n'
        '\n'
        'EMPTY_LINE_IGNORED\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("BLUESKY_HANDLE", raising=False)
    monkeypatch.delenv("BLUESKY_APP_PASSWORD", raising=False)

    load_dotenv(env)
    assert os.environ["BLUESKY_HANDLE"] == "alice.bsky.social"
    assert os.environ["BLUESKY_APP_PASSWORD"] == "abcd-efgh"  # クオート除去


def test_load_dotenv_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("BLUESKY_HANDLE=fromfile\n", encoding="utf-8")
    monkeypatch.setenv("BLUESKY_HANDLE", "fromenv")

    load_dotenv(env)  # override=False
    assert os.environ["BLUESKY_HANDLE"] == "fromenv"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    load_dotenv(tmp_path / "nope.env")  # 例外を出さない


def test_get_bluesky_credentials_none_when_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("BLUESKY_HANDLE", raising=False)
    monkeypatch.delenv("BLUESKY_APP_PASSWORD", raising=False)
    # 存在しない .env を指して、環境変数も無い状態にする。
    monkeypatch.setattr("egosa.config.DEFAULT_ENV_PATH", tmp_path / "nope.env")
    assert get_bluesky_credentials() == (None, None)
