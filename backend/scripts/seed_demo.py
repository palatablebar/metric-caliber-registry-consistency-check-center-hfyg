"""Idempotent demo seed for 微光课堂 · 指标口径注册与一致性检查中心.

Scene: 4 domain teams registered 14 metrics; the same-named metric
``active_users`` was re-implemented by 3 teams with 3 different caliber tuples;
two dependency cycles were introduced by copy-pasted DSL; the governance
committee ran one consistency batch with 3 high conflicts.

Idempotency contract:
  * teams   upsert by ``code``
  * users   upsert by ``email`` (an existing password is never overwritten)
  * metrics upsert by ``metric_key``
  * versions upsert by ``(metric_id, version_no)``
  * table dependencies upsert by ``(from_metric_id, to_table)``
  * the check batch upsert by fixed ``batch_no`` and is re-executed only while
    it is not completed
Ends with exactly one ``SEED_SUMMARY {json}`` line; running twice prints the
same numbers (the Lead uses this line to verify idempotency).

Passwords: admin@metric.local / owner@metric.local / analyst@metric.local — Demo@2026
"""
from __future__ import annotations

import json
import random
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.database import SessionLocal, init_db
from app.constants.domains import Domain
from app.constants.metric_status import MetricStatus
from app.constants.messages import DEMO_PASSWORD, SEED_CHECK_BATCH
from app.models import (
    ConflictFinding,
    ConsistencyCheck,
    MetricDefinition,
    MetricDependency,
    MetricVersion,
    OwnerTeam,
    User,
)
from app.schemas.metric import VersionCreate
from app.services import auth_service, version_service
from app.services.check_service import execute_check
from app.utils.logger import log_event

RANDOM_SEED = 20261110
random.seed(RANDOM_SEED)

TEAMS = [
    {
        "code": "growth",
        "name": "增长实验组",
        "domain": Domain.GROWTH.value,
        "lead_name": "林知夏",
        "member_count": 6,
        "sla_hours": 12,
    },
    {
        "code": "trade",
        "name": "交易指标组",
        "domain": Domain.TRADE.value,
        "lead_name": "陈砚",
        "member_count": 5,
        "sla_hours": 8,
    },
    {
        "code": "content",
        "name": "内容质量组",
        "domain": Domain.CONTENT.value,
        "lead_name": "周自成",
        "member_count": 4,
        "sla_hours": 24,
    },
    {
        "code": "experience",
        "name": "体验度量组",
        "domain": Domain.EXPERIENCE.value,
        "lead_name": "徐清",
        "member_count": 3,
        "sla_hours": 24,
    },
]

ACCOUNTS = [
    {
        "email": "admin@metric.local",
        "display_name": "顾清和",
        "role": "admin",
        "team_code": None,
        "quota": 40,
    },
    {
        "email": "owner@metric.local",
        "display_name": "林知夏",
        "role": "owner",
        "team_code": "growth",
        "quota": 30,
    },
    {
        "email": "analyst@metric.local",
        "display_name": "沈知微",
        "role": "analyst",
        "team_code": None,
        "quota": 10,
    },
]

