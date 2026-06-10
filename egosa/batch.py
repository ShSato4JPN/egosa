"""一括スキャンのコマンドライン入口。

使い方:
    # 全事業会社をスキャン（既定: 1社1秒待機、レポートは reports/ に出力）
    python -m egosa.batch

    # 市場・業種で絞り込み
    python -m egosa.batch --market プライム
    python -m egosa.batch --sector 情報・通信

    # 件数を絞ってお試し
    python -m egosa.batch --limit-companies 50

    # 中断した続きから再開
    python -m egosa.batch --resume

注意: 全件(約3700社)は --delay 1.0 で1時間程度かかります。Ctrl-C で中断しても
チェックポイント(reports/checkpoint.jsonl)に保存され、--resume で続きから再開できます。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .companies import filter_companies, load_companies
from .report import format_top, rank, write_csv, write_json
from .scanner import ScanRow, scan
from .sources.google_news import GoogleNewsSource

DEFAULT_OUT_DIR = Path("reports")
DEFAULT_CHECKPOINT = DEFAULT_OUT_DIR / "checkpoint.jsonl"


def _make_progress(quiet: bool):
    """進捗をstderrに出すコールバックを生成する。"""
    def progress(i: int, total: int, row: ScanRow) -> None:
        if quiet:
            return
        mark = "ERR" if row.error else (f"🔥{row.score}" if row.score else "  -")
        print(f"\r[{i}/{total}] {row.code} {row.name[:16]:<16} {mark}      ", end="", file=sys.stderr)
        if i == total:
            print("", file=sys.stderr)  # 改行
    return progress


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="egosa-batch",
        description="上場企業を一括スキャンして炎上ランキングを出力する",
    )
    parser.add_argument("--market", help="市場・商品区分でフィルタ（部分一致, 例: プライム）")
    parser.add_argument("--sector", help="業種でフィルタ（部分一致, 例: 情報・通信）")
    parser.add_argument("--limit-companies", type=int, default=0, help="対象企業数の上限（0=全件）")
    parser.add_argument("--limit", type=int, default=50, help="1社あたりの取得記事上限（既定: 50）")
    parser.add_argument("--delay", type=float, default=1.0, help="1社ごとの待機秒数（既定: 1.0）")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="レポート出力先ディレクトリ")
    parser.add_argument("--checkpoint", default=None, help="チェックポイントJSONLのパス")
    parser.add_argument("--resume", action="store_true", help="チェックポイントの続きから再開")
    parser.add_argument("--top", type=int, default=20, help="コンソールに表示する上位件数（既定: 20）")
    parser.add_argument("--quiet", action="store_true", help="進捗表示を抑制")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    checkpoint = Path(args.checkpoint) if args.checkpoint else out_dir / "checkpoint.jsonl"

    companies = load_companies()
    companies = filter_companies(companies, market=args.market, sector=args.sector)
    if args.limit_companies and args.limit_companies > 0:
        companies = companies[: args.limit_companies]

    if not companies:
        print("[error] 対象企業が0件です。--market / --sector の条件を見直してください。", file=sys.stderr)
        return 1

    print(f"[info] 対象 {len(companies)} 社をスキャンします（delay={args.delay}s）。", file=sys.stderr)
    if args.resume:
        print(f"[info] チェックポイント {checkpoint} から再開します。", file=sys.stderr)

    source = GoogleNewsSource()
    try:
        rows = scan(
            companies,
            source,
            limit=args.limit,
            delay=args.delay,
            checkpoint_path=checkpoint,
            resume=args.resume,
            progress=_make_progress(args.quiet),
        )
    except KeyboardInterrupt:
        print(
            f"\n[info] 中断しました。{checkpoint} に途中結果を保存済みです。"
            f" `--resume` で再開できます。",
            file=sys.stderr,
        )
        return 130

    # レポート出力。
    csv_path = write_csv(rows, out_dir / "flame_ranking.csv")
    json_path = write_json(rows, out_dir / "flame_ranking.json")

    ok = [r for r in rows if not r.error]
    err = [r for r in rows if r.error]
    flamed = [r for r in ok if r.score > 0]

    print("", file=sys.stderr)
    print(f"[done] スキャン完了: {len(rows)}社（成功 {len(ok)} / 失敗 {len(err)} / 炎上検出 {len(flamed)}）", file=sys.stderr)
    print(f"[done] レポート: {csv_path} , {json_path}", file=sys.stderr)
    print(file=sys.stderr)

    # コンソールに上位ランキングを表示。
    print(format_top(rows, top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
