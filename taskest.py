#!/usr/bin/env python3
# taskest.py - Task decomposition & effort estimation (general engineer baseline) + QA + Buffers
# Minimal single-file CLI (no deps, no CI)

import argparse, json, re
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

# ---- Base (一般エンジニア基準) -------------------------------------------------
BASE_HOURS = {"easy": 1.0, "medium": 3.0, "hard": 8.0}
DOMAIN_WEIGHTS = {"frontend": 1.0, "backend": 1.2, "infra": 1.5, "rust_gui": 1.7, "security": 1.8}
DOMAIN_KEYWORDS = {
    "frontend": ["ui", "react", "vue", "next", "vite", "pwa", "css", "lighthouse"],
    "backend": ["api", "fastapi", "django", "flask", "express", "go ", "golang", "db", "database"],
    "infra": ["ci", "cd", "actions", "docker", "kubernetes", "deploy", "pipeline", "lint", "test"],
    "rust_gui": ["rust", "tauri", "gtk", "webkitgtk", "cargo"],
    "security": ["セキュリティ", "security", "cve", "codeql", "audit", "oauth", "認証", "認可", "脆弱"],
}
HARD_HINTS = ["大規模", "移行", "破壊的", "migration", "major", "complex", "根本", "全面", "from scratch"]
MED_HINTS  = ["設計", "integration", "統合", "リファクタ", "refactor", "テスト", "組み込み", "埋め込み", "調整"]
EASY_HINTS = ["導入", "設定", "追加", "文書", "ドキュメント", "バッジ", "軽微", "修正", "config", "install", "setup"]
FIRST_TIME_HINTS = ["初導入", "first", "初回", "はじめて", "未導入"]
PLATFORMS = ["windows", "linux", "macos", "android", "ios"]

# ---- QA augmentation -----------------------------------------------------------
QA_TYPES = {
    # name: (keywords, case_minutes, artifacts)
    "qa_unit": (
        ["unit", "単体", "pytest", "unittest", "jest", "mocha", "assert", "mock", "stub", "fixture"],
        15,
        ["テスト設計(単体)", "モック/スタブ", "テストデータ", "カバレッジ閾値"],
    ),
    "qa_integration": (
        ["integration", "統合", "e2e", "playwright", "selenium", "cypress", "browser", "クロスブラウザ"],
        30,
        ["E2E設計", "環境/認証シナリオ", "データ準備", "安定化(待機/リトライ)"],
    ),
    "qa_perf": (
        ["k6", "locust", "load", "性能", "スループット", "レイテンシ", "負荷"],
        45,
        ["シナリオ設計", "目標SLO", "基準線計測", "結果レポート"],
    ),
    "qa_security": (
        ["codeql", "owasp", "zap", "sast", "dast", "脆弱", "依存監査", "audit"],
        45,
        ["ルール/プロファイル", "例外管理", "レポート", "修正方針"],
    ),
    "qa_a11y": (
        ["アクセシビリティ", "a11y", "axe", "pa11y", "screen reader", "wcag"],
        20,
        ["判定基準(WCAG)", "自動/手動併用", "対象画面一覧"],
    ),
    "qa_lighthouse": (
        ["lighthouse", "lhci", "performance", "pwa", "seo", "best practices"],
        10,
        ["LHCI設定", "閾値/バジェット", "レポ保存"],
    ),
}
QA_FLAKY_HINTS = ["flaky", "不安定", "断続的", "sporadic", "タイミング", "待機", "race"]
QA_DATA_HINTS  = ["テストデータ", "seed", "fixture", "サンプルデータ", "ダミー"]
QA_ENV_HINTS   = ["環境構築", "test env", "sandbox", "container", "docker compose"]

def norm(s: str) -> str:
    return s.lower()

def guess_domain(task: str) -> tuple[str, float, str]:
    t = norm(task)
    best = ("frontend", DOMAIN_WEIGHTS["frontend"], "default")
    for d, kws in DOMAIN_KEYWORDS.items():
        for k in kws:
            if k in t:
                return (d, DOMAIN_WEIGHTS[d], f"kw:{k}")
    return best

