"""CSV rendering for the impact-sheet download (UTF-8 BOM so Excel opens it)."""
import csv
import io
from typing import Any

BOM = "\ufeff"

HEADER = [
    "批次号",
    "指标key",
    "指标名称",
    "冲突类型",
    "严重度",
    "版本A",
    "版本B",
    "差异维度",
    "受影响指标数",
    "受影响指标",
    "受影响看板",
    "冲突说明",
]


def render_impact_csv(batch_no: str, rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    buffer.write(BOM)
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HEADER)
    for row in rows:
        impact = row.get("impact") or {}
        writer.writerow(
            [
                batch_no,
                row.get("metric_key", ""),
                row.get("metric_name", ""),
                row.get("conflict_type", ""),
                row.get("severity", ""),
                f"v{row.get('version_a_no', '')}",
                f"v{row.get('version_b_no', '')}",
                "/".join(row.get("dimensions") or []),
                impact.get("affected_metric_count", 0),
                "; ".join(metric.get("key", "") for metric in impact.get("affected_metrics", [])),
                "; ".join(impact.get("boards", [])),
                row.get("detail", ""),
            ]
        )
    return buffer.getvalue()
