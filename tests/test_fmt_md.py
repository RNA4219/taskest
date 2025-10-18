import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taskest import estimate, fmt_md


def test_fmt_md_table_structure() -> None:
    res = estimate(
        "UIを調整;APIの統合テストを整備",
        with_qa=True,
        qa_include=True,
        buffer=1.1,
        qa_buffer=1.2,
        buffer_per_task=False,
    )

    output = fmt_md(res)
    lines = output.splitlines()

    header = "| # | タスク | 難易度/根拠 | 領域/根拠 | コアh | QA h | 表示 |"
    assert header in lines

    header_index = lines.index(header)
    assert lines[header_index + 1] == "|---|---|---|---|---:|---:|---:|"

    first_row = lines[header_index + 2]
    second_row = lines[header_index + 3]

    assert first_row.startswith("| 1 | UIを調整")
    assert "medium (medium:keywords)" in first_row
    assert "frontend" in first_row
    assert first_row.endswith("| 0.0h | 0.0h | 0.0h |") is False

    assert second_row.startswith("| 2 | APIの統合テストを整備")
    assert "backend" in second_row

    qa_header = "| タスク | QA種別 | 推奨成果物 | 想定ケース数 | QA見積(時間, バッファ後) |"
    assert qa_header in lines

    totals_line = next(line for line in lines if line.startswith("**積算"))
    assert "Core" in totals_line
    assert "QA" in totals_line
