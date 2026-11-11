"""Metric DSL parser.

Grammar (single line, case-insensitive keywords):

    metric <key> = <agg>[(distinct <measure>)] from <table>
        [where <cond> [and <cond>]...]
        [filter <field> in (<v1>,<v2>,...)]...
        [grain hour|day|week|month]
        [window <n>d|<n>w|<n>h|all]
        [using (<metric_key>,...)]

The parser returns a five-tuple ``(agg, measure, filters, window, grain)`` used by
the conflict detector, plus token spans (byte offsets into the original text) used
by the DSL editor to highlight the source, plus a dependency preview parsed from
``using (...)``. ``where date >= today-N`` also derives a window when the explicit
``window`` clause is absent.

Failure states:
  * syntax   — bad prefix / missing from / duplicate clause / trailing junk / bad values
  * semantic — unknown aggregation, invalid grain, self dependency, empty filter set
"""
from __future__ import annotations

import re
from typing import Any

from app.constants.error_codes import AppError, ErrorCode

ALLOWED_AGG = {"count", "sum", "avg", "min", "max"}
ALLOWED_GRAIN = ("hour", "day", "week", "month")
CLAUSE_NAMES = ("from", "where", "filter", "grain", "window", "using")
CLAUSE_RE = re.compile(r"\b(" + "|".join(CLAUSE_NAMES) + r")\b", re.I)
PREFIX_RE = re.compile(r"^\s*metric\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*", re.I)
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
AGG_RE = re.compile(r"^([A-Za-z_]+)\s*(?:\(\s*(distinct\s+)?([^()]*?)\s*\))?$", re.I)
TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
DATE_WINDOW_RE = re.compile(
    r"^(date|dt|ds|event_date|stat_date|day)\s*>=\s*today\s*-\s*(\d+)$", re.I
)
WINDOW_VALUE_RE = re.compile(r"^(\d+)\s*(d|day|days|w|week|weeks|h|hour|hours)?$", re.I)
FILTER_IN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*)\s+in\s*\((.+)\)$", re.I)
USING_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
COMPARISON_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*(=|!=|<>|>=|<=|>|<)\s*(.+)$")


# --------------------------------------------------------------------------- helpers
def _mask_quotes(text: str) -> str:
    """Same-length copy with quoted literals blanked, so keywords inside values
    ([...] 'and' 'from') never confuse clause detection."""
    out = list(text)
    quote: str | None = None
    for i, ch in enumerate(text):
        if quote:
            out[i] = " "
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out[i] = " "
    return "".join(out)


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_condition(condition: str) -> str:
    raw = _collapse(condition)
    in_match = FILTER_IN_RE.match(raw)
    if in_match:
        field = in_match.group(1).lower()
        values = sorted({_strip_quotes(v) for v in in_match.group(2).split(",") if v.strip()})
        return f"{field} in ({','.join(values)})"
    cmp_match = COMPARISON_RE.match(raw)
    if cmp_match:
        field = cmp_match.group(1).lower()
        op = cmp_match.group(2)
        value = _strip_quotes(cmp_match.group(3))
        return f"{field} {op} {value}"
    return raw


def _normalize_window(number: str, unit: str | None) -> str:
    n = int(number)
    u = (unit or "d").lower()
    if u in ("d", "day", "days"):
        return f"{n}d"
    if u in ("w", "week", "weeks"):
        return f"{n}w"
    return f"{n}h"


def _empty_result(text: str) -> dict[str, Any]:
    return {
        "ok": False,
        "metric_key": None,
        "agg": None,
        "measure": None,
        "distinct": False,
        "source_table": None,
        "filters": [],
        "window": None,
        "grain": None,
        "tuple": None,
        "dependencies": [],
        "tokens": [],
        "warnings": [],
        "error": None,
        "error_kind": None,
        "error_offset": 0,
        "source_text": text,
    }


def _error(result: dict[str, Any], message: str, offset: int, kind: str = "syntax") -> dict[str, Any]:
    result["ok"] = False
    result["error"] = message
    result["error_kind"] = kind
    result["error_offset"] = max(0, int(offset))
    return result


def _split_conditions(segment: str, masked: str, start: int) -> list[tuple[str, int]]:
    """Split a where-segment on top-level ``and`` words, keeping absolute offsets."""
    pieces: list[tuple[str, int]] = []
    last = 0
    for match in re.finditer(r"\band\b", masked, re.I):
        pieces.append((segment[last : match.start()], start + last))
        last = match.end()
    pieces.append((segment[last:], start + last))
    return [(piece, offset) for piece, offset in pieces if piece.strip()]


