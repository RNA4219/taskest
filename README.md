This repository is an R&D artifact and is not used in my current workflow. Keeping it as an archive.

# taskest (minimal)
自然文→タスク分解→一般エンジニア基準の概算工数を出す**ローカルCLI**。QA併記/加算、バッファ対応。単一ファイル版。

## 使い方
```bash
python taskest.py "PlaywrightでE2E整備し、LHCI閾値0.8でCI落とす" --qa --buffer 1.2
python taskest.py "SeleniumでE2E、axeでa11y自動チェック" --qa --qa-include --buffer 1.1 --qa-buffer 1.3 --buffer-per-task
```

## 使用例
```bash
$ python taskest.py "API+Admin構築" --qa --buffer 1.1
**原文**：API+Admin構築

*Buffer(core)×1.10, Buffer(QA)×1.10（タスク行は素の値、総計のみ適用）*

| # | タスク | 難易度/根拠 | 領域/根拠 | コアh | QA h | 表示 |
|---|---|---|---|---:|---:|---:|
| 1 | API+Admin構築 | easy (default) | backend (kw:api) | 1.2h | 0.0h | 1.2h |

**タスク別メモ**

1. API+Admin構築 … base 1.0h × domain 1.20 × first_time 1.00 × platforms 1.00

**QA補助（検出時のみ）**

| タスク | QA種別 | 推奨成果物 | 想定ケース数 | QA見積(時間, バッファ後) |
|---|---|---|---:|---:|

**積算（general）**：Core **1.3h** + QA **0.0h**
```

## オプション
- `--format md|json`
- `--profile general|conservative|fast`
- `--qa` / `--qa-include`
- `--buffer` / `--qa-buffer` / `--buffer-per-task`

> これは“見積り前工程の手元ツール”。CI自動化はしません。
