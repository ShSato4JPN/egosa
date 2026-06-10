import csv
import json

from egosa.report import format_top, rank, write_csv, write_json
from egosa.scanner import ScanRow


def _rows():
    return [
        ScanRow(code="0001", name="低", market="M", total_articles=10, flagged_articles=1, score=1, ratio=0.1),
        ScanRow(code="0002", name="高", market="M", total_articles=10, flagged_articles=5, score=5, ratio=0.5,
                keyword_counts={"炎上": 3, "下落": 2}, source_scores={"google_news": 3, "hatena": 2}),
        ScanRow(code="0003", name="失敗", market="M", error="URLError: x"),
    ]


def test_rank_orders_by_score_desc_errors_last():
    ranked = rank(_rows())
    assert [r.code for r in ranked] == ["0002", "0001", "0003"]
    assert ranked[-1].error  # エラーは末尾


def test_write_csv(tmp_path):
    p = write_csv(_rows(), tmp_path / "out.csv")
    with p.open(encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))
    assert reader[0][0] == "順位"
    # 先頭データ行は最高スコアの企業。
    assert reader[1][1] == "0002"
    # ソース別列・主なワード列の中身を確認。
    header = reader[0]
    src_col = header.index("ソース別")
    kw_col = header.index("主なワード")
    assert "google_news:3" in reader[1][src_col]
    assert "炎上:3" in reader[1][kw_col]


def test_write_json(tmp_path):
    p = write_json(_rows(), tmp_path / "out.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data[0]["code"] == "0002"


def test_format_top_excludes_errors():
    out = format_top(_rows(), top=10)
    assert "0002" in out
    assert "失敗" not in out  # エラー行は表示しない
