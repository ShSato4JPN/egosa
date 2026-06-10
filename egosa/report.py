"""スキャン結果（ScanRow）をランキング化し、CSV/JSONレポートに出力する。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .scanner import ScanRow


def rank(rows: list[ScanRow]) -> list[ScanRow]:
    """炎上スコア降順に並べ替える（同点は比率→記事数の降順）。

    エラー行（取得失敗）は末尾にまとめる。
    """
    ok = [r for r in rows if not r.error]
    err = [r for r in rows if r.error]
    ok.sort(key=lambda r: (r.score, r.ratio, r.total_articles), reverse=True)
    return ok + err


def _top_keywords(row: ScanRow, n: int = 3) -> str:
    """ヒットワード上位を "炎上:2; 下落:1" 形式の文字列にする。"""
    items = sorted(row.keyword_counts.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return "; ".join(f"{k}:{v}" for k, v in items)


def _source_breakdown(row: ScanRow) -> str:
    """ソース別スコアを "google_news:2; hatena:1" 形式の文字列にする。"""
    return "; ".join(f"{name}:{score}" for name, score in row.source_scores.items())


def write_csv(rows: list[ScanRow], path: str | Path) -> Path:
    """ランキングをCSVに書き出す。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ranked = rank(rows)
    with p.open("w", encoding="utf-8-sig", newline="") as f:  # Excel向けにBOM付き
        writer = csv.writer(f)
        writer.writerow(
            ["順位", "コード", "銘柄名", "市場", "炎上スコア", "炎上記事数", "総記事数",
             "比率", "ソース別", "主なワード", "エラー"]
        )
        for i, r in enumerate(ranked, start=1):
            writer.writerow(
                [
                    i,
                    r.code,
                    r.name,
                    r.market,
                    r.score,
                    r.flagged_articles,
                    r.total_articles,
                    f"{r.ratio:.4f}",
                    _source_breakdown(r),
                    _top_keywords(r),
                    r.error,
                ]
            )
    return p


def write_json(rows: list[ScanRow], path: str | Path) -> Path:
    """ランキングをJSONに書き出す。"""
    from dataclasses import asdict

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ranked = rank(rows)
    payload = [asdict(r) for r in ranked]
    with p.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return p


def format_top(rows: list[ScanRow], top: int = 20) -> str:
    """コンソール表示用に上位ランキングを整形する。"""
    ranked = [r for r in rank(rows) if not r.error][:top]
    if not ranked:
        return "（炎上スコアの付いた企業はありませんでした）"
    lines = [f"{'順位':>3} {'コード':<6} {'銘柄名':<20} {'スコア':>5} {'比率':>5}  主なワード"]
    for i, r in enumerate(ranked, start=1):
        lines.append(
            f"{i:>3} {r.code:<6} {r.name:<20.20} {r.score:>5} {r.ratio:>4.0%}  {_top_keywords(r)}"
        )
    return "\n".join(lines)
