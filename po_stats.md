# po_stats.py - PO ファイル翻訳完了率表示ツール

指定した言語コードの PO ファイルをリストし、各ファイルの翻訳完了率を表示します。

## 使い方

```
python po_stats.py <言語コード> [オプション]
```

## オプション

| オプション | 説明 |
|---|---|
| `--sort` | 翻訳完了率の低い順にソートして表示 |
| `--min-pct N` | 完了率が N% 未満のファイルのみ表示 |
| `--bar` | 進捗バーを表示する |

## 使用例

```powershell
# 日本語の全 PO ファイルの翻訳完了率を表示
python po_stats.py ja

# 完了率の低い順にソート
python po_stats.py ja --sort

# 完了率が 80% 未満のファイルのみ表示
python po_stats.py ja --min-pct 80

# ソート＋絞り込み＋進捗バー表示
python po_stats.py ja --sort --min-pct 80 --bar
```

## 出力例

```
Language: ja
------------------------------------------------------------------------------------------
File                                                      Translated  Fuzzy  Total    Rate
------------------------------------------------------------------------------------------
docs\about\index.po                                                0      0      1    0.0%
docs\gentle_gis_introduction\authors_and_contributors.po           3      0      7   42.9%
docs\user_manual\auth_system\auth_overview.po                     62      0    112   55.4%
...
------------------------------------------------------------------------------------------
TOTAL                                                          37475      0  38579   97.1%
```

`--bar` オプションを付けると Rate 列の右に進捗バーが追加されます。

```
docs\about\index.po   0    0  1    0.0%  [...................]
docs\about\foreword.po   8    0  8  100.0%  [####################]
```

## 出力列の説明

| 列 | 内容 |
|---|---|
| File | locale/&lt;言語コード&gt;/LC_MESSAGES/ からの相対パス |
| Translated | 翻訳済みエントリ数 |
| Fuzzy | ファジー（要確認）エントリ数 |
| Total | 全エントリ数（ファイルヘッダーを除く） |
| Rate | 翻訳完了率 (Translated / Total × 100) |

## 注意事項

- 言語コードが存在しない場合、利用可能な言語コードの一覧を表示します。
- Fuzzy エントリは翻訳済みにカウントされません。
- `--min-pct` と `--sort` は組み合わせて使用できます。
