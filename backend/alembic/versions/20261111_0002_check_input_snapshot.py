"""check input snapshot + trust status

Revision ID: 20261111_0002
Revises: 20261110_0001
Create Date: 2026-11-11

Adds the frozen input snapshot, input completeness flag and trust status to
``consistency_checks``. Rows created before this revision are backfilled so the
API never sees a NULL trust state; their snapshot is empty because the frozen
input only exists for batches created after the upgrade.

MySQL cannot attach a literal column DEFAULT to a JSON column, so the JSON
column is added nullable, backfilled with an UPDATE, then made NOT NULL.
"""
import sqlalchemy as sa
from alembic import op

revision = "20261111_0002"
down_revision = "20261110_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) add nullable columns (no JSON literal default -> portable across MySQL/SQLite)
    op.add_column("consistency_checks", sa.Column("input_snapshot_json", sa.JSON(), nullable=True))
    op.add_column("consistency_checks", sa.Column("input_complete", sa.Boolean(), nullable=True))
    op.add_column("consistency_checks", sa.Column("trust_status", sa.String(length=16), nullable=True))

    bind = op.get_bind()
    check = sa.table(
        "consistency_checks",
        sa.column("status", sa.String),
        sa.column("input_snapshot_json", sa.JSON),
        sa.column("input_complete", sa.Boolean),
        sa.column("trust_status", sa.String),
    )

    # 2) backfill existing rows
    bind.execute(check.update().values(input_snapshot_json={}, input_complete=False, trust_status="pending"))
    # pre-upgrade completed batches stay authoritative; failures are explicitly untrusted
    bind.execute(
        check.update().where(check.c.status == "completed").values(
            input_complete=True, trust_status="trusted"
        )
    )
    bind.execute(
        check.update().where(check.c.status == "failed").values(trust_status="untrusted")
    )

    # 3) enforce NOT NULL (every row is populated; new ORM rows use the model
    #    defaults). batch_alter_table emits a native ALTER on MySQL and a table
    #    rebuild on SQLite, keeping the migration portable.
    with op.batch_alter_table("consistency_checks", schema=None) as batch_op:
        batch_op.alter_column("input_snapshot_json", existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column("input_complete", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column(
            "trust_status",
            existing_type=sa.String(length=16),
            nullable=False,
            server_default="pending",
        )
    op.create_index("ix_consistency_checks_trust_status", "consistency_checks", ["trust_status"])


def downgrade() -> None:
    op.drop_index("ix_consistency_checks_trust_status", table_name="consistency_checks")
    with op.batch_alter_table("consistency_checks", schema=None) as batch_op:
        batch_op.drop_column("trust_status")
        batch_op.drop_column("input_complete")
        batch_op.drop_column("input_snapshot_json")
