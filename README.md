# taskest (minimal)
自然文→タスク分解→一般エンジニア基準の概算工数を出す**ローカルCLI**。QA併記/加算、バッファ対応。単一ファイル版。

## 使い方
```bash
python taskest.py "PlaywrightでE2E整備し、LHCI閾値0.8でCI落とす" --qa --buffer 1.2
python taskest.py "SeleniumでE2E、axeでa11y自動チェック" --qa --qa-include --buffer 1.1 --qa-buffer 1.3 --buffer-per-task
```

## オプション
- `--format md|json`
- `--profile general|conservative|fast`
- `--qa` / `--qa-include`
- `--buffer` / `--qa-buffer` / `--buffer-per-task`

> これは“見積り前工程の手元ツール”。CI自動化はしません。
