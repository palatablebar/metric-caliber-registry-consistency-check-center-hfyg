"""initial metricd schema

Revision ID: 20261110_0001
Revises:
Create Date: 2026-11-10

The runtime bootstrap is ``Base.metadata.create_all`` so a fresh compose stack
needs no migration step; this revision lets ``alembic upgrade head`` create the
same tables when Alembic is the chosen path.
"""
from alembic import op

from app.config.database import Base
import app.models  # noqa: F401

revision = "20261110_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
