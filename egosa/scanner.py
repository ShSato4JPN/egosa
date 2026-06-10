"""複数企業を一括スキャンし、炎上スコアを集計する。

大量の企業を順に処理するため、以下を備える:
- リクエスト間の待機（rate limit対策、相手サーバへの配慮）
- エラー発生時は当該企業をスキップして継続
- チェックポイント(JSONL)への逐次書き出しと、途中再開
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .companies import Company
from .multi import fetch_and_analyze
from .sources.base import Source


@dataclass
class ScanRow:
    """1社分のスキャン結果（レポート/チェックポイントの1行）。"""

    code: str
    name: str
    market: str
    total_articles: int = 0
    flagged_articles: int = 0
    score: int = 0
    ratio: float = 0.0
    keyword_counts: dict[str, int] = field(default_factory=dict)
    source_scores: dict[str, int] = field(default_factory=dict)  # ソース別の炎上スコア
    error: str = ""  # 全ソース失敗時のメッセージ（成功時は空）

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "ScanRow":
        data = json.loads(line)
        return cls(**data)


def load_checkpoint(path: str | Path) -> dict[str, ScanRow]:
    """チェックポイントJSONLを読み込み {証券コード: ScanRow} を返す。

    ファイルが無ければ空dict。壊れた行はスキップする。
    """
    p = Path(path)
    rows: dict[str, ScanRow] = {}
    if not p.exists():
        return rows
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = ScanRow.from_json_line(line)
            except (json.JSONDecodeError, TypeError):
                continue
            rows[row.code] = row
    return rows


def scan(
    companies: list[Company],
    sources: list[Source],
    *,
    limit: int = 50,
    delay: float = 1.0,
    checkpoint_path: str | Path | None = None,
    resume: bool = False,
    progress: Callable[[int, int, ScanRow], None] | None = None,
) -> list[ScanRow]:
    """企業リストを一括スキャンして ScanRow のリストを返す。

    Args:
        companies: 対象企業。
        sources: 情報源のリスト（GoogleNewsSource, HatenaBookmarkSource など）。
        limit: 1社あたりの取得記事上限。
        delay: 各社の処理後に待機する秒数（rate limit対策）。
        checkpoint_path: 指定すると1社ごとに結果をJSONL追記する。
        resume: True かつ checkpoint_path が既存なら、完了済みの企業をスキップする。
        progress: (現在index, 総数, ScanRow) を受け取る進捗コールバック。

    Returns:
        全対象企業の ScanRow（resume時は既存分も含む）。

    KeyboardInterrupt が発生してもチェックポイントは保全される（逐次追記のため）。
    """
    done: dict[str, ScanRow] = {}
    if resume and checkpoint_path is not None:
        done = load_checkpoint(checkpoint_path)

    results: list[ScanRow] = []
    ckpt_file = None
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        ckpt_file = Path(checkpoint_path).open("a", encoding="utf-8")

    total = len(companies)
    try:
        for i, company in enumerate(companies, start=1):
            # 再開時、完了済みはそのまま結果へ。
            if company.code in done:
                row = done[company.code]
                results.append(row)
                if progress:
                    progress(i, total, row)
                continue

            row = _scan_one(company, sources, limit=limit)
            results.append(row)

            if ckpt_file is not None:
                ckpt_file.write(row.to_json_line() + "\n")
                ckpt_file.flush()

            if progress:
                progress(i, total, row)

            # 最後の1社の後は待たない。
            if delay > 0 and i < total:
                time.sleep(delay)
    finally:
        if ckpt_file is not None:
            ckpt_file.close()

    return results


def _scan_one(company: Company, sources: list[Source], *, limit: int) -> ScanRow:
    """1社を全ソースでスキャンする。

    各ソースの失敗は multi 層で個別に握りつぶされ、全ソース失敗時のみ error を立てる。
    """
    multi = fetch_and_analyze(company.name, sources, limit=limit)
    total = multi.total
    error = ""
    if multi.all_failed:
        # 全ソース失敗（1件も取得できず）。代表エラーを記録。
        error = "; ".join(f"{name}: {msg}" for name, msg in multi.errors.items())
    return ScanRow(
        code=company.code,
        name=company.name,
        market=company.market,
        total_articles=total.total_articles,
        flagged_articles=total.flagged_articles,
        score=total.score,
        ratio=round(total.ratio, 4),
        keyword_counts=total.keyword_counts,
        source_scores=multi.source_scores,
        error=error,
    )