def guess_difficulty(task: str) -> tuple[str, str]:
    t = task
    def hit(hints): return any(h in t for h in hints)
    if hit(HARD_HINTS):   return ("hard",  "hard:keywords")
    if hit(MED_HINTS):    return ("medium","medium:keywords")
    if hit(EASY_HINTS):   return ("easy",  "easy:keywords")
    if len(t) > 40:       return ("medium","length>40")
    return ("easy","default")

def mod_first_time(task: str) -> float:
    return 1.2 if any(h in task for h in FIRST_TIME_HINTS) else 1.0

def mod_platforms(task: str) -> float:
    t = norm(task)
    hits = sum(1 for p in PLATFORMS if p in t)
    return 1.0 + 0.1 * max(0, hits - 1)

def detect_qa(task: str):
    t = norm(task)
    for name, (kws, case_min, arts) in QA_TYPES.items():
        if any(k in t for k in kws):
            return {"type": name, "case_minutes": case_min, "artifacts": arts}
    return None

def qa_modifiers(task: str) -> Dict[str, float]:
    t = task.lower()
    m: Dict[str, float] = {}
    if any(k in t for k in QA_FLAKY_HINTS): m["flaky"] = 1.2
    if any(k in t for k in QA_DATA_HINTS):  m["test_data"] = 1.1
    if any(k in t for k in QA_ENV_HINTS):   m["env_setup"] = 1.15
    return m

def qa_case_estimate(qa_type: str, text: str) -> int:
    base = {"qa_unit": 6, "qa_integration": 4, "qa_perf": 2, "qa_security": 2, "qa_a11y": 3, "qa_lighthouse": 1}.get(qa_type, 0)
    if any(k in text for k in ["境界", "edge", "異常", "例外"]): base += 2
    if len(text) > 60: base += 1
    return max(base, 0)

def split_tasks(text: str) -> List[str]:
    sep = r"[;\n\r・/]|。|、|，|；| and | および "
    parts = [p.strip(" -—\t") for p in re.split(sep, text) if p.strip()]
    finer: List[str] = []
    for p in parts:
        finer += [q.strip() for q in re.split(r"(?:して|してから|および|かつ)", p) if q.strip()]
    return [t for t in finer if t]

@dataclass
class Est:
    task: str
    difficulty: str
    difficulty_reason: str
    domain: str
    domain_reason: str
    base_hours: float
    multiplier: float
    modifiers: Dict[str, float]
    core_hours: float      # profile後, buffer前
    qa_hours: float        # profile後, buffer前
    shown_hours: float     # 表示用（--buffer-per-taskならbuffer込み）
    qa: Optional[Dict]

def estimate(
    text: str,
    profile: str = "general",
    with_qa: bool = False,
    qa_include: bool = False,
    buffer: float = 1.0,
    qa_buffer: Optional[float] = None,
    buffer_per_task: bool = False,
) -> Dict:
    tasks = split_tasks(text)
    rows: List[Est] = []
    prof_mult = {"general": 1.0, "conservative": 1.3, "fast": 0.7}.get(profile, 1.0)
    qa_buf = qa_buffer if qa_buffer is not None else buffer

    for t in tasks:
        diff, dreason = guess_difficulty(t)
        base = BASE_HOURS[diff]
        domain, mult, mreason = guess_domain(t)
        mods = {"first_time": mod_first_time(t), "platforms": mod_platforms(t)}
        core_base = base * mult * mods["first_time"] * mods["platforms"]
        core_est = core_base * prof_mult

        qa_info = None
        qa_est = 0.0
        if with_qa:
            det = detect_qa(t)
            if det:
                qmods = qa_modifiers(t)
                cases = qa_case_estimate(det["type"], t)
                case_hours = cases * (det["case_minutes"] / 60.0)
                qa_info = {
                    "type": det["type"],
                    "artifacts": det["artifacts"],
                    "case_minutes": det["case_minutes"],
                    "modifiers": qmods,
                    "cases_estimate": cases,
                    "case_hours": round(case_hours * prof_mult, 2),
                }
                qa_est = case_hours * prof_mult

        shown = core_est + (qa_est if qa_include else 0.0)
        if buffer_per_task:
            shown *= buffer

        rows.append(
            Est(
                task=t,
                difficulty=diff,
                difficulty_reason=dreason,
                domain=domain,
                domain_reason=mreason,
                base_hours=base,
                multiplier=mult,
                modifiers=mods,
                core_hours=round(core_est, 2),
                qa_hours=round(qa_est, 2),
                shown_hours=round(shown, 2),
                qa=qa_info,
            )
        )

    core_sum = sum(r.core_hours for r in rows) * buffer
    qa_sum = (sum(r.qa_hours for r in rows) if with_qa else 0.0) * qa_buf
    grand = core_sum + (qa_sum if qa_include else 0.0)

    return {
        "input": text,
        "profile": profile,
        "with_qa": with_qa,
        "qa_included_in_total": qa_include,
        "buffers": {"core_buffer": buffer, "qa_buffer": qa_buf, "buffer_per_task": buffer_per_task},
        "items": [asdict(r) for r in rows],
        "totals": {
            "core_hours": round(core_sum, 2),
            "qa_hours": round(qa_sum, 2),
            "grand_total_hours": round(grand, 2),
        },
    }

