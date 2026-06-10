"""設定・秘密情報の読み込み。

秘密情報（Bluesky のアプリパスワード等）は環境変数または `.env` から読み込み、
コードやコミットには一切含めない。`.env` は `.gitignore` 済み。

外部依存を増やさないため、`.env` の読み込みは標準ライブラリだけで簡易実装する。
"""

from __future__ import annotations

import os
from pathlib import Path

# プロジェクト直下の .env を既定とする。
DEFAULT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_dotenv(path: str | Path = DEFAULT_ENV_PATH, *, override: bool = False) -> None:
    """`.env` を読み込み環境変数へ反映する（簡易版）。

    `KEY=VALUE` 形式の行のみ対象。`#` 始まりの行と空行は無視。値の前後の
    空白とクオートは除去する。既存の環境変数は override=False の場合は上書きしない。

    Args:
        path: .env ファイルパス。存在しなければ何もしない。
        override: True なら既存の環境変数も上書きする。
    """
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value


def get_bluesky_credentials() -> tuple[str | None, str | None]:
    """Bluesky の認証情報 (handle, app_password) を返す。

    `.env`（または環境変数）の BLUESKY_HANDLE / BLUESKY_APP_PASSWORD を参照する。
    未設定の項目は None。
    """
    load_dotenv()
    handle = os.environ.get("BLUESKY_HANDLE") or None
    password = os.environ.get("BLUESKY_APP_PASSWORD") or None
    return handle, password
