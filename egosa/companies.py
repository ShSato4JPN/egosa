"""上場企業一覧CSVの読み込み・フィルタ・検索。

JPXが公開する形式のCSV（ヘッダ: 日付,コード,銘柄名,市場・商品区分, ...）を読み込み、
事業会社（内国株式）のみを対象とする。ETF・REIT・PRO Market・外国株式は除外する。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

# プロジェクト直下の既定CSVパス。
DEFAULT_CSV = Path(__file__).resolve().parent.parent / "上場企業一覧.csv"

# 「市場・商品区分」にこの文字列を含む行のみ事業会社として採用する。
# 例: プライム（内国株式）/ スタンダード（内国株式）/ グロース（内国株式）
DOMESTIC_MARKET_MARKER = "（内国株式）"


@dataclass(frozen=True)
class Company:
    """1社分の企業情報。"""

    code: str          # 証券コード（例: "7203"）
    name: str          # 銘柄名（例: "トヨタ自動車"）
    market: str        # 市場・商品区分
    sector33: str = ""  # 33業種区分
    sector17: str = ""  # 17業種区分


def load_companies(csv_path: str | Path = DEFAULT_CSV) -> list[Company]:
    """CSVを読み込み、事業会社（内国株式）のみのリストを返す。

    Args:
        csv_path: CSVファイルのパス。

    Returns:
        Company のリスト。
    """
    path = Path(csv_path)
    companies: list[Company] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            market = (row.get("市場・商品区分") or "").strip()
            if DOMESTIC_MARKET_MARKER not in market:
                continue
            code = (row.get("コード") or "").strip()
            name = (row.get("銘柄名") or "").strip()
            if not code or not name:
                continue
            companies.append(
                Company(
                    code=code,
                    name=name,
                    market=market,
                    sector33=(row.get("33業種区分") or "").strip(),
                    sector17=(row.get("17業種区分") or "").strip(),
                )
            )
    return companies


def find(query: str, companies: list[Company] | None = None) -> list[Company]:
    """証券コード（完全一致）または銘柄名（部分一致）で企業を検索する。

    数字のみのクエリはまず証券コードの完全一致を試み、見つからなければ
    名前の部分一致にフォールバックする。

    Args:
        query: 検索クエリ（証券コード or 銘柄名の一部）。
        companies: 検索対象。未指定なら既定CSVから読み込む。

    Returns:
        マッチした Company のリスト（マッチなしなら空）。
    """
    if companies is None:
        companies = load_companies()

    q = query.strip()
    if not q:
        return []

    # 証券コード完全一致を最優先。
    code_hits = [c for c in companies if c.code == q]
    if code_hits:
        return code_hits

    # 銘柄名の完全一致を次に優先（「トヨタ」より「トヨタ自動車」狙いを尊重）。
    q_lower = q.lower()
    name_exact = [c for c in companies if c.name.lower() == q_lower]
    if name_exact:
        return name_exact

    # 最後に銘柄名の部分一致。完全一致に近い（短い名前）順に並べる。
    partial = [c for c in companies if q_lower in c.name.lower()]
    partial.sort(key=lambda c: len(c.name))
    return partial