def fmt_md(res: Dict) -> str:
    out = []
    out.append(f"**原文**：{res['input']}")
    out.append("")
    buf = res["buffers"]
    buf_note = f"Buffer(core)×{buf['core_buffer']:.2f}"
    if res.get("with_qa"):
        buf_note += f", Buffer(QA)×{buf['qa_buffer']:.2f}"
    if buf["buffer_per_task"]:
        buf_note += "（タスク行にも適用）"
    else:
        buf_note += "（タスク行は素の値、総計のみ適用）"
    out.append(f"*{buf_note}*")
    out.append("")
    out.append("| タスク | 難易度 | 領域/根拠 | 見積(時間) |")
    out.append("|---|---|---|---:|")
    for it in res["items"]:
        dom = f"{it['domain']} ({it['domain_reason']})"
        out.append(f"| {it['task']} | {it['difficulty']} | {dom} | **{it['shown_hours']:.1f}h** |")
    out.append("")
    if res.get("with_qa"):
        out.append("**QA補助（検出時のみ）**")
        out.append("")
        out.append("| タスク | QA種別 | 推奨成果物 | 想定ケース数 | QA見積(時間, バッファ後) |")
        out.append("|---|---|---|---:|---:|")
        for it in res["items"]:
            qa = it.get("qa")
            if not qa: continue
            arts = " / ".join(qa["artifacts"])
            qa_after_buf = qa["case_hours"] * res["buffers"]["qa_buffer"]
            out.append(f"| {it['task']} | {qa['type']} | {arts} | {qa['cases_estimate']} | {qa_after_buf:.1f}h |")
        out.append("")
    totals = res["totals"]
    line = f"**積算（{res['profile']}）**：Core **{totals['core_hours']:.1f}h**"
    if res.get("with_qa"):
        line += f" + QA **{totals['qa_hours']:.1f}h**"
        if res["qa_included_in_total"]:
            line += f" = **{totals['grand_total_hours']:.1f}h**"
    out.append(line)
    return "\n".join(out)

def main() -> None:
    ap = argparse.ArgumentParser(description="taskest – Task decomposition & estimation CLI")
    ap.add_argument("text", help="見積り対象の文章（引用符で囲む）")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--profile", choices=["general", "conservative", "fast"], default="general")
    ap.add_argument("--qa", action="store_true", help="QA補助情報を出力する（ケース数/成果物/QA時間）")
    ap.add_argument("--qa-include", action="store_true", help="総計にQA時間を加算する")
    ap.add_argument("--buffer", type=float, default=1.0, help="安全係数（コア作業）。例: 1.2 = +20%")
    ap.add_argument("--qa-buffer", type=float, default=None, help="QA専用の安全係数。未指定なら --buffer を使用")
    ap.add_argument("--buffer-per-task", action="store_true", help="タスク行の時間にもバッファを反映（既定は総計のみ）")
    args = ap.parse_args()

    res = estimate(
        args.text,
        profile=args.profile,
        with_qa=args.qa,
        qa_include=args.qa_include,
        buffer=args.buffer,
        qa_buffer=args.qa_buffer,
        buffer_per_task=args.buffer_per_task,
    )
    if args.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(fmt_md(res))

if __name__ == "__main__":
    main()
