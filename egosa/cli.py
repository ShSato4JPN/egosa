"""コマンドライン入口。

使い方:
    python -m egosa.cli "トヨタ"          # 銘柄名で検索
    python -m egosa.cli 7203              # 証券コードで検索
    python -m egosa.cli "トヨタ" --json   # JSON出力
    python -m egosa.cli "トヨタ" --show-titles --limit 30
"""

from __future__ import annotations

import argparse
import json
import sys

from . import companies as companies_mod
from .companies import Company
from .multi import MultiResult, fetch_and_analyze
from .sources import default_sources


def _resolve_company(query: str) -> Company | None:
    """クエリから対象企業を1社決める。

    複数ヒットした場合は先頭を採用しつつ、候補を stderr に表示する。
    CSVに無いクエリ（コードや任意語）でも、検索語そのままで続行できるよう
    None を返したときは呼び出し側でフォールバックする。
    """
    hits = companies_mod.find(query)
    if not hits:
        return None
    if len(hits) > 1:
        print(
            f"[info] 「{query}」は{len(hits)}件ヒットしました。先頭を使用します: "
            f"{hits[0].code} {hits[0].name}",
            file=sys.stderr,
        )
        for c in hits[:10]:
            print(f"        - {c.code} {c.name}（{c.market}）", file=sys.stderr)
    return hits[0]


def _print_human(query: str, company: Company | None, multi: MultiResult, show_titles: bool) -> None:
    """人間向けの整形出力。"""
    result = multi.total
    label = f"{company.code} {company.name}" if company else query
    print(f"■ 対象: {label}")
    print(f"  取得記事数 : {result.total_articles}")
    print(f"  炎上記事数 : {result.flagged_articles}")
    print(f"  炎上スコア : {result.score}  (比率 {result.ratio:.0%})")

    # ソース別の内訳。
    if multi.per_source:
        parts = [
            f"{name}={r.score}/{r.total_articles}件"
            for name, r in multi.per_source.items()
        ]
        print(f"  ソース別   : {', '.join(parts)}")
    if multi.errors:
        for name, msg in multi.errors.items():
            print(f"  [warn] {name} 取得失敗: {msg}", file=sys.stderr)

    if result.keyword_counts:
        print("  ヒットワード（多い順）:")
        for kw, n in result.keyword_counts.items():
            print(f"    - {kw}: {n}")
    else:
        print("  ヒットワード: なし（炎上の兆候は検出されませんでした）")

    if show_titles and result.flagged:
        print("  炎上記事タイトル:")
        for article, hits in result.flagged:
            kw_str = ", ".join(hits.keys())
            src = f"({article.source}) " if article.source else ""
            print(f"    - {src}[{kw_str}] {article.title}")


def _build_payload(query: str, company: Company | None, multi: MultiResult, show_titles: bool) -> dict:
    """JSON出力用の辞書を組み立てる。"""
    result = multi.total
    payload: dict = {
        "query": query,
        "company": (
            {"code": company.code, "name": company.name, "market": company.market}
            if company
            else None
        ),
        "total_articles": result.total_articles,
        "flagged_articles": result.flagged_articles,
        "score": result.score,
        "ratio": round(result.ratio, 4),
        "keyword_counts": result.keyword_counts,
        "source_scores": multi.source_scores,
        "source_articles": multi.source_articles,
        "errors": multi.errors,
    }
    if show_titles:
        payload["flagged"] = [
            {"title": a.title, "link": a.link, "source": a.source, "keywords": hits}
            for a, hits in result.flagged
        ]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="egosa",
        description="上場企業の炎上チェッカー（複数ソースのネガティブワード件数をカウント）",
    )
    parser.add_argument("query", help="企業名（部分一致）または証券コード")
    parser.add_argument("--limit", type=int, default=50, help="取得する記事の上限（既定: 50）")
    parser.add_argument("--json", action="store_true", help="JSON形式で出力")
    parser.add_argument("--show-titles", action="store_true", help="炎上記事のタイトルも表示")
    args = parser.parse_args(argv)

    company = _resolve_company(args.query)
    # 検索語: 企業がCSVで特定できたら正式名称、できなければ入力語をそのまま使う。
    search_term = company.name if company else args.query

    multi = fetch_and_analyze(search_term, default_sources(), limit=args.limit)
    if multi.all_failed:
        for name, msg in multi.errors.items():
            print(f"[error] {name} 取得失敗: {msg}", file=sys.stderr)
        return 2

    if args.json:
        payload = _build_payload(args.query, company, multi, args.show_titles)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(args.query, company, multi, args.show_titles)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