METRICS = [
    {
        "key": "active_users",
        "name": "活跃用户",
        "domain": Domain.GROWTH.value,
        "team_code": "growth",
        "status": MetricStatus.ACTIVE.value,
        "description": "统计周期内发生过有效访问的去重用户数；三个团队各有一版口径，是本季度口径治理的头号议题。",
        "consumers": ["增长周报看板", "AB-2026Q4-留存实验"],
    },
    {
        "key": "new_signups",
        "name": "新增注册",
        "domain": Domain.GROWTH.value,
        "team_code": "growth",
        "status": MetricStatus.ACTIVE.value,
        "description": "自然日内完成注册且未注销的去重用户数。",
        "consumers": ["增长周报看板"],
    },
    {
        "key": "retention_d7",
        "name": "7 日留存率",
        "domain": Domain.GROWTH.value,
        "team_code": "growth",
        "status": MetricStatus.ACTIVE.value,
        "description": "注册后第 7 日仍有访问行为的用户占注册用户比例。",
        "consumers": ["留存实验看板"],
    },
    {
        "key": "visit_pv",
        "name": "访问次数",
        "domain": Domain.GROWTH.value,
        "team_code": "growth",
        "status": MetricStatus.DRAFT.value,
        "description": "埋点上报的页面访问 PV 汇总，草稿态等待与增长组确认去重口径。",
        "consumers": ["流量日报"],
    },
    {
        "key": "gmv",
        "name": "成交总额",
        "domain": Domain.TRADE.value,
        "team_code": "trade",
        "status": MetricStatus.ACTIVE.value,
        "description": "已支付订单金额合计，与财务收入月报口径对齐。",
        "consumers": ["交易大盘", "财务收入月报"],
    },
    {
        "key": "order_count",
        "name": "订单数",
        "domain": Domain.TRADE.value,
        "team_code": "trade",
        "status": MetricStatus.ACTIVE.value,
        "description": "支付成功订单数量。",
        "consumers": ["交易大盘"],
    },
    {
        "key": "refund_rate",
        "name": "退款率",
        "domain": Domain.TRADE.value,
        "team_code": "trade",
        "status": MetricStatus.ACTIVE.value,
        "description": "退款订单数占支付订单数比例。",
        "consumers": ["售后监控看板"],
    },
    {
        "key": "arpu",
        "name": "客单价",
        "domain": Domain.TRADE.value,
        "team_code": "trade",
        "status": MetricStatus.ACTIVE.value,
        "description": "成交总额除以订单数，用于收入结构分析。",
        "consumers": ["财务收入月报"],
    },
    {
        "key": "course_completion_rate",
        "name": "课程完课率",
        "domain": Domain.CONTENT.value,
        "team_code": "content",
        "status": MetricStatus.ACTIVE.value,
        "description": "完成全部章节学习的用户占开课用户比例。",
        "consumers": ["内容质量看板"],
    },
    {
        "key": "watch_minutes",
        "name": "观看时长",
        "domain": Domain.CONTENT.value,
        "team_code": "content",
        "status": MetricStatus.ACTIVE.value,
        "description": "学习行为产生的有效观看时长（分钟）。",
        "consumers": ["内容质量看板"],
    },
    {
        "key": "content_ctr",
        "name": "内容点击率",
        "domain": Domain.CONTENT.value,
        "team_code": "content",
        "status": MetricStatus.DRAFT.value,
        "description": "推荐位曝光转点击的比例，草稿态等待推荐团队确认曝光口径。",
        "consumers": ["内容推荐日报"],
    },
    {
        "key": "crash_rate",
        "name": "崩溃率",
        "domain": Domain.EXPERIENCE.value,
        "team_code": "experience",
        "status": MetricStatus.ACTIVE.value,
        "description": "发生崩溃的会话占总会话比例；当前没有任何看板或指标消费。",
        "consumers": [],
    },
    {
        "key": "avg_session_seconds",
        "name": "平均会话时长",
        "domain": Domain.EXPERIENCE.value,
        "team_code": "experience",
        "status": MetricStatus.ACTIVE.value,
        "description": "单次会话平均时长（秒）。",
        "consumers": ["体验周报"],
    },
    {
        "key": "nps_score",
        "name": "NPS 净推荐值",
        "domain": Domain.EXPERIENCE.value,
        "team_code": "experience",
        "status": MetricStatus.DRAFT.value,
        "description": "季度调研推荐者减贬损者比例；草稿态，尚未接入看板。",
        "consumers": [],
    },
]

