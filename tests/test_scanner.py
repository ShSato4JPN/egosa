from egosa.companies import Company
from egosa.scanner import ScanRow, load_checkpoint, scan
from egosa.sources.base import Article


class FakeSource:
    """ネット不要のテスト用ソース。企業名→記事 を辞書で返す。"""

    name = "fake"

    def __init__(self, mapping, fail_codes=()):
        self.mapping = mapping
        self.fail_names = set(fail_codes)
        self.calls = []

    def fetch(self, query, limit=50):
        self.calls.append(query)
        if query in self.fail_names:
            raise RuntimeError("boom")
        return self.mapping.get(query, [])


def _companies():
    return [
        Company(code="0001", name="炎上社", market="プライム（内国株式）"),
        Company(code="0002", name="平穏社", market="スタンダード（内国株式）"),
        Company(code="0003", name="失敗社", market="グロース（内国株式）"),
    ]


def _source():
    return FakeSource(
        mapping={
            "炎上社": [Article(title="不祥事で炎上、株価急落"), Article(title="さらに減益")],
            "平穏社": [Article(title="増収増益で好調")],
        },
        fail_codes={"失敗社"},
    )


def test_scan_basic_scores():
    rows = scan(_companies(), [_source()], delay=0)
    by_code = {r.code: r for r in rows}
    assert by_code["0001"].score == 2  # 2記事ともネガ
    assert by_code["0002"].score == 0
    assert by_code["0003"].error  # 例外はerrorに記録


def test_scan_continues_after_error():
    rows = scan(_companies(), [_source()], delay=0)
    # 失敗社(3件目)で止まらず全件処理される。
    assert len(rows) == 3


def test_checkpoint_written_and_resumed(tmp_path):
    ckpt = tmp_path / "ckpt.jsonl"
    src1 = _source()
    scan(_companies(), [src1], delay=0, checkpoint_path=ckpt)
    assert ckpt.exists()

    loaded = load_checkpoint(ckpt)
    assert set(loaded.keys()) == {"0001", "0002", "0003"}

    # 再開時は全社完了済みなので fetch は呼ばれない。
    src2 = _source()
    rows = scan(_companies(), [src2], delay=0, checkpoint_path=ckpt, resume=True)
    assert src2.calls == []
    assert len(rows) == 3


def test_progress_callback_called():
    seen = []
    scan(_companies(), [_source()], delay=0, progress=lambda i, t, r: seen.append((i, t)))
    assert seen == [(1, 3), (2, 3), (3, 3)]


def test_scanrow_json_roundtrip():
    row = ScanRow(code="0001", name="A", market="M", score=2, keyword_counts={"炎上": 1})
    again = ScanRow.from_json_line(row.to_json_line())
    assert again == row
