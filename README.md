# egosa — 上場企業 炎上チェッカー

上場企業が「ネット上で炎上しているか」を、ニュース記事中の**ネガティブワード件数**で
ざっくり把握するためのCLIツールです。記事の詳細は読まず、炎上・不祥事・減益・売上下落
などのワードがどれだけ出ているかをカウントします。

- 個人利用向け
- **無料ライブラリのみ**（`feedparser`）
- **公開RSS / 公式APIのみ**を利用（スクレイピングはしません）

## 情報源

- **Google News RSS**（APIキー不要・日本語ニュース）

> 後続で Reddit / Bluesky などの公式APIにも対応予定です。

## 対象企業

プロジェクト直下の `上場企業一覧.csv`（JPX形式）から、**事業会社（内国株式：
プライム / スタンダード / グロース）**のみを対象とします。ETF・REIT・PRO Market・
外国株式は除外します。

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使い方

```bash
# 銘柄名で検索
python -m egosa.cli "トヨタ"

# 証券コードで検索
python -m egosa.cli 7203

# 炎上記事のタイトルも表示、取得件数を指定
python -m egosa.cli "任天堂" --show-titles --limit 30

# JSON出力
python -m egosa.cli "トヨタ" --json
```

### 一括スキャン＆炎上ランキング（PR #2）

複数企業をまとめてスキャンし、炎上スコア順のランキングと CSV/JSON レポートを出力します。

```bash
# 全事業会社をスキャン（既定: 1社1秒待機。全件は約1時間かかります）
python -m egosa.batch

# 市場・業種で絞り込み
python -m egosa.batch --market プライム
python -m egosa.batch --sector 情報・通信

# 件数を絞ってお試し（先頭5社）
python -m egosa.batch --limit-companies 5 --delay 0.5

# 中断（Ctrl-C）した続きから再開
python -m egosa.batch --resume
```

- レポートは `reports/flame_ranking.csv`（Excelで開けるBOM付き）と `reports/flame_ranking.json` に出力されます。
- 処理中は `reports/checkpoint.jsonl` に1社ずつ追記され、Ctrl-C で中断しても `--resume` で続きから再開できます。
- `reports/` は `.gitignore` 済みでコミットされません。
- 主なオプション: `--limit`（1社あたり記事数）, `--top`（コンソール表示件数）, `--quiet`（進捗非表示）。

### 出力例（イメージ）

```
■ 対象: 7203 トヨタ自動車
  取得記事数 : 50
  炎上記事数 : 4
  炎上スコア : 4  (比率 8%)
  ヒットワード（多い順）:
    - リコール: 2
    - 下落: 1
    - 訴訟: 1
```

**炎上スコア = ネガティブワードを含む記事数**（PR #1 のシンプルな定義）。

## テスト

```bash
python -m pytest
```

ネットワークアクセス無しで、CSVフィルタ・キーワード集計・スコア算出のロジックを検証します。

## ライセンス / 注意

- 各情報源の利用規約の範囲内で利用してください。
- 取得結果はあくまで簡易的な指標です。ワードの単純一致のため、文脈によっては
  誤検出（例: 「赤字覚悟の大セール」等の前向きな文）が含まれることがあります。

## 開発ロードマップ

- [x] **PR #1**: Google News RSS による炎上ワードカウントCLI
- [x] **PR #2**: CSV一括スキャン / レポート出力 / 炎上ランキング（本リリース）
- [ ] PR #3: Reddit / Bluesky 等のソース追加（`.env` でキー管理）
- [ ] PR #4: 簡易感情分析・ワード重み付け