# --------------------------------------------------------------------------- parser
def parse_dsl(text: str) -> dict[str, Any]:
    result = _empty_result(text or "")
    if not text or not text.strip():
        return _error(result, "DSL 不能为空", 0)

    raw = text
    masked = _mask_quotes(raw)
    prefix = PREFIX_RE.match(masked)
    if not prefix:
        return _error(result, "DSL 必须以 `metric <key> =` 开头", 0)

    metric_key = prefix.group(1)
    result["metric_key"] = metric_key
    if not KEY_RE.match(metric_key):
        return _error(result, f"指标 key `{metric_key}` 不符合 ^[a-z][a-z0-9_]{{1,63}}$", prefix.start(1), "semantic")

    body_start = prefix.end()
    body = raw[body_start:]
    body_masked = masked[body_start:]

    clauses = [(m.group(1).lower(), m.start(), m.end()) for m in CLAUSE_RE.finditer(body_masked)]
    if not clauses:
        return _error(result, "缺少 from 子句", body_start)
    if clauses[0][0] != "from":
        return _error(result, "聚合表达式之后必须先出现 from 子句", body_start + clauses[0][1])

    seen: dict[str, int] = {}
    for name, start, _end in clauses:
        if name == "filter":
            continue
        if name in seen:
            return _error(result, f"`{name}` 子句重复出现", body_start + start)
        seen[name] = start

    # ---- aggregation expression
    expr_segment = body[0 : clauses[0][1]]
    expr_text = expr_segment.strip()
    expr_offset = body_start + (len(expr_segment) - len(expr_segment.lstrip()))
    agg_match = AGG_RE.match(expr_text)
    if not agg_match:
        return _error(result, "无法解析聚合表达式，期望形如 `count(distinct user_id)`", expr_offset)
    agg = agg_match.group(1).lower()
    distinct = bool(agg_match.group(2))
    measure = (agg_match.group(3) or "").strip()
    if agg not in ALLOWED_AGG:
        return _error(
            result,
            f"不支持的聚合函数 `{agg}`，可用：{'/'.join(sorted(ALLOWED_AGG))}",
            expr_offset,
            "semantic",
        )
    if not measure:
        measure = "*"
    if distinct and agg != "count":
        return _error(result, "distinct 只能与 count 一起使用", expr_offset, "semantic")
    canonical_agg = "count_distinct" if (agg == "count" and distinct) else agg
    result["agg"] = canonical_agg
    result["measure"] = measure
    result["distinct"] = distinct

    tokens: list[dict[str, Any]] = [
        {"start": prefix.start(1), "end": prefix.end(1), "kind": "metric"},
        {"start": expr_offset, "end": expr_offset + len(expr_text), "kind": "agg"},
    ]
    measure_local = expr_segment.find(measure) if measure != "*" else -1
    if measure_local >= 0:
        tokens.append(
            {"start": body_start + measure_local, "end": body_start + measure_local + len(measure), "kind": "measure"}
        )

    # ---- clause segments
    for index, (name, _start, end) in enumerate(clauses):
        next_start = clauses[index + 1][1] if index + 1 < len(clauses) else len(body)
        segment = body[end:next_start]
        segment_masked = body_masked[end:next_start]
        seg_offset = body_start + end
        stripped = segment.strip()
        local_offset = end + (len(segment) - len(segment.lstrip()))

        if name == "from":
            if not TABLE_RE.match(stripped):
                return _error(result, "from 子句只接受单个物理表名", body_start + local_offset)
            result["source_table"] = stripped
            find_at = body.find(stripped, end, next_start)
            tokens.append({"start": body_start + find_at, "end": body_start + find_at + len(stripped), "kind": "table"})

        elif name == "where":
            if not stripped:
                return _error(result, "where 子句为空", body_start + local_offset)
            pieces = _split_conditions(segment, segment_masked, seg_offset)
            if not pieces:
                return _error(result, "where 子句为空", body_start + local_offset)
            for piece, piece_offset in pieces:
                condition = _normalize_condition(piece)
                date_match = DATE_WINDOW_RE.match(condition)
                if date_match:
                    days = int(date_match.group(2))
                    if days <= 0 or days > 3650:
                        return _error(
                            result, "where 中的 today-N 窗口必须在 1..3650 天之间", piece_offset, "semantic"
                        )
                    result["warnings"].append(f"从 where 推导出窗口 {days}d")
                    result.setdefault("_derived_window", f"{days}d")
                    result["_derived_window"] = f"{days}d"
                    continue
                result["filters"].append(condition)
                find_at = body.find(piece.strip(), end, next_start)
                tokens.append(
                    {
                        "start": body_start + max(find_at, 0),
                        "end": body_start + max(find_at, 0) + len(piece.strip()),
                        "kind": "filter",
                    }
                )

        elif name == "filter":
            filter_match = FILTER_IN_RE.match(stripped)
            if not filter_match:
                return _error(
                    result, "filter 子句格式应为 `filter <field> in (v1,v2)`", body_start + local_offset
                )
            field = filter_match.group(1).lower()
            values = sorted({_strip_quotes(v) for v in filter_match.group(2).split(",") if v.strip()})
            if not values:
                return _error(result, "filter 的取值集合不能为空", body_start + local_offset, "semantic")
            result["filters"].append(f"{field} in ({','.join(values)})")
            tokens.append(
                {"start": body_start + local_offset, "end": body_start + local_offset + len(stripped), "kind": "filter"}
            )

        elif name == "grain":
            value = stripped.lower()
            if value not in ALLOWED_GRAIN:
                return _error(
                    result, f"grain 只支持 {'/'.join(ALLOWED_GRAIN)}，收到 `{value}`", body_start + local_offset, "semantic"
                )
            result["grain"] = value
            tokens.append(
                {"start": body_start + local_offset, "end": body_start + local_offset + len(value), "kind": "grain"}
            )

        elif name == "window":
            value = stripped.lower()
            if value in ("all", "none", "full"):
                result["window"] = "all"
            else:
                window_match = WINDOW_VALUE_RE.match(value)
                if not window_match:
                    return _error(
                        result, "window 子句格式应为 `<n>d|<n>w|<n>h|all`", body_start + local_offset
                    )
                number = int(window_match.group(1))
                if number <= 0 or number > 3650:
                    return _error(result, "window 数值必须在 1..3650 之间", body_start + local_offset, "semantic")
                result["window"] = _normalize_window(window_match.group(1), window_match.group(2))
            tokens.append(
                {"start": body_start + local_offset, "end": body_start + local_offset + len(stripped), "kind": "window"}
            )

        elif name == "using":
            inner = stripped
            if inner.startswith("(") and inner.endswith(")"):
                inner = inner[1:-1]
            names = [_strip_quotes(name.strip()) for name in inner.split(",") if name.strip()]
            if not names:
                return _error(result, "using 子句至少需要一个指标 key", body_start + local_offset)
            bad = [name for name in names if not USING_NAME_RE.match(name)]
            if bad:
                return _error(result, f"using 中出现非法指标 key：{','.join(bad)}", body_start + local_offset, "semantic")
            if metric_key in names:
                return _error(result, "指标不能依赖自身", body_start + local_offset, "semantic")
            result["dependencies"] = sorted(set(names))
            tokens.append(
                {"start": body_start + local_offset, "end": body_start + local_offset + len(stripped), "kind": "using"}
            )

    if result["grain"] is None:
        return _error(result, "缺少 grain 子句（hour/day/week/month）", body_start, "semantic")

    if result["window"] is None:
        result["window"] = result.pop("_derived_window", "all")
    else:
        result.pop("_derived_window", None)

    # de-duplicate filters and keep a stable order for the five-tuple comparison
    result["filters"] = sorted(set(result["filters"]))

    # ---- token hygiene: sorted, non-overlapping spans only
    tokens.sort(key=lambda token: (token["start"], -(token["end"] - token["start"])))
    clean: list[dict[str, Any]] = []
    last_end = -1
    for token in tokens:
        if token["start"] < last_end or token["end"] <= token["start"]:
            continue
        clean.append(token)
        last_end = token["end"]
    result["tokens"] = clean

    result["tuple"] = {
        "agg": result["agg"],
        "measure": result["measure"],
        "filters": result["filters"],
        "window": result["window"],
        "grain": result["grain"],
    }
    result["ok"] = True
    return result


def parse_or_raise(text: str) -> dict[str, Any]:
    """Parser wrapper used by write paths: invalid DSL becomes a typed AppError."""
    parsed = parse_dsl(text)
    if parsed["ok"]:
        return parsed
    code = ErrorCode.DSL_SEMANTIC if parsed["error_kind"] == "semantic" else ErrorCode.DSL_SYNTAX
    raise AppError(
        code,
        message=parsed["error"],
        detail={"offset": parsed["error_offset"], "kind": parsed["error_kind"]},
    )