# key -> ordered version rows. Same-named metric versions from different teams is
# the whole point of the conflict detector.
VERSIONS: dict[str, list[dict]] = {
    "active_users": [
        {
            "team_code": "growth",
            "dsl": "metric active_users = count(distinct user_id) from fact_visit "
            "where date >= today-7 filter platform in ('ios','android') grain day",
        },
        {
            "team_code": "content",
            "dsl": "metric active_users = count(distinct user_id) from fact_visit "
            "where date >= today-7 filter platform in ('ios','android','web') grain day",
        },
        {
            "team_code": "experience",
            "dsl": "metric active_users = count(distinct device_id) from fact_visit "
            "where date >= today-7 filter platform in ('ios','android') grain week",
        },
    ],
    "new_signups": [
        {"team_code": "growth", "dsl": "metric new_signups = count(distinct user_id) from fact_register where date >= today-1 grain day"}
    ],
    "retention_d7": [
        {
            "team_code": "growth",
            "dsl": "metric retention_d7 = avg(retain_flag) from fact_retention where date >= today-30 "
            "grain week using (active_users, new_signups)",
        },
        {
            "team_code": "growth",
            "dsl": "metric retention_d7 = avg(is_retained) from fact_retention where date >= today-30 "
            "grain week using (active_users, new_signups)",
        },
    ],
    "visit_pv": [
        {
            "team_code": "growth",
            "dsl": "metric visit_pv = sum(pv_count) from fact_visit where date >= today-1 grain day using (active_users)",
        }
    ],
    "gmv": [
        {
            "team_code": "trade",
            "dsl": "metric gmv = sum(pay_amount) from fact_order where order_status = 'paid' grain day "
            "window 30d using (order_count, arpu)",
        },
        {
            "team_code": "trade",
            "dsl": "metric gmv = sum(pay_amount) from fact_order where order_status = 'paid' grain day "
            "window 7d using (order_count, arpu)",
        },
    ],
    "order_count": [
        {
            "team_code": "trade",
            "dsl": "metric order_count = count(order_id) from fact_order where order_status = 'paid' grain day using (active_users)",
        }
    ],
    "refund_rate": [
        {
            "team_code": "trade",
            "dsl": "metric refund_rate = avg(refund_flag) from fact_order where order_status in ('paid','refunded') "
            "grain day using (order_count, gmv)",
        }
    ],
    "arpu": [
        {
            "team_code": "trade",
            "dsl": "metric arpu = sum(pay_amount) from fact_order where order_status = 'paid' grain day using (gmv, order_count)",
        }
    ],
    "course_completion_rate": [
        {
            "team_code": "content",
            "dsl": "metric course_completion_rate = avg(completion_flag) from fact_learning grain day using (watch_minutes)",
        }
    ],
    "watch_minutes": [
        {
            "team_code": "content",
            "dsl": "metric watch_minutes = sum(watch_seconds) from fact_learning grain day using (content_ctr)",
        }
    ],
    "content_ctr": [
        {
            "team_code": "content",
            "dsl": "metric content_ctr = avg(click_flag) from fact_recommend grain day using (course_completion_rate)",
        }
    ],
    "crash_rate": [
        {"team_code": "experience", "dsl": "metric crash_rate = avg(crash_flag) from fact_crash grain day"}
    ],
    "avg_session_seconds": [
        {
            "team_code": "experience",
            "dsl": "metric avg_session_seconds = avg(session_seconds) from fact_session grain day using (active_users)",
        }
    ],
    "nps_score": [
        {"team_code": "experience", "dsl": "metric nps_score = avg(score) from fact_survey grain month"}
    ],
}

TABLE_DEPENDENCIES = [
    ("active_users", "fact_visit"),
    ("gmv", "fact_order"),
    ("crash_rate", "fact_crash"),
    ("nps_score", "fact_survey"),
]


# --------------------------------------------------------------------------- helpers
def _ensure_team(db: Session, spec: dict) -> OwnerTeam:
    team = db.scalar(select(OwnerTeam).where(OwnerTeam.code == spec["code"]))
    if team is None:
        team = OwnerTeam(**spec)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    team.name = spec["name"]
    team.domain = spec["domain"]
    team.lead_name = spec["lead_name"]
    team.member_count = spec["member_count"]
    team.sla_hours = spec["sla_hours"]
    db.commit()
    return team


