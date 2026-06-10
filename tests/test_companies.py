from pathlib import Path

from egosa.companies import find, load_companies

FIXTURE = Path(__file__).parent / "fixtures" / "sample_companies.csv"


def test_load_excludes_etf_and_foreign():
    companies = load_companies(FIXTURE)
    codes = {c.code for c in companies}
    # 内国株式のみ採用される。
    assert codes == {"1301", "7203", "7974", "3990"}
    # ETF・外国株式は除外。
    assert "1306" not in codes  # ETF
    assert "9999" not in codes  # 外国株式


def test_find_by_code_exact():
    companies = load_companies(FIXTURE)
    hits = find("7203", companies)
    assert len(hits) == 1
    assert hits[0].name == "トヨタ自動車"


def test_find_by_name_partial():
    companies = load_companies(FIXTURE)
    hits = find("トヨタ", companies)
    assert len(hits) == 1
    assert hits[0].code == "7203"


def test_find_no_match_returns_empty():
    companies = load_companies(FIXTURE)
    assert find("存在しない企業", companies) == []


def test_find_empty_query():
    companies = load_companies(FIXTURE)
    assert find("   ", companies) == []