def _ensure_metric(db: Session, spec: dict, team: OwnerTeam) -> MetricDefinition:
    metric = db.scalar(select(MetricDefinition).where(MetricDefinition.metric_key == spec["key"]))
    if metric is None:
        metric = MetricDefinition(
            metric_key=spec["key"],
            display_name=spec["name"],
            domain=spec["domain"],
            owner_team_id=team.id,
            status=spec["status"],
            description=spec["description"],
            consumers_json=spec["consumers"],
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric
    metric.display_name = spec["name"]
    metric.domain = spec["domain"]
    metric.owner_team_id = team.id
    metric.status = spec["status"]
    metric.description = spec["description"]
    metric.consumers_json = spec["consumers"]
    db.commit()
    return metric


def _ensure_versions(db: Session, metric: MetricDefinition, spec: list[dict], teams: dict[str, OwnerTeam], admin: User) -> int:
    created = 0
    for index, row in enumerate(spec, start=1):
        existing = db.scalar(
            select(MetricVersion).where(
                MetricVersion.metric_id == metric.id,
                MetricVersion.version_no == index,
            )
        )
        if existing is not None:
            continue
        version_service.create_version(
            db,
            admin,
            metric.id,
            VersionCreate(
                dsl_text=row["dsl"],
                team_id=teams[row["team_code"]].id,
                effective_from=date.today().isoformat(),
                set_current=True,
            ),
        )
        created += 1
    return created


def _ensure_table_dependency(db: Session, metric: MetricDefinition, table: str) -> None:
    exists = db.scalar(
        select(MetricDependency).where(
            MetricDependency.from_metric_id == metric.id,
            MetricDependency.to_table == table,
        )
    )
    if exists is not None:
        return
    db.add(
        MetricDependency(
            from_metric_id=metric.id,
            to_table=table,
            relation="source",
            note="物理表依赖（人工登记）",
        )
    )
    db.commit()


def _ensure_check_batch(db: Session) -> int:
    check = db.scalar(select(ConsistencyCheck).where(ConsistencyCheck.batch_no == SEED_CHECK_BATCH))
    if check is None:
        check = ConsistencyCheck(
            batch_no=SEED_CHECK_BATCH,
            scope="all",
            status="pending",
            triggered_by="seed_demo",
            summary_json={},
        )
        db.add(check)
        db.commit()
        db.refresh(check)
    if check.status != "completed":
        execute_check(check.id)
    return check.id


def _counts(db: Session) -> dict[str, int]:
    return {
        "owner_team": int(db.scalar(select(func.count(OwnerTeam.id))) or 0),
        "user": int(db.scalar(select(func.count(User.id))) or 0),
        "metric_definition": int(db.scalar(select(func.count(MetricDefinition.id))) or 0),
        "metric_version": int(db.scalar(select(func.count(MetricVersion.id))) or 0),
        "metric_dependency": int(db.scalar(select(func.count(MetricDependency.id))) or 0),
        "consistency_check": int(db.scalar(select(func.count(ConsistencyCheck.id))) or 0),
        "conflict_finding": int(db.scalar(select(func.count(ConflictFinding.id))) or 0),
    }


# --------------------------------------------------------------------------- entry
def run_seed() -> dict:
    init_db()
    db = SessionLocal()
    try:
        teams = {spec["code"]: _ensure_team(db, spec) for spec in TEAMS}
        for spec in ACCOUNTS:
            team_id = teams[spec["team_code"]].id if spec.get("team_code") else None
            auth_service.ensure_demo_user(
                db,
                email=spec["email"],
                display_name=spec["display_name"],
                role=spec["role"],
                password=DEMO_PASSWORD,
                team_id=team_id,
            )
        admin = auth_service.get_user_by_email(db, "admin@metric.local")
        assert admin is not None

        # phase 1: all metric definitions first — `using (...)` may reference a
        # metric defined later in the list, so versions cannot be written before
        # the whole catalog exists.
        metrics: dict[str, MetricDefinition] = {}
        for spec in METRICS:
            metrics[spec["key"]] = _ensure_metric(db, spec, teams[spec["team_code"]])

        # phase 2: ordered versions (idempotent by metric_id + version_no)
        version_created = 0
        for spec in METRICS:
            version_created += _ensure_versions(db, metrics[spec["key"]], VERSIONS[spec["key"]], teams, admin)

        for metric_key, table in TABLE_DEPENDENCIES:
            _ensure_table_dependency(db, metrics[metric_key], table)

        _ensure_check_batch(db)
        # execute_check commits in its own session; end this session's read
        # transaction so MySQL REPEATABLE READ sees the freshly persisted findings
        db.commit()
        counts = _counts(db)
        log_event(
            "SEED_DEMO_FINISHED",
            teams=counts["owner_team"],
            metrics=counts["metric_definition"],
            versions=counts["metric_version"],
            check=SEED_CHECK_BATCH,
        )
        print("SEED_SUMMARY " + json.dumps(counts, ensure_ascii=False, sort_keys=True), flush=True)
        return counts
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
